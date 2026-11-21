import React, { useEffect, useState } from 'react';
import { CheckCircle2, Eye, RefreshCw, ShieldAlert, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { StatementPreview, StatementRequest } from '../types';
import { formatPaise } from '../types';

export const StatementQueuePage: React.FC = () => {
  const [requests, setRequests] = useState<StatementRequest[]>([]);
  const [notes, setNotes] = useState<Record<number, string>>({});
  const [previews, setPreviews] = useState<Record<number, StatementPreview>>({});
  const [previewLoadingId, setPreviewLoadingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busyId, setBusyId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function loadQueue() {
    setLoading(true); setError(null);
    try { setRequests(await api.getStatementQueue()); }
    catch (err: any) { setError(err?.message || 'Could not load statement requests.'); }
    finally { setLoading(false); }
  }
  useEffect(() => { void loadQueue(); }, []);

  async function decide(requestId: number, decision: 'approved' | 'rejected') {
    const note = (notes[requestId] || '').trim();
    if (note.length < 5) { setError('Add a review note of at least 5 characters.'); return; }
    setBusyId(requestId); setError(null); setNotice(null);
    try {
      await api.decideStatementRequest(requestId, decision, note);
      setRequests((current) => current.filter((request) => request.id !== requestId));
      setNotice(`Statement request ${decision}.`);
    } catch (err: any) { setError(err?.message || 'Could not update this request.'); }
    finally { setBusyId(null); }
  }

  async function togglePreview(requestId: number) {
    if (previews[requestId]) {
      setPreviews((current) => {
        const next = { ...current };
        delete next[requestId];
        return next;
      });
      return;
    }
    setPreviewLoadingId(requestId); setError(null);
    try {
      const preview = await api.getStatementPreview(requestId);
      setPreviews((current) => ({ ...current, [requestId]: preview }));
    } catch (err: any) { setError(err?.message || 'Could not preview the statement rows.'); }
    finally { setPreviewLoadingId(null); }
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-5">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 bg-slate-900 text-white rounded-2xl p-6">
        <div className="flex items-start gap-3"><ShieldAlert className="w-6 h-6 text-amber-300 mt-1" /><div><h1 className="text-xl font-bold">Statement Approval Queue</h1><p className="mt-1 text-xs text-slate-300">Review PayGuard activity statement requests. Approval releases a customer report; it does not certify bank records.</p></div></div>
        <button onClick={() => void loadQueue()} disabled={loading} className="inline-flex items-center gap-1.5 rounded-lg bg-slate-700 px-3 py-2 text-xs font-semibold hover:bg-slate-600 disabled:opacity-50"><RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} /> Refresh</button>
      </header>

      {error && <div role="alert" className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">{error}</div>}
      {notice && <div role="status" className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{notice}</div>}
      {loading ? <p className="text-sm text-slate-500">Loading requests…</p> : requests.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 text-center text-sm text-slate-500">No pending statement requests.</div>
      ) : requests.map((request) => (
        <article key={request.id} className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div><p className="text-xs font-semibold uppercase tracking-wide text-indigo-700">Request #{request.id}</p><h2 className="mt-1 text-base font-bold text-slate-900">Customer: {request.requester_username || `User ${request.user_id}`}</h2><p className="mt-1 text-sm text-slate-600">Period: {request.start_date} to {request.end_date}</p><p className="text-xs text-slate-500">{request.transaction_count} completed record(s) · Requested {new Date(request.requested_at).toLocaleString()}</p></div>
            <span className="self-start rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-bold uppercase text-amber-800">Pending</span>
          </div>
          <button onClick={() => void togglePreview(request.id)} disabled={previewLoadingId === request.id} className="mt-4 inline-flex items-center gap-1.5 rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50">
            <Eye className="w-3.5 h-3.5" /> {previewLoadingId === request.id ? 'Loading preview…' : previews[request.id] ? 'Hide transaction preview' : 'Preview transactions'}
          </button>
          {previews[request.id] && (
            <div className="mt-3 rounded-xl border border-indigo-100 bg-indigo-50/40 p-3">
              <p className="mb-2 text-xs text-slate-600">Showing {previews[request.id].rows.length} of {previews[request.id].total_count} completed transaction(s) in this report.</p>
              {previews[request.id].rows.length === 0 ? <p className="text-xs text-slate-500">No completed transactions fall within this date range.</p> : (
                <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                  <table className="min-w-full text-left text-xs">
                    <thead className="bg-slate-50 text-slate-500"><tr><th className="px-3 py-2">Date</th><th className="px-3 py-2">Description</th><th className="px-3 py-2">Category</th><th className="px-3 py-2">Type</th><th className="px-3 py-2 text-right">Amount</th><th className="px-3 py-2">Source</th></tr></thead>
                    <tbody className="divide-y divide-slate-100">{previews[request.id].rows.map((row, index) => <tr key={`${row.transaction_date}-${index}`}><td className="px-3 py-2 whitespace-nowrap">{new Date(row.transaction_date).toLocaleDateString()}</td><td className="px-3 py-2">{row.description}</td><td className="px-3 py-2">{row.category}</td><td className="px-3 py-2 capitalize">{row.type}</td><td className="px-3 py-2 text-right whitespace-nowrap">{formatPaise(row.amount_paise)}</td><td className="px-3 py-2 whitespace-nowrap">{row.source}</td></tr>)}</tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          <label className="mt-4 block text-xs font-semibold text-slate-700">Decision note <span className="font-normal text-slate-500">(required, at least 5 characters)</span>
            <textarea rows={2} maxLength={500} value={notes[request.id] || ''} onChange={(event) => setNotes((current) => ({ ...current, [request.id]: event.target.value }))} className="mt-1 w-full rounded-lg border border-slate-300 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Record the reason for approving or rejecting this request." />
          </label>
          <div className="mt-3 flex flex-wrap gap-2">
            <button onClick={() => void decide(request.id, 'approved')} disabled={busyId === request.id} className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3.5 py-2 text-xs font-bold text-white hover:bg-emerald-800 disabled:opacity-50"><CheckCircle2 className="w-4 h-4" /> Approve report</button>
            <button onClick={() => void decide(request.id, 'rejected')} disabled={busyId === request.id} className="inline-flex items-center gap-1.5 rounded-lg bg-rose-700 px-3.5 py-2 text-xs font-bold text-white hover:bg-rose-800 disabled:opacity-50"><XCircle className="w-4 h-4" /> Reject request</button>
          </div>
        </article>
      ))}
    </div>
  );
};
