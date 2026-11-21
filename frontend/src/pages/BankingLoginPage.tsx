import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Building2, ShieldCheck, UserCheck, AlertCircle, Lock, ArrowRight, User, Scale } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const BankingLoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [selectedRole, setSelectedRole] = useState<'officer' | 'manager'>('officer');
  const [username, setUsername] = useState('ananya_reviewer');
  const [password, setPassword] = useState('password123');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRoleTabChange = (role: 'officer' | 'manager') => {
    setSelectedRole(role);
    setError(null);
    if (role === 'officer') {
      setUsername('ananya_reviewer');
    } else {
      setUsername('vikram_supervisor');
    }
    setPassword('password123');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const loggedUser = await login(username, password);
      if (loggedUser.role === 'reviewer' || loggedUser.role === 'supervisor') {
        navigate('/review');
      } else {
        setError('Access Denied: Customer accounts are not authorized to access the Banking Operations Portal.');
      }
    } catch (err: any) {
      setError(err?.message || 'Authentication failed. Please verify bank officer credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[calc(100vh-80px)] flex flex-col justify-center py-12 px-4 sm:px-6 lg:px-8 bg-slate-900">
      {/* Primary Portal Navigation Tabs */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md mb-6">
        <div className="flex rounded-xl bg-slate-800 p-1 border border-slate-700 shadow-sm">
          <Link
            to="/login/customer"
            className="flex-1 py-2 text-center text-xs font-medium text-slate-400 hover:text-white transition flex items-center justify-center space-x-1.5"
          >
            <User className="w-3.5 h-3.5" />
            <span>Customer Portal</span>
          </Link>
          <Link
            to="/login/banking"
            className="flex-1 py-2 text-center text-xs font-semibold rounded-lg bg-indigo-600 text-white shadow-xs flex items-center justify-center space-x-1.5 transition"
          >
            <Building2 className="w-3.5 h-3.5" />
            <span>Banking Portal</span>
          </Link>
        </div>
      </div>

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 shadow-sm mb-3">
          <Building2 className="w-8 h-8" />
        </div>
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Banking Operations Portal
        </h2>
        <p className="mt-1 text-xs text-slate-400">
          Official Bank Staff & Risk Authority • Transaction Clearance, Ledger Holds & Compliance
        </p>
      </div>

      <div className="mt-6 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-slate-800/90 py-8 px-6 sm:px-8 shadow-2xl rounded-2xl border border-slate-700/80">
          {/* Sub-role selector: Bank Officer vs Branch Manager */}
          <div className="grid grid-cols-2 gap-2 p-1 bg-slate-900 rounded-lg border border-slate-700/60 mb-5">
            <button
              type="button"
              onClick={() => handleRoleTabChange('officer')}
              className={`py-1.5 px-3 rounded-md text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                selectedRole === 'officer'
                  ? 'bg-amber-500 text-slate-950 shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <UserCheck className="w-3.5 h-3.5" />
              <span>Bank Officer</span>
            </button>
            <button
              type="button"
              onClick={() => handleRoleTabChange('manager')}
              className={`py-1.5 px-3 rounded-md text-xs font-semibold transition flex items-center justify-center space-x-1.5 ${
                selectedRole === 'manager'
                  ? 'bg-purple-600 text-white shadow-xs'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              <span>Branch Manager</span>
            </button>
          </div>

          {error && (
            <div className="mb-4 bg-rose-950/80 border border-rose-800 text-rose-200 text-xs p-3 rounded-lg flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                {selectedRole === 'officer' ? 'Bank Officer ID / Username' : 'Branch Manager / Supervisor ID'}
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
                  <User className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder={selectedRole === 'officer' ? 'ananya_reviewer' : 'vikram_supervisor'}
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Bank Security Key / Password
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
                  className="w-full text-xs pl-9 pr-3 py-2.5 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition"
                  required
                />
              </div>
            </div>

            <div className="flex items-center justify-between text-xs pt-1">
              <span className="text-[11px] text-slate-400 flex items-center">
                <span className="w-2 h-2 rounded-full bg-emerald-400 mr-1.5 animate-pulse" />
                {selectedRole === 'officer' ? 'Transaction Clearance Level 1' : 'Executive Authority Level 2'}
              </span>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold py-2.5 px-4 rounded-lg transition shadow-md hover:shadow-lg flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'Authenticating Bank Staff...' : `Sign In as ${selectedRole === 'officer' ? 'Bank Officer' : 'Branch Manager'}`}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </form>

          <div className="mt-6 pt-5 border-t border-slate-700/80 text-center text-[11px]">
            <Link to="/login/customer" className="text-slate-400 hover:text-white transition flex items-center justify-center space-x-1">
              <span>← Looking for personal or business accounts? Switch to Customer Portal</span>
            </Link>
          </div>
        </div>

        {/* Security watermark */}
        <div className="mt-4 flex items-center justify-center space-x-1.5 text-[11px] text-slate-500">
          <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
          <span>Official Bank Portal • Actions logged to immutable SQLite compliance audit triggers.</span>
        </div>
      </div>
    </div>
  );
};
