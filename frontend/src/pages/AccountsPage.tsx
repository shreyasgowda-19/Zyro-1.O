import React, { useEffect, useState } from 'react';
import { AlertCircle, Landmark, Plus, RefreshCw, Trash2 } from 'lucide-react';
import { api } from '../services/api';
import type { TrackedAccount } from '../types';
import { formatPaise } from '../types';

function parseRupees(value: string): number | null {
  const clean = value.trim().replace(/,/g, '');
  if (!/^-?\d+(\.\d{1,2})?$/.test(clean)) return null;
  const amount = Number(clean);
  if (!Number.isFinite(amount) || Math.abs(amount) > 10000000000) return null;
  return Math.round(amount * 100);
}

export const AccountsPage: React.FC = () => {
  const [accounts, setAccounts] = useState<TrackedAccount[]>([]);
  const [balanceDrafts, setBalanceDrafts] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [institutionName, setInstitutionName] = useState('');
  const [accountName, setAccountName] = useState('');
  const [accountType, setAccountType] = useState<TrackedAccount['account_type']>('savings');
  const [lastFour, setLastFour] = useState('');
  const [openingBalance, setOpeningBalance] = useState('');

  async function loadAccounts() {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getTrackedAccounts();
      setAccounts(result);
      setBalanceDrafts(Object.fromEntries(result.map((account) => [
        account.id,
        (account.reported_balance_paise / 100).toFixed(2),
      ])));
    } catch (err: any) {
      setError(err?.message || 'Could not load your accounts.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadAccounts(); }, []);

  async function handleAddAccount(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setNotice(null);
    const balancePaise = parseRupees(openingBalance);
    if (balancePaise === null) {
      setError('Enter a valid balance with up to two decimal places.');
      return;
    }
    setSaving(true);
    try {
      await api.createTrackedAccount({
        institution_name: institutionName.trim(),
        account_name: accountName.trim(),
        account_type: accountType,
        last_four: lastFour || undefined,
        reported_balance_paise: balancePaise,
      });
      setInstitutionName('');
      setAccountName('');
      setAccountType('savings');
      setLastFour('');
      setOpeningBalance('');
      setNotice('Account details saved. The balance is marked as manually reported.');
      await loadAccounts();
    } catch (err: any) {
      setError(err?.message || 'Could not save this account.');
    } finally {
      setSaving(false);
    }
  }

  async function handleUpdateBalance(accountId: number) {
    setError(null);
    setNotice(null);
    const balancePaise = parseRupees(balanceDrafts[accountId] ?? '');
    if (balancePaise === null) {
      setError('Enter a valid balance with up to two decimal places.');
      return;
    }
    setSaving(true);
    try {
      await api.updateTrackedAccountBalance(accountId, balancePaise);
      setNotice('Balance updated and timestamped.');
      await loadAccounts();
    } catch (err: any) {
      setError(err?.message || 'Could not update this balance.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(account: TrackedAccount) {
    if (!window.confirm(`Remove ${account.account_name} from your tracked accounts?`)) return;
    setError(null);
    setNotice(null);
    try {
      await api.deleteTrackedAccount(account.id);
      setAccounts((current) => current.filter((item) => item.id !== account.id));
      setNotice('Tracked account removed.');
    } catch (err: any) {
      setError(err?.message || 'Could not remove this account.');
    }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <header className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-teal-50 text-teal-700 p-3"><Landmark className="w-6 h-6" /></div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">My Accounts</h1>
            <p className="mt-1 text-sm text-slate-600">Record accounts and balances you want to track in one place.</p>
            <p className="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2">
              Balances are entered by you and do not update from your bank. These accounts are separate from FinShield’s simulated payment balance.
            </p>
          </div>
        </div>
      </header>

      {(error || notice) && (
        <div role={error ? 'alert' : 'status'} className={`rounded-xl border p-3 text-sm flex items-center gap-2 ${error ? 'bg-rose-50 border-rose-200 text-rose-800' : 'bg-emerald-50 border-emerald-200 text-emerald-800'}`}>
          {error && <AlertCircle className="w-4 h-4 shrink-0" />}
          <span>{error || notice}</span>
        </div>
      )}

      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2"><Plus className="w-4 h-4 text-teal-600" /> Add an account</h2>
        <form onSubmit={handleAddAccount} className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <label className="text-sm font-medium text-slate-700">Bank or institution name
            <input required maxLength={80} value={institutionName} onChange={(e) => setInstitutionName(e.target.value)} placeholder="e.g. Your bank" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
          </label>
          <label className="text-sm font-medium text-slate-700">Account nickname
            <input required maxLength={50} value={accountName} onChange={(e) => setAccountName(e.target.value)} placeholder="e.g. Everyday savings" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
          </label>
          <label className="text-sm font-medium text-slate-700">Account type
            <select value={accountType} onChange={(e) => setAccountType(e.target.value as TrackedAccount['account_type'])} className="mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500">
              <option value="savings">Savings</option><option value="current">Current</option><option value="cash">Cash</option><option value="other">Other</option>
            </select>
          </label>
          <label className="text-sm font-medium text-slate-700">Last 4 digits <span className="font-normal text-slate-400">(optional)</span>
            <input inputMode="numeric" pattern="[0-9]{4}" maxLength={4} value={lastFour} onChange={(e) => setLastFour(e.target.value.replace(/\D/g, '').slice(0, 4))} placeholder="1234" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
          </label>
          <label className="text-sm font-medium text-slate-700 sm:col-span-2">Current balance (₹)
            <input required type="number" step="0.01" value={openingBalance} onChange={(e) => setOpeningBalance(e.target.value)} placeholder="0.00" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
            <span className="mt-1 block text-xs font-normal text-slate-500">Enter the balance shown by your bank. You can update it later.</span>
          </label>
          <div className="sm:col-span-2">
            <button disabled={saving} className="inline-flex items-center gap-2 rounded-lg bg-teal-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-800 disabled:opacity-50">
              <Plus className="w-4 h-4" /> {saving ? 'Saving…' : 'Save account'}
            </button>
          </div>
        </form>
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-bold text-slate-900">Tracked accounts</h2>
          <button onClick={() => void loadAccounts()} disabled={loading} className="inline-flex items-center gap-1.5 text-sm text-slate-600 hover:text-teal-700 disabled:opacity-50"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
        </div>
        {loading ? <p className="text-sm text-slate-500">Loading accounts…</p> : accounts.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No accounts added yet. Add one above to start tracking your reported balance.</div>
        ) : accounts.map((account) => (
          <article key={account.id} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">{account.institution_name}</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900">{account.account_name}</h3>
                <p className="text-xs text-slate-500 capitalize">{account.account_type}{account.last_four ? ` · ending ${account.last_four}` : ''}</p>
              </div>
              <button onClick={() => void handleDelete(account)} className="self-start inline-flex items-center gap-1.5 text-xs font-medium text-rose-600 hover:text-rose-800"><Trash2 className="w-3.5 h-3.5" /> Remove</button>
            </div>
            <div className="mt-4 border-t border-slate-100 pt-4 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
              <div>
                <p className="text-xs text-slate-500">Last reported balance</p>
                <p className="text-2xl font-bold text-slate-900">{formatPaise(account.reported_balance_paise)}</p>
                <p className="text-xs text-slate-400">Updated {new Date(account.balance_as_of).toLocaleString()}</p>
              </div>
              <div className="flex flex-wrap items-end gap-2">
                <label className="text-xs font-medium text-slate-600">Update balance (₹)
                  <input type="number" step="0.01" value={balanceDrafts[account.id] ?? ''} onChange={(e) => setBalanceDrafts((current) => ({ ...current, [account.id]: e.target.value }))} className="mt-1 block w-44 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500" />
                </label>
                <button onClick={() => void handleUpdateBalance(account.id)} disabled={saving} className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold text-white hover:bg-slate-700 disabled:opacity-50">Update</button>
              </div>
            </div>
          </article>
        ))}
      </section>
    </div>
  );
};
