import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle,
  UserCheck,
  FileText,
  History,
  RefreshCw,
  X
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { api, getErrorMessage } from '../services/api';
import type { ReviewCase } from '../types';
import { formatPaise } from '../types';

export const ReviewQueuePage: React.FC = () => {
  const { user } = useAuth();

  const [activeTab, setActiveTab] = useState<'queue' | 'audit'>('queue');
  const [cases, setCases] = useState<ReviewCase[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('open');
  const [caseTypeFilter, setCaseTypeFilter] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Inspector modal state
  const [selectedCase, setSelectedCase] = useState<ReviewCase | null>(null);
  const [decisionAction, setDecisionAction] = useState<string | null>(null);
  const [decisionNote, setDecisionNote] = useState<string>('');
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [decisionError, setDecisionError] = useState<string | null>(null);
  const [showConfirmAction, setShowConfirmAction] = useState<boolean>(false);

  // Audit log state
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [auditLoading, setAuditLoading] = useState<boolean>(false);

  useEffect(() => {
    if (activeTab === 'queue') {
      loadCases();
    } else {
      loadAudit();
    }
  }, [activeTab, statusFilter, caseTypeFilter]);

  async function loadCases() {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getReviewCases(statusFilter || undefined, caseTypeFilter || undefined);
      setCases(data.items || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function loadAudit() {
    setAuditLoading(true);
    try {
      const data = await api.getReviewAudit();
      setAuditLogs(data.items || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setAuditLoading(false);
    }
  }

  async function handleInspectCase(caseId: number) {
    setDecisionError(null);
    setDecisionNote('');
    setDecisionAction(null);
    setShowConfirmAction(false);
    try {
      const detailed = await api.getReviewCase(caseId);
      setSelectedCase(detailed);
    } catch (err) {
      setError(getErrorMessage(err));
    }
  }

  function handleInitiateAction(action: string) {
    const trimmed = decisionNote.trim();
    if (trimmed.length < 5) {
      setDecisionError('A mandatory justification note of at least 5 characters is required before taking action.');
      return;
    }
    setDecisionAction(action);
    setDecisionError(null);
    setShowConfirmAction(true);
  }

  async function handleConfirmDecision() {
    if (!selectedCase || !decisionAction) return;

    setSubmitting(true);
    setDecisionError(null);

    try {
      const updated = await api.submitDecision(
        selectedCase.id,
        decisionAction,
        decisionNote.trim(),
        selectedCase.version
      );
      setSelectedCase(updated);
      setShowConfirmAction(false);
      setDecisionAction(null);
      setDecisionNote('');
      // Refresh background queue
      loadCases();
    } catch (err) {
      setDecisionError(getErrorMessage(err));
      setShowConfirmAction(false);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <div>
          <span className="text-xs font-semibold text-purple-600 uppercase tracking-wider block mb-0.5">
            {user?.role === 'supervisor' ? 'Supervisor Risk Authority' : 'Fraud Review Console'}
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Human Review Queue
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Inspect flagged high-risk payments. Customer identities and payees are masked under strict privacy boundaries.
          </p>
        </div>

        {/* Tab Toggle */}
        <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('queue')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'queue'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Review Queue
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('audit')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              activeTab === 'audit'
                ? 'bg-white text-slate-900 shadow-2xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Audit Log History
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {activeTab === 'queue' ? (
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          {/* Queue Filter Bar */}
          <div className="px-6 py-4 border-b border-slate-200 flex flex-wrap items-center justify-between gap-4 bg-slate-50/50">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold text-slate-700">Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-2.5 py-1 text-xs bg-white border border-slate-300 rounded-lg text-slate-700 font-medium"
              >
                <option value="open">Open Cases</option>
                {user?.role === 'supervisor' && <option value="escalated">Escalated (Supervisor Only)</option>}
                <option value="closed">Closed / Resolved</option>
                <option value="">All Statuses</option>
              </select>

              <span className="text-xs font-semibold text-slate-700 ml-2">Type:</span>
              <select
                value={caseTypeFilter}
                onChange={(e) => setCaseTypeFilter(e.target.value)}
                className="px-2.5 py-1 text-xs bg-white border border-slate-300 rounded-lg text-slate-700 font-medium"
              >
                <option value="">All Case Types</option>
                <option value="hold_review">Hold Review (Held Funds)</option>
                <option value="post_review">Post Review (Confirmed Payments)</option>
              </select>
            </div>

            <button
              onClick={loadCases}
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-lg text-xs font-medium transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Queue</span>
            </button>
          </div>

          {/* Queue List */}
          {loading ? (
            <div className="p-12 text-center space-y-2">
              <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-500 font-medium">Loading review queue...</p>
            </div>
          ) : cases.length === 0 ? (
            <div className="p-12 text-center space-y-3">
              <CheckCircle className="w-10 h-10 text-emerald-500 mx-auto" />
              <h3 className="text-sm font-bold text-slate-800">Review Queue Empty</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No cases match the selected filters. Use the Demo Simulator to launch high-risk scenarios.
              </p>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {cases.map((c) => {
                let badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
                if (c.band === 'medium') badgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
                else if (c.band === 'low') badgeClass = 'bg-emerald-50 text-emerald-700 border-emerald-200';

                return (
                  <div key={c.id} className="p-5 hover:bg-slate-50/80 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="space-y-1.5">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-xs font-bold text-slate-900">Case #{c.id}</span>
                        <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${badgeClass}`}>
                          Score: {c.score} ({c.band})
                        </span>
                        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                          {c.case_type === 'hold_review' ? 'Hold Review' : 'Post Review'}
                        </span>
                        {c.status === 'escalated' && (
                          <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-purple-100 text-purple-800 border border-purple-200">
                            Escalated
                          </span>
                        )}
                        {c.decision && (
                          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-slate-200 text-slate-800">
                            Decision: {c.decision}
                          </span>
                        )}
                      </div>

                      <div className="text-xs text-slate-600 flex flex-wrap items-center gap-x-4 gap-y-1">
                        <span>
                          Amount: <span className="font-bold text-slate-900">{formatPaise(c.amount_paise)}</span>
                        </span>
                        <span>Payee: <span className="font-mono">{c.masked_payee}</span></span>
                        <span>Customer Ref: <span className="font-mono">{c.masked_customer_ref}</span></span>
                        <span>Method: <span className="uppercase text-[11px] font-medium">{c.method}</span></span>
                      </div>

                      {c.reasons && c.reasons.length > 0 && (
                        <div className="flex flex-wrap items-center gap-1.5 pt-1">
                          {c.reasons.map((r, i) => (
                            <span key={i} className="text-[10px] font-medium px-2 py-0.5 bg-slate-100 text-slate-600 rounded">
                              {r.rule_code}: +{r.points} pts
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    <button
                      onClick={() => handleInspectCase(c.id)}
                      className="inline-flex items-center space-x-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold shadow-xs transition shrink-0 self-start md:self-center"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Inspect Case</span>
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        /* Audit Log History Tab */
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <History className="w-4 h-4 text-purple-600" />
              <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                Append-Only Review Audit Trail (§12, §13)
              </h2>
            </div>
            <button
              onClick={loadAudit}
              disabled={auditLoading}
              className="text-xs text-slate-600 hover:text-slate-900 font-medium"
            >
              Refresh Audit
            </button>
          </div>

          {auditLoading ? (
            <div className="p-12 text-center space-y-2">
              <div className="w-8 h-8 border-2 border-purple-600 border-t-transparent rounded-full animate-spin mx-auto" />
              <p className="text-xs text-slate-500 font-medium">Loading audit logs...</p>
            </div>
          ) : auditLogs.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-500">
              No audit logs recorded yet.
            </div>
          ) : (
            <div className="divide-y divide-slate-100 text-xs">
              {auditLogs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-slate-50/60 transition flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="space-y-0.5">
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900">{log.action}</span>
                      <span className="text-[10px] uppercase font-semibold px-2 py-0.2 bg-slate-100 text-slate-700 rounded">
                        {log.entity_type} #{log.entity_id}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        by <span className="font-semibold text-slate-700">{log.actor_username || 'system'}</span> ({log.actor_role || 'system'})
                      </span>
                    </div>
                    {log.safe_metadata && Object.keys(log.safe_metadata).length > 0 && (
                      <p className="text-[11px] text-slate-500 font-mono">
                        {JSON.stringify(log.safe_metadata)}
                      </p>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 shrink-0">
                    {new Date(log.created_at).toLocaleString()}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Case Inspector Modal / Drawer */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-slate-200">
            {/* Modal Header */}
            <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between z-10">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-purple-100 rounded-lg text-purple-700">
                  <ShieldAlert className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <h2 className="text-base font-bold text-slate-900">Review Case #{selectedCase.id}</h2>
                    <span className="text-[10px] font-bold uppercase px-2 py-0.5 rounded bg-slate-100 text-slate-700 border border-slate-200">
                      Version {selectedCase.version}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Type: <span className="font-semibold">{selectedCase.case_type}</span> • Status:{' '}
                    <span className="font-semibold">{selectedCase.status}</span>
                  </p>
                </div>
              </div>

              <button
                onClick={() => setSelectedCase(null)}
                className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-6">
              {decisionError && (
                <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 shrink-0" />
                  <span className="font-medium">{decisionError}</span>
                </div>
              )}

              {/* Case Attributes Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Amount</span>
                  <span className="font-bold text-slate-900 text-sm">{formatPaise(selectedCase.amount_paise)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Masked Payee</span>
                  <span className="font-mono font-semibold text-slate-800">{selectedCase.masked_payee}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Masked Customer</span>
                  <span className="font-mono font-semibold text-slate-800">{selectedCase.masked_customer_ref}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold block">Risk Band</span>
                  <span className="font-bold uppercase text-rose-700">{selectedCase.score}/100 ({selectedCase.band})</span>
                </div>
              </div>

              {/* Detection Reasons */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                  Detection Reasons ({selectedCase.reasons?.length || 0})
                </h3>
                <div className="space-y-1.5">
                  {selectedCase.reasons?.map((r, i) => (
                    <div key={i} className="p-3 bg-slate-50 border border-slate-200 rounded-lg flex items-center justify-between text-xs">
                      <div>
                        <span className="font-bold text-slate-800 mr-2">{r.rule_code}</span>
                        <span className="text-slate-600 font-mono text-[11px]">{JSON.stringify(r.params)}</span>
                      </div>
                      <span className="font-bold text-slate-700 bg-white px-2 py-0.5 rounded border border-slate-200">
                        +{r.points} pts
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action History / Audit Trail on this Case */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center space-x-1.5">
                  <History className="w-3.5 h-3.5 text-slate-500" />
                  <span>Case Action History (§12)</span>
                </h3>
                {selectedCase.actions && selectedCase.actions.length > 0 ? (
                  <div className="space-y-2">
                    {selectedCase.actions.map((act) => (
                      <div key={act.id} className="p-3 bg-purple-50/50 border border-purple-200/60 rounded-lg text-xs space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-purple-900 uppercase text-[11px]">
                            {act.action} by {act.actor_username} ({act.actor_role})
                          </span>
                          <span className="text-[10px] text-slate-400">{new Date(act.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-slate-700 text-[11px]">"{act.note}"</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No prior actions taken on this case.</p>
                )}
              </div>

              {/* Consequential Actions Panel (Only if open or escalated) */}
              {selectedCase.status !== 'closed' ? (
                <div className="border-t border-slate-200 pt-5 space-y-4">
                  <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
                    Take Decision Action (§12)
                  </h3>

                  {/* Mandatory Note */}
                  <div className="space-y-1">
                    <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
                      <span>Decision Justification Note *</span>
                      <span className={`text-[10px] ${decisionNote.trim().length >= 5 ? 'text-emerald-600' : 'text-slate-400'}`}>
                        {decisionNote.trim().length}/500 chars (min 5 required)
                      </span>
                    </label>
                    <textarea
                      rows={3}
                      value={decisionNote}
                      onChange={(e) => setDecisionNote(e.target.value)}
                      placeholder="Provide a detailed reason for approving, rejecting, or escalating this transaction..."
                      maxLength={500}
                      className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-purple-500"
                    />
                  </div>

                  {/* Action Buttons depending on Case Type & Status */}
                  <div className="flex flex-wrap items-center gap-2 pt-2">
                    {selectedCase.case_type === 'hold_review' && selectedCase.status === 'open' && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('approve')}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Approve Payment
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('reject')}
                          className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Reject Payment (Release Funds)
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('escalate')}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Escalate to Supervisor
                        </button>
                      </>
                    )}

                    {selectedCase.case_type === 'post_review' && selectedCase.status === 'open' && (
                      <>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('mark_false_alarm')}
                          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Mark False Alarm
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('mark_confirmed_fraud')}
                          className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Mark Confirmed Fraud (Flag Payee)
                        </button>
                        <button
                          type="button"
                          onClick={() => handleInitiateAction('escalate')}
                          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                        >
                          Escalate to Supervisor
                        </button>
                      </>
                    )}

                    {selectedCase.status === 'escalated' && user?.role === 'supervisor' && (
                      <>
                        {selectedCase.case_type === 'hold_review' ? (
                          <>
                            <button
                              type="button"
                              onClick={() => handleInitiateAction('approve')}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                            >
                              Supervisor Final Approve
                            </button>
                            <button
                              type="button"
                              onClick={() => handleInitiateAction('reject')}
                              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                            >
                              Supervisor Final Reject
                            </button>
                          </>
                        ) : (
                          <>
                            <button
                              type="button"
                              onClick={() => handleInitiateAction('mark_false_alarm')}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                            >
                              Supervisor Final: False Alarm
                            </button>
                            <button
                              type="button"
                              onClick={() => handleInitiateAction('mark_confirmed_fraud')}
                              className="px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                            >
                              Supervisor Final: Confirmed Fraud
                            </button>
                          </>
                        )}
                      </>
                    )}
                  </div>
                </div>
              ) : (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-600 flex items-center space-x-2">
                  <CheckCircle className="w-4 h-4 text-emerald-600 shrink-0" />
                  <span>This case is closed with decision: <strong className="uppercase">{selectedCase.decision}</strong>.</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Action Confirmation Dialog */}
      {showConfirmAction && (
        <div className="fixed inset-0 z-60 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="w-10 h-10 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center">
              <UserCheck className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900">Confirm Action: {decisionAction}</h3>
              <p className="text-xs text-slate-500">
                Are you sure you want to execute <strong className="text-slate-800">{decisionAction}</strong> on Case #{selectedCase?.id}? This decision will be logged permanently in the append-only audit trail.
              </p>
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmAction(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg font-medium"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDecision}
                disabled={submitting}
                className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1"
              >
                {submitting && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />}
                <span>Execute Action</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
