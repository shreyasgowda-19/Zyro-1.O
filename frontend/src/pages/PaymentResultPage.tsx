import React, { useState, useEffect } from 'react';
import { useParams, useLocation, Link } from 'react-router-dom';
import { ShieldCheck, AlertTriangle, ShieldAlert, CheckCircle, XCircle, ArrowLeft, Info, HelpCircle } from 'lucide-react';
import { api, getErrorMessage } from '../services/api';
import { formatPaise } from '../types';
import { useLanguage } from '../contexts/LanguageContext';

export const PaymentResultPage: React.FC = () => {
  const { t } = useLanguage();
  const { id } = useParams<{ id: string }>();
  const location = useLocation();

  const [payment, setPayment] = useState<any>(location.state?.payment || null);
  const [breakdown, setBreakdown] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(!payment);
  const [acting, setActing] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [showConfirmModal, setShowConfirmModal] = useState<boolean>(false);
  const [showCancelModal, setShowCancelModal] = useState<boolean>(false);

  const paymentId = Number(id || payment?.id);

  useEffect(() => {
    async function loadData() {
      if (!paymentId) return;
      try {
        setLoading(true);
        const [txData, bdData] = await Promise.all([
          payment ? Promise.resolve(payment) : api.getPayment(paymentId),
          api.getRiskBreakdown(paymentId).catch(() => null),
        ]);
        setPayment(txData);
        setBreakdown(bdData);
      } catch (err) {
        setError(getErrorMessage(err));
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [paymentId]);

  async function handleConfirm() {
    setActing(true);
    setError(null);
    try {
      await api.confirmPayment(paymentId);
      const updated = await api.getPayment(paymentId);
      setPayment(updated);
      setShowConfirmModal(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setActing(false);
    }
  }

  async function handleCancel() {
    setActing(true);
    setError(null);
    try {
      await api.cancelPayment(paymentId);
      const updated = await api.getPayment(paymentId);
      setPayment(updated);
      setShowCancelModal(false);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setActing(false);
    }
  }

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto py-16 text-center space-y-3">
        <div className="w-8 h-8 border-2 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-xs text-slate-500 font-medium">Loading risk evaluation result...</p>
      </div>
    );
  }

  if (!payment) {
    return (
      <div className="max-w-md mx-auto py-16 text-center space-y-4">
        <AlertTriangle className="w-10 h-10 text-amber-500 mx-auto" />
        <h2 className="text-base font-bold text-slate-800">Payment Not Found</h2>
        <p className="text-xs text-slate-500">Could not retrieve details for transaction #{id}.</p>
        <Link to="/dashboard" className="inline-block px-4 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold">
          Return to Dashboard
        </Link>
      </div>
    );
  }

  const assessment = payment.assessment;
  const score = assessment?.score ?? 0;
  const band = assessment?.band ?? (score >= 70 ? 'high' : score >= 40 ? 'medium' : 'low');
  const reasons = assessment?.reasons ?? [];

  // Theme configuration based on risk band
  let ThemeIcon = ShieldCheck;
  let themeHeader = 'bg-linear-to-r from-emerald-600 to-teal-700 text-white';
  let bandTitle = 'Low Risk — Payment Processed';

  if (band === 'medium') {
    ThemeIcon = AlertTriangle;
    themeHeader = 'bg-linear-to-r from-amber-600 to-orange-700 text-white';
    bandTitle = 'Medium Risk — Confirmation Required';
  } else if (band === 'high') {
    ThemeIcon = ShieldAlert;
    themeHeader = 'bg-linear-to-r from-rose-700 to-red-800 text-white';
    bandTitle = 'High Risk — Payment Held for Review';
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 space-y-6">
      {/* Top Header Card */}
      <div className="rounded-2xl border border-slate-200 overflow-hidden shadow-xs bg-white">
        <div className={`p-6 ${themeHeader}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2.5 bg-white/20 rounded-xl backdrop-blur-xs">
                <ThemeIcon className="w-7 h-7 text-white" />
              </div>
              <div>
                <span className="text-[11px] font-semibold uppercase tracking-wider text-white/80 block">
                  Risk Analysis Complete
                </span>
                <h1 className="text-xl font-bold tracking-tight">{bandTitle}</h1>
              </div>
            </div>

            <div className="text-right">
              <span className="text-[10px] text-white/80 uppercase tracking-wider block font-semibold">Advisory Score</span>
              <span className="text-3xl font-extrabold tracking-tight">{score}</span>
              <span className="text-xs text-white/80 font-medium"> / 100</span>
            </div>
          </div>
        </div>

        {error && (
          <div className="m-4 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* State Banner & Guidance */}
        <div className="p-6 border-b border-slate-100">
          {payment.status === 'completed' && (
            <div className="flex items-start space-x-3 text-emerald-900 bg-emerald-50/70 p-4 rounded-xl border border-emerald-200">
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <p className="font-bold">Transaction Successfully Completed</p>
                <p className="text-emerald-800 text-[11px]">
                  Simulated payment of {formatPaise(payment.amount_paise)} to {payment.payee_name || payment.masked_payee} was verified with no blocking signals.
                </p>
              </div>
            </div>
          )}

          {payment.status === 'awaiting_confirmation' && (
            <div className="space-y-4">
              <div className="flex items-start space-x-3 text-amber-900 bg-amber-50 p-4 rounded-xl border border-amber-200">
                <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs space-y-1">
                  <p className="font-bold">Explicit Confirmation Required</p>
                  <p className="text-amber-800 text-[11px]">
                    PayGuard 360 scored this payment as Medium Risk. Funds have NOT moved yet. You may cancel safely without penalty or proceed if you are confident.
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCancelModal(true)}
                  disabled={acting}
                  className="px-4 py-2 border border-slate-300 text-slate-700 hover:bg-slate-100 rounded-lg text-xs font-semibold transition"
                >
                  Cancel Payment
                </button>
                <button
                  type="button"
                  onClick={() => setShowConfirmModal(true)}
                  disabled={acting}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                >
                  Confirm & Send Money
                </button>
              </div>
            </div>
          )}

          {payment.status === 'held' && (
            <div className="flex items-start space-x-3 text-rose-900 bg-rose-50 p-4 rounded-xl border border-rose-200">
              <ShieldAlert className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
              <div className="text-xs space-y-1">
                <p className="font-bold">High Risk Payment Held for Human Review</p>
                <p className="text-rose-800 text-[11px]">
                  Due to high risk indicators, this payment has been temporarily paused. Your funds of{' '}
                  <span className="font-bold">{formatPaise(payment.amount_paise)}</span> are safe and reserved in your held balance. A fraud reviewer will inspect this case. You will receive an alert once resolved.
                </p>
              </div>
            </div>
          )}

          {payment.status === 'cancelled' && (
            <div className="flex items-start space-x-3 text-slate-700 bg-slate-100 p-4 rounded-xl border border-slate-200">
              <XCircle className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
              <div className="text-xs space-y-0.5">
                <p className="font-bold">Payment Cancelled</p>
                <p className="text-[11px] text-slate-500">You cancelled this payment request. No funds were debited.</p>
              </div>
            </div>
          )}

          {payment.status === 'released' && (
            <div className="flex items-start space-x-3 text-blue-900 bg-blue-50 p-4 rounded-xl border border-blue-200">
              <Info className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
              <div className="text-xs space-y-0.5">
                <p className="font-bold">Payment Rejected by Reviewer (Funds Released)</p>
                <p className="text-[11px] text-blue-800">The fraud reviewer rejected this held payment. Reserved funds have been returned to your available balance.</p>
              </div>
            </div>
          )}
        </div>

        {/* Explainable Reasons Breakdown (§10, §16) */}
        <div className="p-6 space-y-4">
          <h2 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center justify-between">
            <span>Detection Reasons & Rule Factors</span>
            <span className="text-[10px] text-slate-400 font-normal">Deterministic rules version 1.0.0</span>
          </h2>

          {reasons.length === 0 ? (
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500 text-center font-medium">
              {t('pay.no_risk_signals')}
            </div>
          ) : (
            <div className="space-y-2.5">
              {reasons.map((r: any, idx: number) => (
                <div key={idx} className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-[10px] font-bold uppercase px-1.5 py-0.5 bg-slate-200 text-slate-700 rounded">
                        {r.rule_code}
                      </span>
                      <span className="text-xs font-bold text-slate-800">
                        {t(`risk.reason.${r.rule_code}`, r.params || {})}
                      </span>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-slate-700 bg-white border border-slate-200 px-2 py-0.5 rounded-full shrink-0">
                    +{r.points} pts
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* What-If / Score Reduction Breakdown (§10, D18) */}
          {breakdown?.what_would_change && breakdown.what_would_change.length > 0 && (
            <div className="mt-4 p-4 bg-indigo-50/70 border border-indigo-200 rounded-xl space-y-2.5">
              <div>
                <h3 className="text-xs font-bold text-indigo-950 flex items-center space-x-1.5">
                  <HelpCircle className="w-4 h-4 text-indigo-600" />
                  <span>{t('pay.what_would_change_title')}</span>
                </h3>
                <p className="text-[11px] text-indigo-800/80 mt-0.5">
                  {t('pay.what_would_change_subtitle')}
                </p>
              </div>
              <div className="space-y-2 pt-1 border-t border-indigo-200/60">
                {breakdown.what_would_change.map((w: any, i: number) => (
                  <div key={i} className="text-xs text-indigo-950 bg-white/70 p-2.5 rounded-lg border border-indigo-200/50 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
                    <div className="space-y-0.5">
                      <div className="font-semibold text-slate-900">{w.explanation}</div>
                      <div className="text-[11px] text-indigo-700 font-medium">
                        {t('pay.without_signal', {
                          without_score: w.without_signal_score,
                          without_band: w.without_signal_band,
                        })}
                      </div>
                    </div>
                    <span className="text-[11px] font-bold text-indigo-800 bg-indigo-100 px-2 py-0.5 rounded self-start sm:self-auto shrink-0">
                      -{w.reduction_points} pts
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Transaction Receipt Details */}
        <div className="p-6 bg-slate-50 border-t border-slate-200 space-y-3">
          <h2 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Transaction Summary</h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
            <div>
              <span className="text-[10px] text-slate-400 block">Transaction ID</span>
              <span className="font-semibold text-slate-800">#{payment.id}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Amount</span>
              <span className="font-bold text-slate-900">{formatPaise(payment.amount_paise)}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Payee</span>
              <span className="font-semibold text-slate-800">{payment.payee_name || payment.masked_payee}</span>
            </div>
            <div>
              <span className="text-[10px] text-slate-400 block">Category</span>
              <span className="font-semibold text-slate-800">{payment.category}</span>
            </div>
          </div>
        </div>

        {/* Bottom Actions */}
        <div className="p-4 bg-white border-t border-slate-200 flex items-center justify-between">
          <Link
            to="/dashboard"
            className="inline-flex items-center space-x-1.5 px-3 py-1.5 text-xs text-slate-600 hover:text-slate-900 font-medium transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Dashboard</span>
          </Link>

          <Link
            to="/pay"
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
          >
            <span>Send Another Payment</span>
          </Link>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="w-10 h-10 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900">Confirm Payment of {formatPaise(payment.amount_paise)}</h3>
              <p className="text-xs text-slate-500">
                You are overriding a Medium Risk warning. Are you completely sure you wish to transfer funds to {payment.payee_name || payment.masked_payee}?
              </p>
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowConfirmModal(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg font-medium"
              >
                Go Back
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={acting}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1"
              >
                {acting && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />}
                <span>Yes, Send Money</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Cancel Modal */}
      {showCancelModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 shadow-xl border border-slate-200">
            <div className="w-10 h-10 rounded-full bg-slate-100 text-slate-600 flex items-center justify-center">
              <XCircle className="w-5 h-5" />
            </div>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-slate-900">Cancel This Payment?</h3>
              <p className="text-xs text-slate-500">
                The payment will be cancelled immediately and marked as cancelled in your transaction history. No funds will be transferred.
              </p>
            </div>
            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setShowCancelModal(false)}
                className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded-lg font-medium"
              >
                Keep Reviewing
              </button>
              <button
                type="button"
                onClick={handleCancel}
                disabled={acting}
                className="px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-bold transition flex items-center space-x-1"
              >
                {acting && <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mr-1" />}
                <span>Confirm Cancellation</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
