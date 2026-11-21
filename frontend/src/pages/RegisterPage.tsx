import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AlertCircle, ArrowRight, Lock, ShieldCheck, User } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const RegisterPage: React.FC = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [sandboxBalance, setSandboxBalance] = useState('50000');
  const [profileType, setProfileType] = useState<'personal' | 'business'>('personal');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < 8) {
      setError('Use a password with at least 8 characters.');
      return;
    }
    if (password !== confirmPassword) {
      setError('The passwords do not match.');
      return;
    }
    const cleanBalance = sandboxBalance.trim().replace(/,/g, '');
    if (!/^\d+(\.\d{1,2})?$/.test(cleanBalance)) {
      setError('Enter a valid sandbox balance with up to two decimal places.');
      return;
    }
    const sandboxBalancePaise = Math.round(Number(cleanBalance) * 100);
    if (!Number.isSafeInteger(sandboxBalancePaise) || sandboxBalancePaise > 1000000000) {
      setError('The sandbox starting balance must be between ₹0 and ₹1,00,00,000.');
      return;
    }
    setLoading(true);
    try {
      await register(username.trim(), password, profileType, sandboxBalancePaise);
      navigate('/accounts', { replace: true });
    } catch (err: any) {
      setError(err?.message || 'Could not create your account. Please try another username.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-10 px-4 sm:px-6 lg:px-8 bg-slate-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-500/10 text-teal-700 border border-teal-500/20 mb-3"><ShieldCheck className="w-8 h-8" /></div>
        <h1 className="text-2xl font-extrabold tracking-tight text-slate-900">Create your customer account</h1>
        <p className="mt-1 text-sm text-slate-500">Choose a username and password to start tracking your finances.</p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white p-6 sm:p-8 shadow-sm rounded-2xl border border-slate-200">
          {error && <div role="alert" className="mb-4 bg-rose-50 border border-rose-200 text-rose-800 text-sm p-3 rounded-lg flex items-center gap-2"><AlertCircle className="w-4 h-4 shrink-0" /><span>{error}</span></div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <label className="block text-sm font-semibold text-slate-700">Username / ID
              <span className="relative block mt-1"><User className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" /><input autoComplete="username" autoCapitalize="none" minLength={3} maxLength={50} required value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Choose a username" className="w-full text-sm pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500" /></span>
            </label>
            <label className="block text-sm font-semibold text-slate-700">Account type
              <select value={profileType} onChange={(e) => setProfileType(e.target.value as 'personal' | 'business')} className="mt-1 w-full text-sm px-3 py-2.5 border border-slate-300 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-teal-500"><option value="personal">Personal</option><option value="business">Business</option></select>
            </label>
            <label className="block text-sm font-semibold text-slate-700">Sandbox payment starting balance (₹)
              <input inputMode="decimal" type="number" min="0" max="10000000" step="0.01" required value={sandboxBalance} onChange={(e) => setSandboxBalance(e.target.value)} className="mt-1 w-full text-sm px-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500" />
              <span className="mt-1 block text-xs font-normal text-slate-500">This is simulated test balance for trying payment review. It is separate from your manually reported bank balance.</span>
            </label>
            <label className="block text-sm font-semibold text-slate-700">Password
              <span className="relative block mt-1"><Lock className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" /><input autoComplete="new-password" type="password" minLength={8} maxLength={100} required value={password} onChange={(e) => setPassword(e.target.value)} className="w-full text-sm pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500" /></span>
              <span className="mt-1 block text-xs font-normal text-slate-500">At least 8 characters.</span>
            </label>
            <label className="block text-sm font-semibold text-slate-700">Confirm password
              <input autoComplete="new-password" type="password" minLength={8} maxLength={100} required value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="mt-1 w-full text-sm px-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500" />
            </label>
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-3 text-xs text-amber-900">The sandbox balance is fictitious and only supports the demo payment flow. Your manually reported bank account and balance are entered separately on the next page.</div>
            <button type="submit" disabled={loading} className="w-full bg-teal-700 hover:bg-teal-800 text-white text-sm font-semibold py-2.5 px-4 rounded-lg transition flex items-center justify-center gap-2 disabled:opacity-50"><span>{loading ? 'Creating account…' : 'Create account'}</span><ArrowRight className="w-4 h-4" /></button>
          </form>
          <p className="mt-5 pt-4 border-t border-slate-100 text-center text-sm text-slate-500">Already have an account? <Link to="/login/customer" className="font-semibold text-teal-700 hover:underline">Sign in</Link></p>
        </div>
        <p className="mt-4 text-center text-xs text-slate-500">Never enter your bank password, UPI PIN, OTP, CVV, or full card number here.</p>
      </div>
    </div>
  );
};
