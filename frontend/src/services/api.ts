import type { User, Transaction, ReviewCase, AlertItem, ReconciliationResult, BalanceSummary } from '../types';

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

  confirmPayment: async (paymentId: number): Promise<Transaction> => {
    return request(`/payments/${paymentId}/confirm`, {
      method: 'POST',
    });
  },

  cancelPayment: async (paymentId: number): Promise<Transaction> => {
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

  getReviewCases: async (): Promise<ReviewCase[]> => {
    return request('/review/cases');
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

  getAlerts: async (): Promise<AlertItem[]> => {
    return request('/alerts');
  },

  markAlertRead: async (alertId: number): Promise<void> => {
    return request(`/alerts/${alertId}/read`, {
      method: 'POST',
    });
  },

  getScenarios: async (): Promise<any[]> => {
    return request('/demo/scenarios');
  },

  resetDemo: async (): Promise<{ message: string; elapsed_seconds: number }> => {
    return request('/demo/reset', {
      method: 'POST',
    });
  },
};
