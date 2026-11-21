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
        return 'Security Alert: Credential detected. PayGuard 360 will never ask for your PIN, OTP, or CVV.';
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
        return 'Access denied: You do not have permission to perform this action.';
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

  const response = await fetch(`${BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  const isJson = response.headers.get('content-type')?.includes('application/json');
  const data = isJson ? await response.json() : null;

  if (!response.ok) {
    throw new ApiError(response.status, data);
  }

  return data as T;
}

export const api = {
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
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
    return request(`/review/cases${query}`);
  },

  getReviewCase: async (caseId: number): Promise<ReviewCase> => {
    return request(`/review/cases/${caseId}`);
  },

  submitDecision: async (caseId: number, action: string, note: string, expectedVersion: number): Promise<ReviewCase> => {
    return request(`/review/cases/${caseId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ action, note, expected_version: expectedVersion }),
    });
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
