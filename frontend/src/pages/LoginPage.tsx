import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, User, Building, UserCheck, AlertCircle, ArrowRight, ShieldAlert } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('rahul_personal');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const demoAccounts = [
    {
      username: 'rahul_personal',
      name: 'Rahul Sharma',
      role: 'Personal Customer',
      desc: 'Salaried individual, ₹50,000 opening balance, 90-day history',
      icon: User,
      color: 'border-blue-500/30 bg-blue-500/5 hover:border-blue-500',
    },
    {
      username: 'priya_personal',
      name: 'Priya Patel',
      role: 'Personal Customer',
      desc: 'Frequent transactor, ₹75,000 balance, held investment case',
      icon: User,
      color: 'border-indigo-500/30 bg-indigo-500/5 hover:border-indigo-500',
    },
    {
      username: 'sharma_kirana',
      name: 'Sharma Kirana Store',
      role: 'Business Customer',
      desc: 'Retailer, ₹2,00,000 balance, supplier payments, escalated case',
      icon: Building,
      color: 'border-emerald-500/30 bg-emerald-500/5 hover:border-emerald-500',
    },
    {
      username: 'techcraft_solutions',
      name: 'TechCraft Solutions',
      role: 'Business Customer',
      desc: 'IT agency, ₹5,00,000 balance, high velocity thresholds',
      icon: Building,
      color: 'border-teal-500/30 bg-teal-500/5 hover:border-teal-500',
    },
    {
      username: 'ananya_reviewer',
      name: 'Ananya Iyer',
      role: 'Fraud Reviewer',
      desc: 'Fraud team member, acts on held payments, mandatory notes',
      icon: UserCheck,
      color: 'border-amber-500/30 bg-amber-500/5 hover:border-amber-500',
    },
    {
      username: 'vikram_supervisor',
      name: 'Vikram Malhotra',
      role: 'Review Supervisor',
      desc: 'Senior risk officer, resolves escalated cases (two-person rule)',
      icon: ShieldCheck,
      color: 'border-purple-500/30 bg-purple-500/5 hover:border-purple-500',
    },
  ];

  const handleQuickLogin = async (uname: string) => {
    setError(null);
    setLoading(true);
    try {
      await login(uname, 'password123');
      if (uname.includes('reviewer') || uname.includes('supervisor')) {
        navigate('/review');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err?.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    handleQuickLogin(username);
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-10 sm:px-6 lg:px-8 bg-slate-50">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-xl bg-teal-500/10 text-teal-600 border border-teal-500/20 shadow-sm mb-3">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Sign in to PayGuard 360
        </h2>
        <p className="mt-1 text-sm text-slate-500">
          Fraud-first financial safety platform for India (Prototype)
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-2xl px-4 sm:px-0">
        <div className="bg-amber-50 border border-amber-200/80 rounded-lg p-3.5 mb-6 flex items-start space-x-3 text-amber-900">
          <ShieldAlert className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-xs">
            <span className="font-semibold block text-amber-950">Security Notice:</span>
            PayGuard 360 will never ask for your PIN, OTP, CVV or password. All transactions in this demo are simulated with synthetic data.
          </div>
        </div>

        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-lg mb-6 flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm mb-6">
          <h3 className="text-sm font-semibold text-slate-800 mb-1 flex items-center justify-between">
            <span>One-Click Seeded Demo Accounts</span>
            <span className="text-[11px] font-normal text-slate-500">Password: password123</span>
          </h3>
          <p className="text-xs text-slate-500 mb-4">
            Select any persona below to log in immediately with realistic Indian transaction history.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {demoAccounts.map((acc) => {
              const Icon = acc.icon;
              return (
                <button
                  key={acc.username}
                  onClick={() => handleQuickLogin(acc.username)}
                  disabled={loading}
                  className={`p-3.5 rounded-lg border text-left transition flex items-start space-x-3 group ${acc.color}`}
                >
                  <div className="p-2 rounded-md bg-white border border-slate-200/70 shadow-2xs group-hover:scale-105 transition">
                    <Icon className="w-4 h-4 text-slate-700" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-900 truncate">{acc.name}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400 group-hover:translate-x-0.5 transition" />
                    </div>
                    <span className="text-[10px] font-medium text-teal-700 block">{acc.role}</span>
                    <span className="text-[11px] text-slate-500 block truncate mt-0.5">{acc.desc}</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        <div className="bg-white p-6 rounded-xl border border-slate-200/80 shadow-sm">
          <h3 className="text-sm font-semibold text-slate-800 mb-4">Or sign in manually</h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-500"
                required
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full text-xs px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-1 focus:ring-teal-500"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold py-2 px-4 rounded-md transition shadow-xs flex items-center justify-center space-x-1.5"
            >
              <span>{loading ? 'Signing in...' : 'Sign In'}</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};
