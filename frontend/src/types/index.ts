export interface User {
  id: number;
  username: string;
  role: 'customer' | 'reviewer' | 'supervisor';
  profile_type?: 'personal' | 'business' | null;
  is_active: boolean;
  created_at: string;
}

export interface Account {
  id: number;
  user_id: number;
  opening_balance_paise: number;
}

export interface BalanceSummary {
  completed_balance_paise: number;
  held_balance_paise: number;
  available_balance_paise: number;
}

export interface Payee {
  id: number;
  owner_user_id: number;
  display_name: string;
  masked_identifier: string;
  trust_status: 'new' | 'known' | 'flagged';
  created_at: string;
}

export interface RiskReason {
  id?: number;
  rule_code: string;
  points: number;
  params: Record<string, any>;
}

export interface RiskAssessment {
  id?: number;
  transaction_id: number;
  score: number;
  band: 'low' | 'medium' | 'high';
  rules_version: string;
  reasons: RiskReason[];
  created_at?: string;
}

export interface Transaction {
  id: number;
  user_id: number;
  type: 'income' | 'expense';
  source: 'payment' | 'manual';
  amount_paise: number;
  category: string;
  payee_id?: number | null;
  payee_name?: string;
  masked_payee?: string;
  method: 'upi' | 'card' | 'netbanking' | 'wallet' | 'collect_approval';
  status: 'pending' | 'awaiting_confirmation' | 'held' | 'escalated' | 'completed' | 'cancelled' | 'released';
  note?: string | null;
  synthetic_device_tag?: string | null;
  synthetic_city_tag?: string | null;
  created_at: string;
  assessment?: RiskAssessment;
}

export interface ReviewCase {
  id: number;
  transaction_id: number;
  case_type: 'hold_review' | 'post_review';
  status: 'open' | 'escalated' | 'closed';
  decision?: 'approved' | 'rejected' | 'false_alarm' | 'confirmed_fraud' | null;
  version: number;
  assigned_reviewer_id?: number | null;
  created_at: string;
  updated_at: string;
  masked_customer_ref: string;
  masked_payee: string;
  amount_paise: number;
  method: string;
  score: number;
  band: 'low' | 'medium' | 'high';
  reasons: RiskReason[];
  actions?: Array<{
    id: number;
    actor_id: number;
    actor_username?: string;
    actor_role?: string;
    action: string;
    note: string;
    created_at: string;
  }>;
}

export interface AlertItem {
  id: number;
  type: 'budget' | 'fraud' | 'review';
  title_code: string;
  params: Record<string, any>;
  related_transaction_id?: number | null;
  read_at?: string | null;
  created_at: string;
}

export interface ReconciliationCheck {
  name: string;
  description: string;
  passed: boolean;
  details: Record<string, any>;
}

export interface ReconciliationResult {
  all_passed: boolean;
  timestamp: string;
  checks: ReconciliationCheck[];
}

export interface Budget {
  id: number;
  user_id: number;
  category?: string | null;
  amount_paise: number;
  period: string;
  created_at: string;
}

export interface CategoryBudgetSummary {
  category: string;
  budget_paise?: number | null;
  spent_paise: number;
  remaining_paise?: number | null;
  percentage?: number | null;
}

export interface OverallBudgetSummary {
  budget_paise?: number | null;
  spent_paise: number;
  remaining_paise?: number | null;
  percentage?: number | null;
}

export interface BudgetSummary {
  period: string;
  overall: OverallBudgetSummary;
  categories: CategoryBudgetSummary[];
}

export interface SavingsGoal {
  id: number;
  user_id: number;
  title: string;
  target_paise: number;
  current_paise: number;
  target_date?: string | null;
  progress_percentage: number;
  created_at: string;
}

export interface CashflowPoint {
  date: string;
  income_paise: number;
  expenses_paise: number;
  net_paise: number;
}

export interface CashflowAnalytics {
  period: string;
  total_income_paise: number;
  total_expenses_paise: number;
  net_cashflow_paise: number;
  daily: CashflowPoint[];
}

export interface CategoryAnalytics {
  period: string;
  total_spent_paise: number;
  categories: Array<{
    category: string;
    amount_paise: number;
    percentage: number;
  }>;
}

export interface GuidanceItem {
  id: number;
  topic: string;
  language: 'en' | 'hi';
  title: string;
  body: string;
  source_label: string;
  source_url?: string | null;
  last_verified: string;
}

export interface ScamCheckMatchedSignal {
  code: string;
  name: string;
  description: string;
}

export interface ScamCheckResult {
  is_suspicious: boolean;
  risk_level: 'low' | 'medium' | 'high';
  matched_signals: ScamCheckMatchedSignal[];
  advice_codes: string[];
  disclaimer: string;
}

export interface RiskWhatWouldChange {
  rule_code: string;
  factor: string;
  reduction_points: number;
  without_signal_score: number;
  without_signal_band: 'Low' | 'Medium' | 'High';
  explanation: string;
}

export interface RiskBreakdown {
  transaction_id: number;
  score: number;
  band: 'low' | 'medium' | 'high';
  rules_version: string;
  fired_reasons: RiskReason[];
  what_would_change: RiskWhatWouldChange[];
}

export function formatPaise(paise: number, showDecimals = true): string {
  const isNegative = paise < 0;
  const absPaise = Math.abs(Math.round(paise));
  const rupees = Math.floor(absPaise / 100);
  const remainder = absPaise % 100;

  const strRupees = rupees.toString();
  let formattedRupees = "";
  if (strRupees.length <= 3) {
    formattedRupees = strRupees;
  } else {
    const last3 = strRupees.substring(strRupees.length - 3);
    const remaining = strRupees.substring(0, strRupees.length - 3);
    const parts: string[] = [];
    let rem = remaining;
    while (rem.length > 2) {
      parts.unshift(rem.substring(rem.length - 2));
      rem = rem.substring(0, rem.length - 2);
    }
    if (rem.length > 0) {
      parts.unshift(rem);
    }
    formattedRupees = parts.join(",") + "," + last3;
  }

  const prefix = isNegative ? "-₹" : "₹";
  if (showDecimals) {
    const dec = remainder.toString().padStart(2, "0");
    return `${prefix}${formattedRupees}.${dec}`;
  }
  return `${prefix}${formattedRupees}`;
}
