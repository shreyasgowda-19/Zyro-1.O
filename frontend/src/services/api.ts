import type {
  User,
  Transaction,
  ReviewCase,
  AlertItem,
  ReconciliationResult,
  BalanceSummary,
  Budget,
  BudgetSummary,
  SavingsGoal,
  CashflowAnalytics,
  CategoryAnalytics,
  GuidanceItem,
  ScamCheckResult,
  RiskBreakdown,
  TrackedAccount,
  StatementRequest,
  StatementPreview,
  ImportedStatementRow,
} from '../types';

export class ApiError extends Error {
  code: string;
  params: Record<string, any>;
  fields: Array<{ field: string; code: string; params?: Record<string, any> }>;
  requestId?: string;
  status: number;

  constructor(status: number, data: any) {
    const errorObj = data?.error || {};
    super(errorObj.message || errorObj.code || `HTTP error ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.code = errorObj.code || 'UNKNOWN_ERROR';
    this.params = errorObj.params || {};
    this.fields = errorObj.fields || [];
    this.requestId = errorObj.request_id;
  }
}

export function getErrorMessage(err: any): string {
  if (err instanceof ApiError) {
    switch (err.code) {
      case 'INSUFFICIENT_FUNDS':
        return 'Insufficient available funds for this payment. Please check your available balance.';
      case 'CREDENTIAL_INPUT_REJECTED':
        return 'Security Alert: Credential detected. FinShield will never ask for your PIN, OTP, or CVV.';
      case 'INVALID_TEXT':
        return 'Invalid input: script tags and unsafe text patterns are blocked.';
      case 'NOTE_REQUIRED':
        return 'Review action requires a justification note between 5 and 500 characters.';
      case 'CASE_CONFLICT':
        return 'Case Conflict: This review case was modified by another reviewer. Please refresh and try again.';
      case 'ILLEGAL_TRANSITION':
        return 'Illegal state transition: This transaction cannot be transitioned in its current state.';
      case 'IDEMPOTENCY_CONFLICT':
        return 'Duplicate submission detected with different transaction payload.';
      case 'FORBIDDEN':
        return err.message || 'Access denied: You do not have permission to perform this action.';
      case 'NOT_FOUND':
        return 'Requested record was not found.';
      case 'VALIDATION_ERROR':
        return 'Validation error: Please verify payment amount (₹1 to ₹2,00,000) and required fields.';
      case 'UNAUTHENTICATED':
        return 'Session expired. Please log in again.';
      default:
        return err.message || 'An unexpected error occurred.';
    }
  }
  return err?.message || 'Network error or server unavailable.';
}

const BASE_URL = '';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = sessionStorage.getItem('payguard_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => controller.abort(), 15000);
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${endpoint}`, {
      ...options,
      headers,
      signal: options.signal ?? controller.signal,
    });
  } catch (err) {
    if (controller.signal.aborted) {
      throw new Error('The server did not respond within 15 seconds. Refresh this case before retrying to check whether the decision was recorded.');
    }
    throw err;
  } finally {
    window.clearTimeout(timeoutId);
  }

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

function normalizeReviewCase(data: any, fallbackId?: number): ReviewCase {
  const rawId = data?.id ?? data?.case_id ?? fallbackId;
  const id = typeof rawId === 'number' ? rawId : Number(rawId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    throw new Error('The review case response did not include a valid case ID. Refresh the queue and reopen the case.');
  }
  return { ...data, id } as ReviewCase;
}

export const api = {
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  },

