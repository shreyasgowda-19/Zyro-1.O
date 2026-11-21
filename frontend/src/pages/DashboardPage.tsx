import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Send, AlertTriangle, ShieldCheck, ShieldAlert, Sparkles, RefreshCw, Eye, Bell } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api, getErrorMessage } from '../services/api';
import type { BalanceSummary, AlertItem, Transaction, ReconciliationResult } from '../types';
import { formatPaise } from '../types';
import { DemoSimulatorModal } from '../components/common/DemoSimulatorModal';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [balances, setBalances] = useState<BalanceSummary>({
    completed_balance_paise: 0,
    held_balance_paise: 0,
    available_balance_paise: 0,
  });
  const [reconciliation, setReconciliation] = useState<ReconciliationResult | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isSimulatorOpen, setIsSimulatorOpen] = useState<boolean>(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  async function loadDashboardData() {
    setLoading(true);
    setError(null);
    try {
      const [balData, reconData, alertData, txData] = await Promise.all([
        api.getBalances(),
        api.getReconciliation().catch(() => null),
        api.getAlerts().catch(() => ({ items: [], unread_count: 0 })),
        api.getTransactions().catch(() => []),
      ]);

      setBalances(balData);
      setReconciliation(reconData);
      setAlerts(alertData.items || []);
      setTransactions(txData || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleDismissAlert(alertId: number) {
    try {
      await api.markAlertRead(alertId);
      setAlerts(prev => prev.map(a => a.id === alertId ? { ...a, read_at: new Date().toISOString() } : a));
    } catch (e) {
      console.error(e);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <span className="text-xs font-semibold text-teal-600 uppercase tracking-wider block mb-0.5">
            {user?.profile_type === 'business' ? 'Business Account' : 'Personal Account'}
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Welcome back, {user?.username}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time explainable fraud protection and single-source ledger reconciliation.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            type="button"
            onClick={() => setIsSimulatorOpen(true)}
            className="inline-flex items-center space-x-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 px-3.5 py-2 rounded-xl text-xs font-semibold transition"
          >
            <Sparkles className="w-4 h-4 text-indigo-500" />
            <span>Demo Attack Presets</span>
          </button>

          <Link
            to="/pay"
            className="inline-flex items-center space-x-2 bg-teal-600 hover:bg-teal-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-xs transition"
          >
            <Send className="w-4 h-4" />
            <span>Send Payment</span>
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Balances Card Grid (§8 Ledger definitions) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Available Balance */}
        <div className="bg-white p-5 rounded-2xl border border-teal-500/30 shadow-xs relative overflow-hidden">
          <div className="absolute top-0 right-0 w-24 h-24 bg-teal-500/5 rounded-bl-full pointer-events-none" />
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Available Balance</span>
            <span className="text-[10px] font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full border border-teal-200/50">
              Spendable
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-900 tracking-tight">
            {formatPaise(balances.available_balance_paise)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Completed minus held reserves</p>
        </div>

        {/* Held Balance */}
        <div className="bg-white p-5 rounded-2xl border border-amber-500/30 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Held (Under Review)</span>
            <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200/50">
              Reserved
            </span>
          </div>
          <div className="text-2xl font-bold text-amber-600 tracking-tight">
            {formatPaise(balances.held_balance_paise)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Pending fraud review decisions</p>
        </div>

        {/* Completed Balance */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-xs relative overflow-hidden">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-slate-500">Completed Balance</span>
            <span className="text-[10px] font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded-full">
              Settled
            </span>
          </div>
          <div className="text-2xl font-bold text-slate-700 tracking-tight">
            {formatPaise(balances.completed_balance_paise)}
          </div>
          <p className="text-[11px] text-slate-400 mt-1">Opening + Income − Expenses</p>
        </div>
      </div>

      {/* Live Reconciliation Badge (§8) */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-xs flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-lg ${reconciliation?.all_passed ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-100 text-slate-500'}`}>
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-bold text-slate-900">Ledger Single Source of Truth (§8)</span>
              {reconciliation?.all_passed ? (
                <span className="text-[10px] font-bold uppercase bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full border border-emerald-200">
                  Reconciled (4/4 Passed)
                </span>
              ) : (
                <span className="text-[10px] font-semibold uppercase bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                  Checking...
                </span>
              )}
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Available = Completed − Held • Category Totals = Total Spending • Cash Flow Balanced
            </p>
          </div>
        </div>

        <button
          onClick={loadDashboardData}
          disabled={loading}
          className="text-xs text-slate-500 hover:text-slate-800 flex items-center space-x-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Verify</span>
        </button>
      </div>

      {/* In-App Alerts Section (§14) */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Bell className="w-4 h-4 text-teal-600" />
              <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                In-App Safety & Budget Alerts
              </h2>
            </div>
            <span className="text-[11px] text-slate-500">
              {alerts.filter(a => !a.read_at).length} unread
            </span>
          </div>

          <div className="divide-y divide-slate-100">
            {alerts.slice(0, 3).map((a) => (
              <div key={a.id} className="p-4 hover:bg-slate-50/80 transition flex items-center justify-between gap-4">
                <div className="flex items-start space-x-3">
                  {a.type === 'fraud' ? (
                    <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                  )}
                  <div className="space-y-0.5">
                    <span className="text-xs font-bold text-slate-900 block">{a.title_code}</span>
                    <span className="text-[11px] text-slate-500 font-mono block">
                      {JSON.stringify(a.params)}
                    </span>
                  </div>
                </div>

                {!a.read_at && (
                  <button
                    onClick={() => handleDismissAlert(a.id)}
                    className="text-[11px] font-semibold text-teal-600 hover:text-teal-800 shrink-0"
                  >
                    Mark as read
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Transactions Table */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
            Recent Payments & Transactions
          </h2>
          <span className="text-[11px] text-slate-500 font-medium">
            Total recorded: {transactions.length}
          </span>
        </div>

        {transactions.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No transactions found. Click "Send Payment" to initiate your first simulated payment.
          </div>
        ) : (
          <div className="divide-y divide-slate-100 overflow-x-auto">
            {transactions.slice(0, 10).map((t) => {
              let statusBadge = 'bg-slate-100 text-slate-700';
              if (t.status === 'completed') statusBadge = 'bg-emerald-100 text-emerald-800';
              else if (t.status === 'held') statusBadge = 'bg-rose-100 text-rose-800 font-bold';
              else if (t.status === 'awaiting_confirmation') statusBadge = 'bg-amber-100 text-amber-800 font-bold';
              else if (t.status === 'released') statusBadge = 'bg-blue-100 text-blue-800';

              return (
                <div key={t.id} className="p-4 hover:bg-slate-50/60 transition flex items-center justify-between gap-4 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900">
                        {t.type === 'income' ? '+' : '-'}{formatPaise(t.amount_paise)}
                      </span>
                      <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${statusBadge}`}>
                        {t.status}
                      </span>
                      <span className="text-[10px] text-slate-400">#{t.id}</span>
                    </div>

                    <div className="text-slate-500 text-[11px] flex items-center space-x-3">
                      <span>Payee: <strong className="text-slate-700 font-normal">{t.payee_name || t.masked_payee || 'Direct Credit'}</strong></span>
                      <span>Category: <strong className="text-slate-700 font-normal">{t.category}</strong></span>
                      <span>Method: <strong className="text-slate-700 font-normal uppercase">{t.method}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 shrink-0">
                    <Link
                      to={`/payments/${t.id}/result`}
                      className="inline-flex items-center space-x-1 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-medium transition"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Risk</span>
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Demo Simulator Modal */}
      <DemoSimulatorModal
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
        onScenarioSelect={() => {
          setIsSimulatorOpen(false);
          navigate('/pay');
        }}
      />
    </div>
  );
};
