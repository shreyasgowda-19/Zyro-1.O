import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldAlert, UserCheck, AlertCircle, Lock, ArrowRight, User, Sparkles } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const ReviewerLoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('ananya_reviewer');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [showDemoHints, setShowDemoHints] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const loggedUser = await login(username, password);
      if (loggedUser.role === 'reviewer' || loggedUser.role === 'supervisor') {
        navigate('/review');
      } else {
        setError('Access Denied: Customer accounts are not authorized to access the Fraud Review Console.');
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify staff credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-900">
      {/* Role Portal Navigation Tabs */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <div className="flex rounded-lg bg-slate-800 p-1 border border-slate-700 shadow-2xs">
          <Link
            to="/login/customer"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5"
          >
            <span>Customer Portal</span>
          </Link>
          <Link
            to="/login/reviewer"
            className="flex-1 py-2 text-center text-xs font-semibold rounded-md bg-amber-500 text-slate-950 shadow-xs flex items-center justify-center space-x-1.5 transition"
          >
            <UserCheck className="w-3.5 h-3.5" />
            <span>Fraud Reviewer</span>
          </Link>
          <Link
            to="/login/supervisor"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5"
          >
            <span>Supervisor</span>
          </Link>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500/10 text-amber-400 border border-amber-500/30 shadow-sm mb-3">
          <UserCheck className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Fraud Operations Console
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Authorized fraud analysts only • Tier-1 held transaction review & escalation
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800/90 py-8 px-6 sm:px-8 shadow-xl rounded-2xl border border-slate-700">
          {error && (
            <div className="mb-4 bg-rose-950/80 border border-rose-800 text-rose-200 text-xs p-3 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Analyst ID / Staff Username
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. ananya_reviewer"
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Security Passphrase
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-[11px] text-slate-400 flex items-center">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                Audit Trail Active
              </span>
              <button
                type="button"
                onClick={() => setShowDemoHints(!showDemoHints)}
                className="text-amber-400 hover:text-amber-300 font-medium flex items-center space-x-1"
              >
                <Sparkles className="w-3 h-3 text-amber-400" />
                <span>{showDemoHints ? 'Hide Hints' : 'Reviewer Credential'}</span>
              </button>
            </div>

            {showDemoHints && (
              <div className="bg-slate-900/80 border border-slate-700 rounded-lg p-3 text-[11px] text-slate-300 space-y-1.5">
                <div className="font-semibold text-amber-400">Reviewer Credentials:</div>
                <button
                  type="button"
                  onClick={() => { setUsername('ananya_reviewer'); setPassword('password123'); }}
                  className="w-full text-left px-2.5 py-1.5 bg-slate-800 border border-slate-700 rounded hover:bg-slate-700 text-amber-300 flex items-center justify-between"
                >
                  <span>ananya_reviewer</span>
                  <span className="text-[10px] text-slate-400">Click to fill</span>
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-amber-500 hover:bg-amber-400 text-slate-950 text-xs font-bold py-2.5 px-4 rounded-lg transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating Staff...' : 'Sign In to Review Console'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-700/80 flex items-center justify-between text-[11px]">
            <Link to="/login/customer" className="text-slate-400 hover:text-white transition">
              ← Customer Portal
            </Link>
            <Link to="/login/supervisor" className="text-purple-400 hover:text-purple-300 font-medium transition">
              Supervisor Portal →
            </Link>
          </div>
        </div>

        {/* Security watermark */}
        <div className="mt-4 flex items-center justify-center space-x-1.5 text-[11px] text-slate-500">
          <ShieldAlert className="w-3.5 h-3.5 text-amber-500" />
          <span>Internal Use Only • Actions logged to immutable SQLite audit triggers.</span>
        </div>
      </div>
    </div>
  );
};