  register: async (username: string, password: string, profileType: 'personal' | 'business', initialBalancePaise: number): Promise<{ access_token: string; user: User }> => {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, profile_type: profileType, initial_balance_paise: initialBalancePaise }),
    });
  },

  getMe: async (): Promise<User> => {
    return request('/users/me');
  },

  getHealth: async (): Promise<{ status: string; version: string; schema_head: string; rules_version: string; demo_mode: boolean }> => {
    return request('/health');
  },

  getBalances: async (): Promise<BalanceSummary> => {
    return request('/accounting/summary');
  },

  getTrackedAccounts: async (): Promise<TrackedAccount[]> => {
    return request('/accounts');
  },

  createTrackedAccount: async (data: {
    institution_name: string;
    account_name: string;
    account_type: TrackedAccount['account_type'];
    last_four?: string;
    reported_balance_paise: number;
  }): Promise<TrackedAccount> => {
    return request('/accounts', { method: 'POST', body: JSON.stringify(data) });
  },

  updateTrackedAccountBalance: async (id: number, reported_balance_paise: number): Promise<TrackedAccount> => {
    return request(`/accounts/${id}/balance`, {
      method: 'PATCH',
      body: JSON.stringify({ reported_balance_paise }),
    });
  },

  deleteTrackedAccount: async (id: number): Promise<void> => {
    return request(`/accounts/${id}`, { method: 'DELETE' });
  },

  importStatementRows: async (file_hash: string, rows: ImportedStatementRow[]): Promise<{ imported_count: number; duplicates_skipped: number; transaction_ids: number[] }> => {
    return request('/statements/import', {
      method: 'POST',
      body: JSON.stringify({ file_hash, rows }),
    });
  },

  createStatementRequest: async (start_date: string, end_date: string): Promise<StatementRequest> => {
    return request('/statements/requests', {
      method: 'POST',
      body: JSON.stringify({ start_date, end_date }),
    });
  },

  getStatementRequests: async (): Promise<StatementRequest[]> => request('/statements/requests'),

  getStatementQueue: async (): Promise<StatementRequest[]> => request('/statements/requests/queue'),

  getStatementPreview: async (id: number): Promise<StatementPreview> => request(`/statements/requests/${id}/preview`),

  decideStatementRequest: async (id: number, decision: 'approved' | 'rejected', note: string): Promise<StatementRequest> => {
    return request(`/statements/requests/${id}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, note }),
    });
  },

  downloadStatement: async (id: number): Promise<Blob> => {
    const token = sessionStorage.getItem('payguard_token');
    const response = await fetch(`/statements/requests/${id}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const isJson = response.headers.get('content-type')?.includes('application/json');
      throw new ApiError(response.status, isJson ? await response.json() : null);
    }
    return response.blob();
  },

  getReconciliation: async (): Promise<ReconciliationResult> => {
    return request('/accounting/reconciliation');
  },

  createPayment: async (paymentData: any, idempotencyKey: string): Promise<Transaction> => {
    return request('/payments', {
      method: 'POST',
      headers: { 'Idempotency-Key': idempotencyKey },
      body: JSON.stringify(paymentData),
    });
  },

  confirmPayment: async (paymentId: number): Promise<{ id: number; status: string; message: string }> => {
    return request(`/payments/${paymentId}/confirm`, {
      method: 'POST',
    });
  },

  cancelPayment: async (paymentId: number): Promise<{ id: number; status: string; message: string }> => {
    return request(`/payments/${paymentId}/cancel`, {
      method: 'POST',
    });
  },

  getPayment: async (paymentId: number): Promise<Transaction> => {
    return request(`/payments/${paymentId}`);
  },

  getTransactions: async (): Promise<Transaction[]> => {
    return request('/transactions');
  },

  getReviewCases: async (status?: string, caseType?: string): Promise<{ items: ReviewCase[]; total: number }> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (caseType) params.append('case_type', caseType);
    const query = params.toString() ? `?${params.toString()}` : '';
    const data = await request<{ items: any[]; total: number }>(`/review/cases${query}`);
    return { ...data, items: (data.items || []).map(normalizeReviewCase) };
  },

  getReviewCase: async (caseId: number): Promise<ReviewCase> => {
    return normalizeReviewCase(await request(`/review/cases/${caseId}`), caseId);
  },

  submitDecision: async (caseId: number, action: string, note: string, expectedVersion: number): Promise<ReviewCase> => {
    const data = await request(`/review/cases/${caseId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action, note, expected_version: expectedVersion }),
    });
    return normalizeReviewCase(data, caseId);
  },

  getReviewAudit: async (caseId?: number): Promise<{ items: any[]; total: number }> => {
    const query = caseId ? `?case_id=${caseId}` : '';
    return request(`/review/audit${query}`);
  },

  getAlerts: async (unreadOnly: boolean = false): Promise<{ items: AlertItem[]; unread_count: number }> => {
    return request(`/alerts?unread_only=${unreadOnly}`);
  },

  markAlertRead: async (alertId: number): Promise<AlertItem> => {
    return request(`/alerts/${alertId}/read`, {
      method: 'POST',
    });
  },

  getScenarios: async (): Promise<{ scenarios: any[] }> => {
    return request('/demo/scenarios');
  },

  resetDemo: async (): Promise<{ status: string; message: string; duration_seconds: number }> => {
    return request('/demo/reset', {
      method: 'POST',
    });
  },

  getRiskAssessment: async (transactionId: number): Promise<any> => {
    return request(`/risk/assessments/${transactionId}`);
  },

  getRiskBreakdown: async (transactionId: number): Promise<RiskBreakdown> => {
    return request(`/risk/assessments/${transactionId}/breakdown`);
  },

  // Budgeting & Analytics
  getBudgets: async (period?: string): Promise<Budget[]> => {
    const query = period ? `?period=${period}` : '';
    return request(`/budgets${query}`);
  },

  createBudget: async (data: { category?: string; amount_paise: number; period: string }): Promise<Budget> => {
    return request('/budgets', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateBudget: async (id: number, amount_paise: number): Promise<Budget> => {
    return request(`/budgets/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ amount_paise }),
    });
  },

  deleteBudget: async (id: number): Promise<{ status: string; message: string }> => {
    return request(`/budgets/${id}`, {
      method: 'DELETE',
    });
  },

  getBudgetSummary: async (period?: string): Promise<BudgetSummary> => {
    const query = period ? `?period=${period}` : '';
    return request(`/budgets/summary${query}`);
  },

  // Savings Goals
  getGoals: async (): Promise<SavingsGoal[]> => {
    return request('/goals');
  },

  createGoal: async (data: { title: string; target_paise: number; target_date?: string }): Promise<SavingsGoal> => {
    return request('/goals', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateGoal: async (id: number, data: { title?: string; target_paise?: number; target_date?: string }): Promise<SavingsGoal> => {
    return request(`/goals/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  contributeGoal: async (id: number, amount_paise: number): Promise<SavingsGoal> => {
    return request(`/goals/${id}/contributions`, {
      method: 'POST',
      body: JSON.stringify({ amount_paise }),
    });
  },

  deleteGoal: async (id: number): Promise<{ status: string; message: string }> => {
    return request(`/goals/${id}`, {
      method: 'DELETE',
    });
  },

  // Cash Flow & Category Analytics
  getCashflow: async (period?: string): Promise<CashflowAnalytics> => {
    const query = period ? `?period=${period}` : '';
    return request(`/accounting/cashflow${query}`);
  },

  getCategoryAnalytics: async (period?: string): Promise<CategoryAnalytics> => {
    const query = period ? `?period=${period}` : '';
    return request(`/accounting/categories${query}`);
  },

  // Manual Transactions (Cash/Income)
  createManualTransaction: async (data: { type: string; amount_paise: number; category: string; note?: string; created_at?: string }): Promise<Transaction> => {
    return request('/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  // Financial Awareness Guidance & Scam Checker (§14, §17, D13)
  getGuidance: async (lang: string = 'en'): Promise<GuidanceItem[]> => {
    return request(`/guidance?lang=${lang}`);
  },

  checkScamMessage: async (message: string): Promise<ScamCheckResult> => {
    return request('/guidance/scam-check', {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
};
