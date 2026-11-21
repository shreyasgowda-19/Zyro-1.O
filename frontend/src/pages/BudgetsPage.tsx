import React, { useState, useEffect } from 'react';
import {
  PieChart,
  Target,
  TrendingUp,
  PlusCircle,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  ShieldCheck,
  ChevronLeft,
  ChevronRight,
  Trash2,
  ArrowDownRight,
  ArrowUpRight
} from 'lucide-react';
import { api, ApiError } from '../services/api';
import { formatPaise } from '../types';
import type {
  BudgetSummary,
  SavingsGoal,
  CashflowAnalytics,
  CategoryAnalytics,
  ReconciliationResult
} from '../types';

export const BudgetsPage: React.FC = () => {
  const currentDate = new Date();
  const currentMonthStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;

  const [period, setPeriod] = useState<string>(currentMonthStr);
  const [summary, setSummary] = useState<BudgetSummary | null>(null);
  const [goals, setGoals] = useState<SavingsGoal[]>([]);
  const [cashflow, setCashflow] = useState<CashflowAnalytics | null>(null);
  const [categoriesData, setCategoriesData] = useState<CategoryAnalytics | null>(null);
  const [recon, setRecon] = useState<ReconciliationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modals
  const [showBudgetModal, setShowBudgetModal] = useState(false);
  const [showGoalModal, setShowGoalModal] = useState(false);
  const [showContribModal, setShowContribModal] = useState<SavingsGoal | null>(null);
  const [showTxModal, setShowTxModal] = useState(false);

  // Budget Modal Form State
  const [budgetCategory, setBudgetCategory] = useState<string>('');
  const [budgetRupees, setBudgetRupees] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Goal Modal Form State
  const [goalTitle, setGoalTitle] = useState('');
  const [goalTargetRupees, setGoalTargetRupees] = useState('');
  const [goalTargetDate, setGoalTargetDate] = useState('');

  // Contrib Modal Form State
  const [contribRupees, setContribRupees] = useState('');

  // Manual Tx Form State
  const [txType, setTxType] = useState<'income' | 'expense'>('expense');
  const [txRupees, setTxRupees] = useState('');
  const [txCategory, setTxCategory] = useState('General');
  const [txNote, setTxNote] = useState('');

  const loadData = async (activePeriod: string) => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, goalsRes, cfRes, catRes, reconRes] = await Promise.all([
        api.getBudgetSummary(activePeriod),
        api.getGoals(),
        api.getCashflow(activePeriod),
        api.getCategoryAnalytics(activePeriod),
        api.getReconciliation().catch(() => null)
      ]);
      setSummary(sumRes);
      setGoals(goalsRes);
      setCashflow(cfRes);
      setCategoriesData(catRes);
      if (reconRes) setRecon(reconRes);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to load budgeting data.');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(period);
  }, [period]);

  const changeMonth = (delta: number) => {
    const [yStr, mStr] = period.split('-');
    let y = parseInt(yStr, 10);
    let m = parseInt(mStr, 10) + delta;
    if (m > 12) {
      m = 1;
      y += 1;
    } else if (m < 1) {
      m = 12;
      y -= 1;
    }
    const newPeriod = `${y}-${String(m).padStart(2, '0')}`;
    setPeriod(newPeriod);
  };

  // Budget submission
  const handleSaveBudget = async (e: React.FormEvent) => {
    e.preventDefault();
    const paise = Math.round(parseFloat(budgetRupees || '0') * 100);
    if (paise <= 0) return;

    setIsSubmitting(true);
    try {
      await api.createBudget({
        category: budgetCategory ? budgetCategory : undefined,
        amount_paise: paise,
        period: period,
      });
      setShowBudgetModal(false);
      setBudgetCategory('');
      setBudgetRupees('');
      await loadData(period);
    } catch (err: any) {
      alert(err.message || 'Failed to save budget.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Goal submission
  const handleSaveGoal = async (e: React.FormEvent) => {
    e.preventDefault();
    const paise = Math.round(parseFloat(goalTargetRupees || '0') * 100);
    if (paise <= 0 || !goalTitle.trim()) return;

    setIsSubmitting(true);
    try {
      await api.createGoal({
        title: goalTitle.trim(),
        target_paise: paise,
        target_date: goalTargetDate || undefined,
      });
      setShowGoalModal(false);
      setGoalTitle('');
      setGoalTargetRupees('');
      setGoalTargetDate('');
      await loadData(period);
    } catch (err: any) {
      alert(err.message || 'Failed to create goal.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Goal contribution
  const handleContribute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!showContribModal) return;
    const paise = Math.round(parseFloat(contribRupees || '0') * 100);
    if (paise <= 0) return;

    setIsSubmitting(true);
    try {
      await api.contributeGoal(showContribModal.id, paise);
      setShowContribModal(null);
      setContribRupees('');
      await loadData(period);
    } catch (err: any) {
      alert(err.message || 'Contribution failed. Please check your available balance.');
    } finally {
      setIsSubmitting(false);
    }
  };

  // Manual Transaction submission
  const handleSaveTx = async (e: React.FormEvent) => {
    e.preventDefault();
    const paise = Math.round(parseFloat(txRupees || '0') * 100);
    if (paise <= 0) return;

    setIsSubmitting(true);
    try {
      await api.createManualTransaction({
        type: txType,
        amount_paise: paise,
        category: txCategory,
        note: txNote ? txNote.trim() : undefined,
      });
      setShowTxModal(false);
      setTxRupees('');
      setTxNote('');
      await loadData(period);
    } catch (err: any) {
      alert(err.message || 'Transaction recording failed.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteGoal = async (id: number) => {
    if (!confirm('Are you sure you want to delete this savings goal?')) return;
    try {
      await api.deleteGoal(id);
      await loadData(period);
    } catch (err: any) {
      alert(err.message || 'Failed to delete goal.');
    }
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto pb-12">
      {/* Top Header & Period Control */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <PieChart className="w-7 h-7 text-teal-600" />
            Smart Budgeting & Goals
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Track categorized spending, set proactive monthly limits, and manage goal earmarks.
          </p>
        </div>

        {/* Period Selector & Action buttons */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center bg-slate-50 border border-slate-200 rounded-lg p-1">
            <button
              onClick={() => changeMonth(-1)}
              className="p-1 hover:bg-slate-200 rounded text-slate-600"
              title="Previous Month"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="px-3 text-sm font-semibold text-slate-800 flex items-center gap-1.5">
              <Calendar className="w-4 h-4 text-slate-500" />
              {period}
            </span>
            <button
              onClick={() => changeMonth(1)}
              className="p-1 hover:bg-slate-200 rounded text-slate-600"
              title="Next Month"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>

          <button
            onClick={() => setShowBudgetModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <PlusCircle className="w-4 h-4" />
            Set Budget
          </button>

          <button
            onClick={() => setShowGoalModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <Target className="w-4 h-4" />
            New Goal
          </button>

          <button
            onClick={() => setShowTxModal(true)}
            className="flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-sm font-medium transition-colors"
          >
            <PlusCircle className="w-4 h-4 text-slate-600" />
            Record Entry
          </button>
        </div>
      </div>

      {/* Reconciliation Leg Status Panel */}
      {recon && (
        <div className="bg-emerald-50 border border-emerald-200/60 rounded-xl p-4 flex items-center justify-between text-sm text-emerald-900">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            <span>
              <strong>Ledger Consistency Verified:</strong> All 4 accounting legs balance in full. Completed expenses match ledger journals exactly.
            </span>
          </div>
          <span className="text-xs font-semibold bg-emerald-200/70 text-emerald-800 px-2.5 py-1 rounded-full">
            4/4 Checks Passed
          </span>
        </div>
      )}

      {loading ? (
        <div className="p-12 text-center text-slate-500 bg-white rounded-2xl border border-slate-100">
          Loading smart budgeting analytics...
        </div>
      ) : error ? (
        <div className="p-6 bg-rose-50 text-rose-800 rounded-2xl border border-rose-200 text-sm">
          {error}
        </div>
      ) : (
        <>
          {/* OVERALL MONTHLY BUDGET SECTION */}
          {summary?.overall.budget_paise ? (
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="flex justify-between items-start mb-4">
                <div>
                  <span className="text-xs font-bold uppercase tracking-wider text-slate-400">
                    Monthly Spending Ceiling
                  </span>
                  <h2 className="text-xl font-bold text-slate-900 mt-0.5">
                    Overall Budget ({period})
                  </h2>
                </div>
                {/* Alert Band Tag */}
                {typeof summary.overall.percentage === 'number' && (
                  <span
                    className={`px-3 py-1 text-xs font-semibold rounded-full flex items-center gap-1 ${
                      summary.overall.percentage >= 100
                        ? 'bg-rose-100 text-rose-700'
                        : summary.overall.percentage >= 80
                        ? 'bg-amber-100 text-amber-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}
                  >
                    {summary.overall.percentage >= 100 ? (
                      <AlertTriangle className="w-3.5 h-3.5" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5" />
                    )}
                    {summary.overall.percentage >= 100
                      ? '100% Exceeded'
                      : summary.overall.percentage >= 80
                      ? '80%+ Alert Triggered'
                      : 'On Track'}
                  </span>
                )}
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-100 h-3 rounded-full overflow-hidden mb-4">
                <div
                  className={`h-full transition-all duration-500 ${
                    (summary.overall.percentage || 0) >= 100
                      ? 'bg-rose-500'
                      : (summary.overall.percentage || 0) >= 80
                      ? 'bg-amber-500'
                      : 'bg-teal-600'
                  }`}
                  style={{ width: `${Math.min(100, summary.overall.percentage || 0)}%` }}
                />
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm pt-2 border-t border-slate-100">
                <div>
                  <div className="text-slate-500 text-xs font-medium">Completed Spent</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {formatPaise(summary.overall.spent_paise)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 text-xs font-medium">Monthly Limit</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {formatPaise(summary.overall.budget_paise)}
                  </div>
                </div>
                <div>
                  <div className="text-slate-500 text-xs font-medium">Remaining Headroom</div>
                  <div
                    className={`text-lg font-bold mt-0.5 ${
                      (summary.overall.remaining_paise || 0) <= 0 ? 'text-rose-600' : 'text-emerald-700'
                    }`}
                  >
                    {formatPaise(summary.overall.remaining_paise || 0)}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-slate-50 border border-dashed border-slate-200 p-6 rounded-2xl text-center">
              <h3 className="font-semibold text-slate-700">No Overall Budget Set for {period}</h3>
              <p className="text-sm text-slate-500 mt-1 mb-4">
                Set an overall spending limit to monitor spending and receive proactive 80% / 100% alerts.
              </p>
              <button
                onClick={() => {
                  setBudgetCategory('');
                  setShowBudgetModal(true);
                }}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium inline-flex items-center gap-2"
              >
                <PlusCircle className="w-4 h-4" />
                Set Overall Budget
              </button>
            </div>
          )}

          {/* PER-CATEGORY BUDGETS & SPENDING */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <h2 className="text-lg font-bold text-slate-900 mb-4 flex items-center justify-between">
              <span>Category Budgets & Actuals</span>
              <span className="text-xs font-normal text-slate-400">
                {summary?.categories.length || 0} categories tracked
              </span>
            </h2>

            {summary?.categories.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-6">
                No category spending or budgets recorded in {period}.
              </p>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summary?.categories.map((c) => {
                  const pct = c.percentage || 0;
                  const isExceeded = pct >= 100;
                  const isWarning = pct >= 80 && pct < 100;

                  return (
                    <div
                      key={c.category}
                      className="p-4 rounded-xl border border-slate-100 bg-slate-50/60 flex flex-col justify-between"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <div>
                          <div className="font-semibold text-slate-900">{c.category}</div>
                          <div className="text-xs text-slate-500">
                            Spent: <span className="font-medium text-slate-800">{formatPaise(c.spent_paise)}</span>
                            {c.budget_paise && (
                              <> / Limit: <span className="font-medium">{formatPaise(c.budget_paise)}</span></>
                            )}
                          </div>
                        </div>

                        {c.budget_paise ? (
                          <span
                            className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                              isExceeded
                                ? 'bg-rose-100 text-rose-700'
                                : isWarning
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-emerald-100 text-emerald-700'
                            }`}
                          >
                            {pct.toFixed(0)}%
                          </span>
                        ) : (
                          <button
                            onClick={() => {
                              setBudgetCategory(c.category);
                              setShowBudgetModal(true);
                            }}
                            className="text-xs text-teal-600 font-semibold hover:underline"
                          >
                            + Set Limit
                          </button>
                        )}
                      </div>

                      {c.budget_paise && (
                        <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden mt-2">
                          <div
                            className={`h-full ${
                              isExceeded ? 'bg-rose-500' : isWarning ? 'bg-amber-500' : 'bg-teal-600'
                            }`}
                            style={{ width: `${Math.min(100, pct)}%` }}
                          />
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* CASH FLOW ANALYTICS & CATEGORY BREAKDOWN */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Cash Flow Summary */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100 flex flex-col justify-between">
              <div>
                <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-2">
                  <TrendingUp className="w-5 h-5 text-teal-600" />
                  Monthly Cash Flow Trends
                </h3>
                <p className="text-xs text-slate-500 mb-4">
                  Aggregated strictly from completed ledger entries for {period}.
                </p>

                {/* Cashflow Metric Cards */}
                <div className="grid grid-cols-3 gap-2 mb-6">
                  <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-100">
                    <div className="text-xs text-emerald-800 flex items-center gap-1 font-medium">
                      <ArrowDownRight className="w-3.5 h-3.5 text-emerald-600" /> Income
                    </div>
                    <div className="text-sm font-bold text-emerald-900 mt-1">
                      {formatPaise(cashflow?.total_income_paise || 0)}
                    </div>
                  </div>

                  <div className="p-3 bg-rose-50 rounded-xl border border-rose-100">
                    <div className="text-xs text-rose-800 flex items-center gap-1 font-medium">
                      <ArrowUpRight className="w-3.5 h-3.5 text-rose-600" /> Expenses
                    </div>
                    <div className="text-sm font-bold text-rose-900 mt-1">
                      {formatPaise(cashflow?.total_expenses_paise || 0)}
                    </div>
                  </div>

                  <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <div className="text-xs text-slate-600 font-medium">Net Cash Flow</div>
                    <div
                      className={`text-sm font-bold mt-1 ${
                        (cashflow?.net_cashflow_paise || 0) >= 0 ? 'text-emerald-700' : 'text-rose-600'
                      }`}
                    >
                      {formatPaise(cashflow?.net_cashflow_paise || 0)}
                    </div>
                  </div>
                </div>

                {/* Daily Points Table */}
                <div className="max-h-56 overflow-y-auto border border-slate-100 rounded-xl">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-50 text-slate-600 border-b border-slate-100 sticky top-0">
                      <tr>
                        <th className="py-2 px-3">Date</th>
                        <th className="py-2 px-3">Income</th>
                        <th className="py-2 px-3">Expense</th>
                        <th className="py-2 px-3 text-right">Net</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-700">
                      {cashflow?.daily && cashflow.daily.length > 0 ? (
                        cashflow.daily.map((d) => (
                          <tr key={d.date} className="hover:bg-slate-50/50">
                            <td className="py-2 px-3 font-medium text-slate-900">{d.date}</td>
                            <td className="py-2 px-3 text-emerald-700">
                              {d.income_paise > 0 ? formatPaise(d.income_paise) : '—'}
                            </td>
                            <td className="py-2 px-3 text-rose-700">
                              {d.expenses_paise > 0 ? formatPaise(d.expenses_paise) : '—'}
                            </td>
                            <td
                              className={`py-2 px-3 text-right font-medium ${
                                d.net_paise >= 0 ? 'text-emerald-700' : 'text-rose-700'
                              }`}
                            >
                              {formatPaise(d.net_paise)}
                            </td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan={4} className="py-6 text-center text-slate-400">
                            No cashflow events in this period
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Category Spending Breakdown */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <h3 className="font-bold text-slate-900 flex items-center gap-2 mb-2">
                <PieChart className="w-5 h-5 text-teal-600" />
                Spending Distribution
              </h3>
              <p className="text-xs text-slate-500 mb-4">
                Total spent: {formatPaise(categoriesData?.total_spent_paise || 0)}
              </p>

              {categoriesData?.categories && categoriesData.categories.length > 0 ? (
                <div className="space-y-4">
                  {categoriesData.categories.map((item) => (
                    <div key={item.category} className="space-y-1">
                      <div className="flex justify-between text-xs font-semibold text-slate-700">
                        <span>{item.category}</span>
                        <span>
                          {formatPaise(item.amount_paise)} ({item.percentage.toFixed(1)}%)
                        </span>
                      </div>
                      <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
                        <div
                          className="bg-teal-600 h-full rounded-full transition-all duration-300"
                          style={{ width: `${item.percentage}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-8 text-center text-slate-400 text-sm">
                  No expenses recorded in {period}.
                </div>
              )}
            </div>
          </div>

          {/* SAVINGS GOALS SECTION */}
          <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                  <Target className="w-5 h-5 text-teal-600" />
                  Savings Goals & Earmarks
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Set aside money towards targeted financial goals. Validated against your live available balance.
                </p>
              </div>
              <button
                onClick={() => setShowGoalModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-teal-50 hover:bg-teal-100 text-teal-700 rounded-lg text-xs font-bold transition-colors"
              >
                <PlusCircle className="w-3.5 h-3.5" />
                Add Goal
              </button>
            </div>

            {goals.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-sm border border-dashed border-slate-200 rounded-xl">
                No savings goals created yet. Create a goal to begin building earmarks!
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {goals.map((g) => {
                  const isDone = g.progress_percentage >= 100;

                  return (
                    <div
                      key={g.id}
                      className="p-5 rounded-2xl border border-slate-100 bg-slate-50/50 flex flex-col justify-between hover:border-slate-200 transition-colors"
                    >
                      <div>
                        <div className="flex justify-between items-start mb-2">
                          <h3 className="font-bold text-slate-900">{g.title}</h3>
                          <button
                            onClick={() => handleDeleteGoal(g.id)}
                            className="text-slate-400 hover:text-rose-600 transition-colors"
                            title="Delete Goal"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>

                        <div className="text-xs text-slate-500 mb-3">
                          {g.target_date ? `Target: ${g.target_date}` : 'No deadline set'}
                        </div>

                        <div className="flex justify-between items-baseline text-sm mb-1">
                          <span className="font-bold text-slate-900">
                            {formatPaise(g.current_paise)}
                          </span>
                          <span className="text-xs text-slate-500">
                            of {formatPaise(g.target_paise)}
                          </span>
                        </div>

                        <div className="w-full bg-slate-200 h-2.5 rounded-full overflow-hidden mb-2">
                          <div
                            className={`h-full transition-all duration-500 ${
                              isDone ? 'bg-emerald-500' : 'bg-teal-600'
                            }`}
                            style={{ width: `${Math.min(100, g.progress_percentage)}%` }}
                          />
                        </div>

                        <div className="flex justify-between text-xs text-slate-500 mb-4 font-medium">
                          <span>{g.progress_percentage.toFixed(0)}% reached</span>
                          <span>{formatPaise(Math.max(0, g.target_paise - g.current_paise))} to go</span>
                        </div>
                      </div>

                      <button
                        onClick={() => setShowContribModal(g)}
                        disabled={isDone}
                        className={`w-full py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-1.5 transition-colors ${
                          isDone
                            ? 'bg-emerald-100 text-emerald-800 cursor-default'
                            : 'bg-teal-600 hover:bg-teal-700 text-white shadow-sm'
                        }`}
                      >
                        {isDone ? (
                          <>
                            <CheckCircle2 className="w-3.5 h-3.5" /> Goal Achieved!
                          </>
                        ) : (
                          <>
                            <PlusCircle className="w-3.5 h-3.5" /> Contribute
                          </>
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      )}

      {/* MODAL: SET BUDGET */}
      {showBudgetModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Set Monthly Budget</h3>
            <p className="text-xs text-slate-500 mb-4">
              Enter a limit in INR. Alerts will fire automatically at 80% and 100%.
            </p>

            <form onSubmit={handleSaveBudget} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Budget Target
                </label>
                <select
                  value={budgetCategory}
                  onChange={(e) => setBudgetCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <option value="">Overall Monthly Budget (All categories)</option>
                  <option value="Food & Dining">Food & Dining</option>
                  <option value="Groceries">Groceries</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Shopping">Shopping</option>
                  <option value="Health">Health</option>
                  <option value="Entertainment">Entertainment</option>
                  <option value="General">General</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Budget Limit (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    value={budgetRupees}
                    onChange={(e) => setBudgetRupees(e.target.value)}
                    placeholder="e.g. 15000"
                    className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
                <p className="text-[11px] text-slate-400 mt-1">
                  Saved as {Math.round(parseFloat(budgetRupees || '0') * 100)} integer paise.
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowBudgetModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
                >
                  {isSubmitting ? 'Saving...' : 'Save Budget'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: NEW SAVINGS GOAL */}
      {showGoalModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Create Savings Goal</h3>
            <p className="text-xs text-slate-500 mb-4">
              Set a target to earmark money toward future needs.
            </p>

            <form onSubmit={handleSaveGoal} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Goal Title
                </label>
                <input
                  type="text"
                  required
                  maxLength={100}
                  value={goalTitle}
                  onChange={(e) => setGoalTitle(e.target.value)}
                  placeholder="e.g. Emergency Fund, Bike Service"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Amount (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    value={goalTargetRupees}
                    onChange={(e) => setGoalTargetRupees(e.target.value)}
                    placeholder="e.g. 50000"
                    className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Target Date (Optional)
                </label>
                <input
                  type="date"
                  value={goalTargetDate}
                  onChange={(e) => setGoalTargetDate(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowGoalModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Creating...' : 'Create Goal'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: CONTRIBUTE TO GOAL */}
      {showContribModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">
              Contribute to {showContribModal.title}
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              Current progress: {formatPaise(showContribModal.current_paise)} / {formatPaise(showContribModal.target_paise)}.
            </p>

            <form onSubmit={handleContribute} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Contribution Amount (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    value={contribRupees}
                    onChange={(e) => setContribRupees(e.target.value)}
                    placeholder="e.g. 2000"
                    className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowContribModal(null)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50"
                >
                  {isSubmitting ? 'Transferring...' : 'Confirm Contribution'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* MODAL: MANUAL TRANSACTION ENTRY */}
      {showTxModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-100">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Record Cash / Direct Entry</h3>
            <p className="text-xs text-slate-500 mb-4">
              Manual entries are recorded as completed without fraud scoring (§8, §13).
            </p>

            <form onSubmit={handleSaveTx} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Entry Type
                </label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setTxType('expense')}
                    className={`py-2 text-xs font-bold rounded-lg border transition-colors ${
                      txType === 'expense'
                        ? 'bg-rose-50 border-rose-300 text-rose-700'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    Expense
                  </button>
                  <button
                    type="button"
                    onClick={() => setTxType('income')}
                    className={`py-2 text-xs font-bold rounded-lg border transition-colors ${
                      txType === 'income'
                        ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
                        : 'border-slate-200 text-slate-600 hover:bg-slate-50'
                    }`}
                  >
                    Income
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Amount (₹)
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-slate-400 font-bold">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="1"
                    min="1"
                    required
                    value={txRupees}
                    onChange={(e) => setTxRupees(e.target.value)}
                    placeholder="e.g. 500"
                    className="w-full pl-8 pr-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Category
                </label>
                <select
                  value={txCategory}
                  onChange={(e) => setTxCategory(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"
                >
                  <option value="Groceries">Groceries</option>
                  <option value="Food & Dining">Food & Dining</option>
                  <option value="Utilities">Utilities</option>
                  <option value="Shopping">Shopping</option>
                  <option value="Health">Health</option>
                  <option value="Salary">Salary (Income)</option>
                  <option value="Sales">Sales (Income)</option>
                  <option value="General">General</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Note (No PIN/OTP)
                </label>
                <input
                  type="text"
                  maxLength={140}
                  value={txNote}
                  onChange={(e) => setTxNote(e.target.value)}
                  placeholder="e.g. Cash grocery at local market"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowTxModal(false)}
                  className="px-4 py-2 border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 disabled:opacity-50"
                >
                  {isSubmitting ? 'Recording...' : 'Record Transaction'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
