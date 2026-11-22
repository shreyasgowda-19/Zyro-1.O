import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, User, AlertCircle, Lock, ArrowRight, ShieldAlert, Building2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const CustomerLoginPage: React.FC = () => {
  const { login, logout } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const loggedUser = await login(username, password);
      if (loggedUser.role === 'customer') {
        navigate('/dashboard');
      } else {
        // Do not leave a staff session active on the customer sign-in page.
        logout();
        setError(`This is a ${loggedUser.role} account. Redirecting to the Banking Portal...`);
        setTimeout(() => navigate('/login/banking'), 1200);
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-50">
      {/* Primary Portal Navigation Tabs */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <div className="flex rounded-xl bg-slate-200/80 p-1 border border-slate-300/80 shadow-2xs">
          <Link
            to="/login/customer"
            className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-white text-teal-700 shadow-xs flex items-center justify-center space-x-1.5 transition"
          >
            <User className="w-3.5 h-3.5" />
            <span>Customer Portal</span>
          </Link>
          <Link
            to="/login/banking"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-600 hover:text-slate-900 transition flex items-center justify-center space-x-1.5"
          >
            <Building2 className="w-3.5 h-3.5 text-indigo-600" />
            <span>Banking Portal</span>
          </Link>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-teal-500/10 text-teal-600 border border-teal-500/20 shadow-sm mb-3">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">
          Customer Banking Portal
        </h2>
        <p className="mt-1 text-xs text-slate-500">
          Sign in to manage payments, monitor safety scores, and track budgets
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-6 sm:px-8 shadow-sm rounded-2xl border border-slate-200/80">
          {error && (
            <div className="mb-4 bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Customer Username / ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full text-xs pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full text-xs pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center text-slate-600 cursor-pointer">
                <input type="checkbox" defaultChecked className="rounded border-slate-300 text-teal-600 focus:ring-teal-500 mr-2" />
                Remember Customer ID
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-teal-600 hover:bg-teal-700 text-white text-xs font-semibold py-2.5 px-4 rounded-lg transition shadow-sm hover:shadow flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating...' : 'Sign In to Customer Account'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-100 text-center space-y-2">
            <p className="text-[11px] text-slate-500">
              New here?{' '}
              <Link to="/register" className="font-semibold text-teal-700 hover:underline">Create a customer account</Link>
            </p>
            <p className="text-[11px] text-slate-500">
              Bank Officer or Branch Manager?{' '}
              <Link to="/login/banking" className="font-semibold text-indigo-600 hover:underline">
                Banking Operations Portal →
              </Link>
            </p>
          </div>
        </div>

        {/* Security Assurance Footer */}
        <div className="mt-4 flex items-center justify-center space-x-1.5 text-[11px] text-slate-500">
          <ShieldAlert className="w-3.5 h-3.5 text-teal-600" />
          <span>FinShield will never ask for your PIN, OTP, or CVV.</span>
        </div>
      </div>
    </div>
  );
};
