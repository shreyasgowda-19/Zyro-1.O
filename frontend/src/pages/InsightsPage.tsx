import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowDownRight,
  ArrowLeft,
  ArrowRight,
  ArrowUpRight,
  BarChart3,
  Calendar,
  ChevronLeft,
  ChevronRight,
  PiggyBank,
  RefreshCw,
  ShieldAlert,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { api, getErrorMessage } from '../services/api';
import { formatPaise } from '../types';
import type {
  AlertItem,
  BalanceSummary,
  CashflowAnalytics,
  CategoryAnalytics,
  RiskBreakdown,
  SavingsGoal,
  Transaction,
} from '../types';
import { useLanguage } from '../contexts/LanguageContext';

type PaymentRisk = { transaction: Transaction; breakdown: RiskBreakdown };

const CHART_COLORS = ['#0f766e', '#4f46e5', '#f59e0b', '#e11d48', '#0284c7', '#7c3aed', '#65a30d'];

function currentPeriod() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`;
}

function changePeriod(period: string, offset: number) {
  const [year, month] = period.split('-').map(Number);
  const date = new Date(year, month - 1 + offset, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function periodLabel(period: string) {
  const [year, month] = period.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

export const InsightsPage: React.FC = () => {
  const { t } = useLanguage();
  const [period, setPeriod] = useState(currentPeriod);
  const [cashflow, setCashflow] = useState<CashflowAnalytics | null>(null);
  const [categories, setCategories] = useState<CategoryAnalytics | null>(null);
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [paymentRisks, setPaymentRisks] = useState<PaymentRisk[]>([]);
  const [balances, setBalances] = useState<BalanceSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadInsights() {
      setLoading(true);
      setError(null);
      try {
        const [cashflowData, categoryData, goalData, alertData, transactionData, balanceData] = await Promise.all([
          api.getCashflow(period),
          api.getCategoryAnalytics(period),
          api.getGoals(),
          api.getAlerts(),
          api.getTransactions(),
          api.getBalances(),
        ]);
        if (cancelled) return;

        setCashflow(cashflowData);
        setCategories(categoryData);
        setGoals(goalData);
        setAlerts((alertData.items || []).filter((item) => item.type === 'fraud' || item.type === 'review'));
        setBalances(balanceData);

        const recentPayments = transactionData
          .filter((item) => item.source === 'payment' && item.type === 'expense')
          .slice(0, 8);
        const riskResults = await Promise.all(recentPayments.map(async (transaction) => {
          try {
            return { transaction, breakdown: await api.getRiskBreakdown(transaction.id) };
          } catch {
            return null;
          }
        }));
        if (!cancelled) setPaymentRisks(riskResults.filter((item): item is PaymentRisk => item !== null));
      } catch (err) {
        if (!cancelled) setError(getErrorMessage(err));
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadInsights();
    return () => { cancelled = true; };
  }, [period]);

  const topCategory = categories?.categories[0];
  const savingsRate = cashflow && cashflow.total_income_paise > 0
    ? Math.round((cashflow.net_cashflow_paise / cashflow.total_income_paise) * 100)
    : null;
  const chartCashflow = useMemo(() => (cashflow?.daily || []).map((point) => ({
    day: point.date.slice(8),
    income: point.income_paise,
    expenses: point.expenses_paise,
    net: point.net_paise,
  })), [cashflow]);
  const riskByTransaction = useMemo(
    () => new Map(paymentRisks.map((item) => [item.transaction.id, item])),
    [paymentRisks]
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="rounded-2xl bg-slate-900 text-white p-6 sm:p-8 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-5">
        <div>
          <div className="inline-flex items-center gap-2 text-teal-300 text-xs font-bold uppercase tracking-wider">
            <BarChart3 className="w-4 h-4" /> FinShield Insights
          </div>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold">Your money, clearly explained</h1>
          <p className="mt-2 text-sm text-slate-300 max-w-2xl">
            Spending, savings, cash flow, and payment safety in one view, with the reasons behind each insight.
          </p>
        </div>
        <div className="flex items-center gap-2 self-start lg:self-auto rounded-xl border border-slate-700 bg-slate-800 p-1.5">
          <button type="button" aria-label="Previous month" onClick={() => setPeriod((value) => changePeriod(value, -1))} className="p-2 rounded-lg hover:bg-slate-700">
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="min-w-32 text-center text-sm font-semibold flex items-center justify-center gap-2">
            <Calendar className="w-4 h-4 text-teal-300" /> {periodLabel(period)}
          </span>
          <button type="button" aria-label="Next month" onClick={() => setPeriod((value) => changePeriod(value, 1))} disabled={period >= currentPeriod()} className="p-2 rounded-lg hover:bg-slate-700 disabled:opacity-40">
            <ChevronRight className="w-4 h-4" />
          </button>
          <button type="button" onClick={() => setPeriod(currentPeriod())} className="px-2.5 py-2 text-xs font-semibold text-teal-200 hover:bg-slate-700 rounded-lg">This month</button>
        </div>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}
      {loading && <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-500 flex items-center gap-2"><RefreshCw className="w-4 h-4 animate-spin" /> Updating your insights…</div>}

      <section aria-label="Monthly money summary" className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        <MetricCard title="Spent this month" value={formatPaise(cashflow?.total_expenses_paise || 0)} note={topCategory ? `${topCategory.category} is your largest category (${topCategory.percentage.toFixed(0)}% of spending).` : 'Based on completed expenses in this period.'} tone="rose" icon={<ArrowUpRight className="w-4 h-4" />} />
        <MetricCard title="Income recorded" value={formatPaise(cashflow?.total_income_paise || 0)} note="Completed income entries recorded for this month." tone="emerald" icon={<ArrowDownRight className="w-4 h-4" />} />
        <MetricCard title="Net cash flow" value={formatPaise(cashflow?.net_cashflow_paise || 0)} note={(cashflow?.net_cashflow_paise || 0) >= 0 ? 'Income is greater than completed spending this month.' : 'Completed spending is greater than recorded income this month.'} tone={(cashflow?.net_cashflow_paise || 0) >= 0 ? 'teal' : 'rose'} icon={<TrendingUp className="w-4 h-4" />} />
        <MetricCard title="Savings rate" value={savingsRate === null ? '—' : `${savingsRate}%`} note={savingsRate === null ? 'Add income to calculate net cash flow as a share of income.' : 'Calculated as (income − completed spending) ÷ income.'} tone="indigo" icon={<PiggyBank className="w-4 h-4" />} />
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900">Where your spending went</h2>
              <p className="mt-1 text-xs text-slate-500">Completed expenses by category for {periodLabel(period)}.</p>
            </div>
            <span className="text-sm font-bold text-slate-800">{formatPaise(categories?.total_spent_paise || 0)}</span>
          </div>
          {categories?.categories.length ? (
            <SpendingBars items={categories.categories} />
          ) : <EmptyInsight text={`No completed expenses recorded in ${periodLabel(period)}.`} />}
          {topCategory && <p className="mt-3 rounded-lg bg-teal-50 px-3 py-2 text-xs text-teal-900"><strong>Why this stands out:</strong> {topCategory.category} accounts for {topCategory.percentage.toFixed(1)}% of your completed spending this month.</p>}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
          <div>
            <h2 className="text-base font-bold text-slate-900">Cash flow through the month</h2>
            <p className="mt-1 text-xs text-slate-500">Daily income compared with completed expenses. Held payments are excluded until resolved.</p>
          </div>
          {chartCashflow.length ? (
            <CashflowBars data={chartCashflow} period={period} />
          ) : <EmptyInsight text="No completed income or expense entries to chart for this month." />}
          <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-700"><strong>How to read this:</strong> net cash flow is recorded income minus completed expenses. A positive result means more income than spending was recorded.</p>
        </div>
      </section>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-5">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
          <div className="flex items-center justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2"><PiggyBank className="w-5 h-5 text-teal-700" /> Savings progress</h2>
              <p className="mt-1 text-xs text-slate-500">Your saved goal contributions and current spendable balance.</p>
            </div>
            <Link to="/budgets" className="text-xs font-semibold text-teal-700 hover:underline">Manage goals <ArrowRight className="inline w-3.5 h-3.5" /></Link>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-teal-50 p-4"><div className="text-xs text-teal-800">Earmarked toward goals</div><div className="mt-1 text-lg font-bold text-teal-950">{formatPaise(goals.reduce((sum, goal) => sum + goal.current_paise, 0))}</div></div>
            <div className="rounded-xl bg-slate-50 p-4"><div className="text-xs text-slate-600">Available balance</div><div className="mt-1 text-lg font-bold text-slate-900">{formatPaise(balances?.available_balance_paise || 0)}</div></div>
          </div>
          {goals.length ? (
            <div className="mt-4 space-y-4">
              {goals.slice(0, 4).map((goal) => (
                <div key={goal.id}>
                  <div className="flex justify-between gap-2 text-xs"><span className="font-semibold text-slate-800">{goal.title}</span><span className="text-slate-600">{goal.progress_percentage.toFixed(0)}% · {formatPaise(goal.current_paise)} / {formatPaise(goal.target_paise)}</span></div>
                  <div className="mt-1.5 h-2 rounded-full bg-slate-100 overflow-hidden"><div className="h-full rounded-full bg-teal-600" style={{ width: `${Math.max(0, Math.min(100, goal.progress_percentage))}%` }} /></div>
                  <p className="mt-1 text-[11px] text-slate-500">{formatPaise(Math.max(0, goal.target_paise - goal.current_paise))} remaining to reach this goal.</p>
                </div>
              ))}
            </div>
          ) : <EmptyInsight text="No savings goals yet. Create one to track progress toward a target." link="/budgets" linkText="Create a savings goal" />}
          {cashflow && <p className="mt-4 rounded-lg bg-indigo-50 px-3 py-2 text-xs text-indigo-900"><strong>Why:</strong> goal progress reflects contributions recorded in FinShield. This is separate from your available balance; goals are planning earmarks.</p>}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6 shadow-xs">
          <div className="flex items-center gap-2"><ShieldAlert className="w-5 h-5 text-rose-600" /><h2 className="text-base font-bold text-slate-900">Fraud alerts and payment reasons</h2></div>
          <p className="mt-1 text-xs text-slate-500">Risk signals help explain a review. A high score is a warning, not proof of fraud.</p>
          {alerts.length > 0 && (
            <div className="mt-4 space-y-2">
              {alerts.slice(0, 4).map((alert) => {
                const linkedRisk = alert.related_transaction_id ? riskByTransaction.get(alert.related_transaction_id) : undefined;
                return (
                  <article key={alert.id} className={`rounded-xl border p-3 ${alert.type === 'fraud' ? 'border-rose-200 bg-rose-50/70' : 'border-amber-200 bg-amber-50/70'}`}>
                    <div className="flex items-start justify-between gap-3">
                      <div className="text-xs font-semibold text-slate-900">{t(alert.title_code, alert.params || {})}</div>
                      <span className="shrink-0 text-[10px] font-bold uppercase text-slate-500">{alert.type}</span>
                    </div>
                    <p className="mt-1 text-[11px] text-slate-600">{alert.type === 'fraud' ? 'A reviewer confirmed a fraud concern for this payment.' : 'This payment needed a review before or after processing.'}</p>
                    {linkedRisk?.breakdown.what_would_change.length ? <p className="mt-2 text-[11px] text-slate-700"><strong>Risk signals:</strong> {linkedRisk.breakdown.what_would_change.slice(0, 2).map((reason) => reason.explanation).join(' ')}</p> : null}
                    {alert.related_transaction_id && <Link to={`/payments/${alert.related_transaction_id}/result`} className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-teal-700 hover:underline">View payment <ArrowRight className="w-3 h-3" /></Link>}
                  </article>
                );
              })}
            </div>
          )}
          <div className="mt-4 space-y-2">
            {paymentRisks.slice(0, 5).map(({ transaction, breakdown }) => (
              <article key={transaction.id} className="rounded-xl border border-slate-200 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="text-xs font-semibold text-slate-900">{transaction.payee_name || transaction.masked_payee || transaction.category} · {formatPaise(transaction.amount_paise)}</div>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase ${breakdown.band === 'high' ? 'bg-rose-100 text-rose-800' : breakdown.band === 'medium' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'}`}>{breakdown.band} · {breakdown.score}/100</span>
                </div>
                {breakdown.what_would_change.length ? (
                  <ul className="mt-2 space-y-1 text-[11px] text-slate-600">
                    {breakdown.what_would_change.slice(0, 2).map((reason) => <li key={reason.rule_code}>• {reason.explanation}</li>)}
                  </ul>
                ) : <p className="mt-2 text-[11px] text-slate-500 flex items-center gap-1"><ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> No risk signals fired for this payment.</p>}
              </article>
            ))}
          </div>
          {!alerts.length && !paymentRisks.length && !loading && <EmptyInsight text="No payment risk alerts or scored payments are available yet. New payments will appear here with the signals behind their score." link="/pay" linkText="Make a payment" />}
        </div>
      </section>

      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-xs text-slate-500">
        <span>Insights use completed ledger entries and your own payment risk assessments. They are not bank statements or financial advice.</span>
        <Link to="/dashboard" className="inline-flex items-center gap-1 font-semibold text-teal-700 hover:underline"><ArrowLeft className="w-3.5 h-3.5" /> Back to dashboard</Link>
      </div>
    </div>
  );
};

