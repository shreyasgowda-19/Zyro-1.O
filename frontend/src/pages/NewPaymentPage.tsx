import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Send, Shield, AlertTriangle, CheckSquare, Square, Clock } from 'lucide-react';
import { api, getErrorMessage } from '../services/api';
import { formatPaise } from '../types';

export const NewPaymentPage: React.FC = () => {
  const navigate = useNavigate();

  const [payeeName, setPayeeName] = useState<string>('');
  const [payeeMasked, setPayeeMasked] = useState<string>('');
  const [amountRupees, setAmountRupees] = useState<string>('');
  const [category, setCategory] = useState<string>('General');
  const [method, setMethod] = useState<string>('upi');
  const [note, setNote] = useState<string>('');
  const [simulatedAt, setSimulatedAt] = useState<string>('');
  const [syntheticDevice, setSyntheticDevice] = useState<string>('D1');
  const [syntheticCity, setSyntheticCity] = useState<string>('Bengaluru');

  // Safety checklist states (§14)
  const [checkPayee, setCheckPayee] = useState<boolean>(false);
  const [checkNoPressure, setCheckNoPressure] = useState<boolean>(false);
  const [checkDetails, setCheckDetails] = useState<boolean>(false);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Check if a prefilled scenario was provided in sessionStorage
  useEffect(() => {
    const raw = sessionStorage.getItem('prefilled_scenario');
    if (raw) {
      try {
        const scenario = JSON.parse(raw);
        applyScenario(scenario);
      } catch (e) {
        console.error(e);
      } finally {
        sessionStorage.removeItem('prefilled_scenario');
      }
    }
  }, []);

  function applyScenario(scenario: any) {
    const p = scenario.payload;
    if (!p) return;
    setPayeeName(p.payee_display_name || '');
    setPayeeMasked(p.payee_masked_identifier || '');
    setAmountRupees(p.amount_paise ? (p.amount_paise / 100).toString() : '');
    setCategory(p.category || 'General');
    setMethod(p.method || 'upi');
    setNote(p.note || '');
    setSimulatedAt(p.simulated_at || '');
    if (p.synthetic_device_tag) setSyntheticDevice(p.synthetic_device_tag);
    if (p.synthetic_city_tag) setSyntheticCity(p.synthetic_city_tag);
    // Pre-check verification checklist
    setCheckPayee(true);
    setCheckNoPressure(true);
    setCheckDetails(true);
  }

  // Integer paise conversion
  const parsedPaise = amountRupees && !isNaN(Number(amountRupees)) ? Math.round(Number(amountRupees) * 100) : 0;
  const isChecklistComplete = checkPayee && checkNoPressure && checkDetails;
  const isFormValid = payeeName.trim().length > 0 && parsedPaise >= 100 && parsedPaise <= 20000000 && isChecklistComplete;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!isFormValid || loading) return;

    setLoading(true);
    setError(null);

    const idempotencyKey = `pay_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    const payload: any = {
      amount_paise: parsedPaise,
      category,
      payee_display_name: payeeName.trim(),
      payee_masked_identifier: payeeMasked.trim() || undefined,
      method,
      note: note.trim() || undefined,
      synthetic_device_tag: syntheticDevice || undefined,
      synthetic_city_tag: syntheticCity || undefined,
      simulated_at: simulatedAt || undefined,
    };

    try {
      const res = await api.createPayment(payload, idempotencyKey);
      // Navigate to payment result screen
      navigate(`/payments/${res.id}/result`, { state: { payment: res } });
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      {/* Top Banner */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-xs">
        <span className="text-xs font-semibold text-teal-600 uppercase tracking-wider block mb-0.5">
          Pre-Payment Fraud Analysis
        </span>
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
          Send Payment
        </h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Every payment is evaluated in real time against 10 explainable risk rules before funds move.
        </p>
      </div>

      {/* Credential Notice Banner (§0.2, §11) */}
      <div className="bg-amber-50/80 border border-amber-200/90 rounded-xl p-4 flex items-start space-x-3">
        <Shield className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        <div className="text-xs text-amber-900 space-y-0.5">
          <p className="font-bold">PayGuard 360 will never ask for your PIN, OTP or password.</p>
          <p className="text-amber-800 text-[11px]">
            Never enter payment credentials in notes or descriptions. Standalone digits and card numbers are actively blocked.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 flex items-center space-x-2 animate-in fade-in">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          <span className="font-medium">{error}</span>
        </div>
      )}

      {/* Payment Form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200/80 shadow-xs p-6 space-y-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* Payee Display Name */}
          <div className="space-y-1 sm:col-span-2">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span>Payee / Beneficiary Name *</span>
              <span className="text-[10px] text-slate-400">e.g. Fresh Mart, Airtel Broadband</span>
            </label>
            <input
              type="text"
              required
              value={payeeName}
              onChange={(e) => setPayeeName(e.target.value)}
              placeholder="Enter merchant or recipient name"
              maxLength={60}
              className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
            />
          </div>

          {/* Payee Masked Identifier / UPI ID */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span>Payee Identifier / VPA</span>
              <span className="text-[10px] text-slate-400">e.g. ••••8891 or merchant@upi</span>
            </label>
            <input
              type="text"
              value={payeeMasked}
              onChange={(e) => setPayeeMasked(e.target.value)}
              placeholder="••••8891"
              maxLength={30}
              className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
            />
          </div>

          {/* Payment Method */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Payment Method</label>
            <select
              value={method}
              onChange={(e) => setMethod(e.target.value)}
              className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition bg-white"
            >
              <option value="upi">UPI (Instant Real-time)</option>
              <option value="netbanking">Net Banking (NEFT / IMPS)</option>
              <option value="card">Debit / Credit Card</option>
              <option value="wallet">Prepaid Wallet</option>
              <option value="collect_approval">UPI Collect Request Approval</option>
            </select>
          </div>

          {/* Amount in Rupees */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span>Amount (₹ Rupees) *</span>
              <span className="text-[10px] text-slate-400">Limit: ₹1 to ₹2,00,000</span>
            </label>
            <div className="relative">
              <span className="absolute left-3.5 top-2 text-xs font-semibold text-slate-400">₹</span>
              <input
                type="number"
                step="any"
                min="1"
                max="200000"
                required
                value={amountRupees}
                onChange={(e) => setAmountRupees(e.target.value)}
                placeholder="500"
                className="w-full pl-8 pr-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
              />
            </div>
            {parsedPaise > 0 && (
              <p className="text-[11px] font-medium text-teal-600">
                Paise equivalent: <span className="font-bold">{parsedPaise.toLocaleString('en-IN')} paise</span> ({formatPaise(parsedPaise)})
              </p>
            )}
          </div>

          {/* Category */}
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-700">Budget Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition bg-white"
            >
              <option value="General">General</option>
              <option value="Groceries">Groceries</option>
              <option value="Utilities">Utilities</option>
              <option value="Food & Dining">Food & Dining</option>
              <option value="Shopping">Shopping</option>
              <option value="Entertainment">Entertainment</option>
              <option value="Housing">Housing</option>
              <option value="Inventory">Inventory</option>
            </select>
          </div>

          {/* Note / Purpose */}
          <div className="space-y-1 sm:col-span-2">
            <label className="text-xs font-semibold text-slate-700 flex items-center justify-between">
              <span>Payment Note / Purpose</span>
              <span className="text-[10px] text-slate-400">Optional (max 140 chars)</span>
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="e.g. Dinner with team, Broadband bill"
              maxLength={140}
              className="w-full px-3.5 py-2 text-xs border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
            />
          </div>

          {/* Scheduled Time (Optional) */}
          {simulatedAt && (
            <div className="space-y-1 sm:col-span-2 bg-slate-50 p-3 rounded-lg border border-slate-200">
              <label className="text-xs font-semibold text-slate-700 flex items-center space-x-1.5">
                <Clock className="w-3.5 h-3.5 text-slate-500" />
                <span>Scheduled Execution Timestamp</span>
              </label>
              <input
                type="text"
                value={simulatedAt}
                onChange={(e) => setSimulatedAt(e.target.value)}
                className="w-full px-3 py-1.5 text-xs bg-white border border-slate-200 rounded font-mono text-slate-700"
              />
            </div>
          )}
        </div>

        {/* Before-You-Pay Safety Checklist (§14, §16) */}
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-teal-600" />
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
              Before-You-Pay Verification Checklist
            </h3>
          </div>
          <p className="text-[11px] text-slate-500">
            Please confirm all three safety points before initiating payment:
          </p>

          <div className="space-y-2">
            <button
              type="button"
              onClick={() => setCheckPayee(!checkPayee)}
              className="flex items-center space-x-2 text-left w-full group"
            >
              {checkPayee ? (
                <CheckSquare className="w-4 h-4 text-teal-600 shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-slate-400 shrink-0 group-hover:text-slate-600" />
              )}
              <span className="text-xs text-slate-700 group-hover:text-slate-900">
                I know this payee personally or have independently verified their official payment request.
              </span>
            </button>

            <button
              type="button"
              onClick={() => setCheckNoPressure(!checkNoPressure)}
              className="flex items-center space-x-2 text-left w-full group"
            >
              {checkNoPressure ? (
                <CheckSquare className="w-4 h-4 text-teal-600 shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-slate-400 shrink-0 group-hover:text-slate-600" />
              )}
              <span className="text-xs text-slate-700 group-hover:text-slate-900">
                No unknown person on a phone call or chat pressured me to make this payment or share an OTP.
              </span>
            </button>

            <button
              type="button"
              onClick={() => setCheckDetails(!checkDetails)}
              className="flex items-center space-x-2 text-left w-full group"
            >
              {checkDetails ? (
                <CheckSquare className="w-4 h-4 text-teal-600 shrink-0" />
              ) : (
                <Square className="w-4 h-4 text-slate-400 shrink-0 group-hover:text-slate-600" />
              )}
              <span className="text-xs text-slate-700 group-hover:text-slate-900">
                I have confirmed the payment amount and understand that money moves immediately.
              </span>
            </button>
          </div>
        </div>

        {/* Submit Button */}
        <div className="pt-2 flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="px-4 py-2 border border-slate-300 text-slate-600 hover:bg-slate-100 rounded-lg text-xs font-semibold transition"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={!isFormValid || loading}
            className={`inline-flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-bold shadow-xs transition ${
              isFormValid && !loading
                ? 'bg-teal-600 hover:bg-teal-700 text-white cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            <span>Analyze & Submit Payment</span>
          </button>
        </div>
      </form>
    </div>
  );
};
