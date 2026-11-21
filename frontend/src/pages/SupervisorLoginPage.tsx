import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, Scale, AlertCircle, Lock, ArrowRight, User, Sparkles, Award } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const SupervisorLoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState('vikram_supervisor');
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
      if (loggedUser.role === 'supervisor') {
        navigate('/review');
      } else {
        setError('Access Denied: Requires Senior Risk Officer (Supervisor) role authorization.');
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify supervisor credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-950">
      {/* Role Portal Navigation Tabs */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <div className="flex rounded-lg bg-slate-900 p-1 border border-slate-800 shadow-2xs">
          <Link
            to="/login/customer"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5"
          >
            <span>Customer Portal</span>
          </Link>
          <Link
            to="/login/reviewer"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5"
          >
            <span>Fraud Reviewer</span>
          </Link>
          <Link
            to="/login/supervisor"
            className="flex-1 py-2 text-center text-xs font-semibold rounded-md bg-purple-600 text-white shadow-xs flex items-center justify-center space-x-1.5 transition"
          >
            <ShieldCheck className="w-3.5 h-3.5 text-purple-200" />
            <span>Supervisor</span>
          </Link>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-purple-500/10 text-purple-400 border border-purple-500/30 shadow-sm mb-3">
          <Scale className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Risk & Compliance Authority
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Executive oversight • Two-person rule escalation resolution & compliance controls
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-900/90 py-8 px-6 sm:px-8 shadow-2xl rounded-2xl border border-purple-900/40">
          {error && (
            <div className="mb-4 bg-rose-950/80 border border-rose-800 text-rose-200 text-xs p-3 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Supervisor Officer ID
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="e.g. vikram_supervisor"
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Executive Security Key / Password
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
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-950 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-[11px] text-purple-300 flex items-center">
                <Award className="w-3.5 h-3.5 text-purple-400 mr-1" />
                Senior Authority Level 2
              </span>
              <button
                type="button"
                onClick={() => setShowDemoHints(!showDemoHints)}
                className="text-purple-400 hover:text-purple-300 font-medium flex items-center space-x-1"
              >
                <Sparkles className="w-3 h-3 text-purple-400" />
                <span>{showDemoHints ? 'Hide Hints' : 'Supervisor Credential'}</span>
              </button>
            </div>

            {showDemoHints && (
              <div className="bg-slate-950 border border-purple-900/50 rounded-lg p-3 text-[11px] text-slate-300 space-y-1.5">
                <div className="font-semibold text-purple-300">Supervisor Credentials:</div>
                <button
                  type="button"
                  onClick={() => { setUsername('vikram_supervisor'); setPassword('password123'); }}
                  className="w-full text-left px-2.5 py-1.5 bg-slate-900 border border-purple-900/60 rounded hover:bg-slate-800 text-purple-200 flex items-center justify-between"
                >
                  <span>vikram_supervisor</span>
                  <span className="text-[10px] text-slate-400">Click to fill</span>
                </button>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-purple-600 hover:bg-purple-500 text-white text-xs font-bold py-2.5 px-4 rounded-lg transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Verifying Executive Credentials...' : 'Authenticate as Supervisor'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-800 flex items-center justify-between text-[11px]">
            <Link to="/login/customer" className="text-slate-400 hover:text-white transition">
              ← Customer Portal
            </Link>
            <Link to="/login/reviewer" className="text-amber-400 hover:text-amber-300 font-medium transition">
              ← Fraud Reviewer Console
            </Link>
          </div>
        </div>

        {/* Legal / Two-person rule watermark */}
        <div className="mt-4 flex items-center justify-center space-x-1.5 text-[11px] text-slate-500">
          <Scale className="w-3.5 h-3.5 text-purple-400" />
          <span>Strict Separation of Duties: Escalator cannot self-resolve escalations.</span>
        </div>
      </div>
    </div>
  );
};