function SpendingBars({ items }: { items: NonNullable<CategoryAnalytics['categories']> }) {
  const visibleItems = items.slice(0, 7);
  const maxAmount = Math.max(1, ...visibleItems.map((item) => item.amount_paise));
  return (
    <div className="mt-5 space-y-4" role="img" aria-label="Horizontal bar chart showing completed spending by category">
      {visibleItems.map((item, index) => (
        <div key={item.category}>
          <div className="mb-1.5 flex items-center justify-between gap-3 text-xs">
            <span className="font-semibold text-slate-700">{item.category}</span>
            <span className="shrink-0 text-slate-600">{formatPaise(item.amount_paise)} <span className="text-slate-400">({item.percentage.toFixed(1)}%)</span></span>
          </div>
          <div className="h-3 overflow-hidden rounded-full bg-slate-100">
            <div className="h-full rounded-full transition-all" style={{ width: `${Math.max(1, (item.amount_paise / maxAmount) * 100)}%`, backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }} />
          </div>
        </div>
      ))}
      {items.length > visibleItems.length && <p className="text-[11px] text-slate-500">Showing the top {visibleItems.length} of {items.length} spending categories.</p>}
    </div>
  );
}

function CashflowBars({ data, period }: { data: Array<{ day: string; income: number; expenses: number; net: number }>; period: string }) {
  const width = 720;
  const height = 250;
  const left = 76;
  const right = 10;
  const top = 12;
  const bottom = 210;
  const plotHeight = bottom - top;
  const plotWidth = width - left - right;
  const maxValue = Math.max(1, ...data.flatMap((point) => [point.income, point.expenses]));
  const slotWidth = plotWidth / data.length;
  const barWidth = Math.max(2, Math.min(18, slotWidth * 0.32));
  const labelEvery = Math.max(1, Math.ceil(data.length / 10));

  return (
    <div className="mt-4" role="img" aria-label={`Daily income and completed expenses for ${period}`}>
      <div className="mb-2 flex items-center justify-end gap-4 text-[11px] text-slate-600">
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-sm bg-teal-700" /> Income</span>
        <span className="flex items-center gap-1.5"><i className="h-2.5 w-2.5 rounded-sm bg-rose-600" /> Expenses</span>
      </div>
      <svg viewBox={`0 0 ${width} ${height}`} className="h-64 w-full" preserveAspectRatio="none" aria-hidden="true">
        {[0, 1, 2, 3].map((step) => {
          const y = top + (plotHeight / 3) * step;
          const value = maxValue * (1 - step / 3);
          return <g key={step}><line x1={left} y1={y} x2={width - right} y2={y} stroke="#e2e8f0" strokeDasharray="4 4" /><text x={left - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#64748b">{formatPaise(value, false)}</text></g>;
        })}
        {data.map((point, index) => {
          const center = left + slotWidth * index + slotWidth / 2;
          const incomeHeight = (point.income / maxValue) * plotHeight;
          const expenseHeight = (point.expenses / maxValue) * plotHeight;
          const showLabel = index % labelEvery === 0 || index === data.length - 1;
          return <g key={point.day}>
            <title>{`${period}-${point.day}: income ${formatPaise(point.income)}, expenses ${formatPaise(point.expenses)}`}</title>
            <rect x={center - barWidth - 1} y={bottom - incomeHeight} width={barWidth} height={Math.max(point.income ? 2 : 0, incomeHeight)} rx="2" fill="#0f766e" />
            <rect x={center + 1} y={bottom - expenseHeight} width={barWidth} height={Math.max(point.expenses ? 2 : 0, expenseHeight)} rx="2" fill="#e11d48" />
            {showLabel && <text x={center} y={bottom + 18} textAnchor="middle" fontSize="10" fill="#64748b">{point.day}</text>}
          </g>;
        })}
        <text x={left + plotWidth / 2} y={height - 4} textAnchor="middle" fontSize="10" fill="#64748b">Day of month</text>
      </svg>
    </div>
  );
}

function MetricCard({ title, value, note, tone, icon }: { title: string; value: string; note: string; tone: 'rose' | 'emerald' | 'teal' | 'indigo'; icon: React.ReactNode }) {
  const tones = {
    rose: 'border-rose-200 bg-rose-50 text-rose-800',
    emerald: 'border-emerald-200 bg-emerald-50 text-emerald-800',
    teal: 'border-teal-200 bg-teal-50 text-teal-800',
    indigo: 'border-indigo-200 bg-indigo-50 text-indigo-800',
  };
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
      <div className="flex items-center justify-between"><span className="text-xs font-semibold text-slate-500">{title}</span><span className={`rounded-lg border p-2 ${tones[tone]}`}>{icon}</span></div>
      <div className="mt-3 text-2xl font-bold text-slate-900">{value}</div>
      <p className="mt-2 min-h-8 text-[11px] leading-4 text-slate-500">{note}</p>
    </article>
  );
}

function EmptyInsight({ text, link, linkText }: { text: string; link?: string; linkText?: string }) {
  return (
    <div className="mt-5 rounded-xl border border-dashed border-slate-200 bg-slate-50 px-4 py-8 text-center text-xs text-slate-500">
      <p>{text}</p>
      {link && linkText && <Link to={link} className="mt-2 inline-flex items-center gap-1 font-semibold text-teal-700 hover:underline">{linkText} <ArrowRight className="w-3 h-3" /></Link>}
    </div>
  );
}
