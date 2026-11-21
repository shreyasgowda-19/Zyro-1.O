import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, LogOut, ArrowRightLeft, LayoutDashboard, Send, History, PieChart, BookOpen, Sparkles, Globe } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';
import { DemoSimulatorModal } from '../common/DemoSimulatorModal';

export const Navbar: React.FC = () => {
  const { user, logout, switchAccount } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();
  const [isSimulatorOpen, setIsSimulatorOpen] = useState<boolean>(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const isCustomer = user?.role === 'customer';
  const isReviewer = user?.role === 'reviewer' || user?.role === 'supervisor';

  const demoAccounts = [
    { label: 'Rahul (Personal Customer)', username: 'rahul_personal' },
    { label: 'Priya (Personal Customer)', username: 'priya_personal' },
    { label: 'Sharma Kirana (Business Customer)', username: 'sharma_kirana' },
    { label: 'TechCraft (Business Customer)', username: 'techcraft_solutions' },
    { label: 'Ananya (Reviewer)', username: 'ananya_reviewer' },
    { label: 'Vikram (Supervisor)', username: 'vikram_supervisor' },
  ];

  return (
    <header className="bg-slate-900 text-white shadow-md border-b border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3">
            <Link to={isReviewer ? "/review" : "/dashboard"} className="flex items-center space-x-2.5 group">
              <div className="w-10 h-10 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400 group-hover:bg-teal-500/20 transition">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
                  PayGuard <span className="text-teal-400 font-extrabold">360</span>
                </span>
                <span className="block text-[10px] text-slate-400 tracking-wider uppercase font-medium">Financial Safety India</span>
              </div>
            </Link>

            {/* Navigation links */}
            {user && (
              <nav className="hidden md:flex items-center space-x-1 ml-6">
                {isCustomer && (
                  <>
                    <Link
                      to="/dashboard"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/dashboard' ? 'bg-slate-800 text-teal-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <LayoutDashboard className="w-4 h-4" />
                      <span>{t('nav.dashboard')}</span>
                    </Link>
                    <Link
                      to="/pay"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/pay' ? 'bg-teal-500 text-slate-950 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <Send className="w-4 h-4" />
                      <span>{t('nav.pay')}</span>
                    </Link>
                    <Link
                      to="/budgets"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/budgets' ? 'bg-slate-800 text-teal-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <PieChart className="w-4 h-4" />
                      <span>{t('nav.budgets')}</span>
                    </Link>
                    <Link
                      to="/learn"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/learn' ? 'bg-slate-800 text-teal-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <BookOpen className="w-4 h-4" />
                      <span>{t('nav.learn')}</span>
                    </Link>
                  </>
                )}

                {isReviewer && (
                  <>
                    <Link
                      to="/review"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/review' ? 'bg-slate-800 text-teal-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>Review Queue</span>
                    </Link>
                    <Link
                      to="/review/audit"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/review/audit' ? 'bg-slate-800 text-teal-400' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <History className="w-4 h-4" />
                      <span>Audit Trail</span>
                    </Link>
                  </>
                )}
              </nav>
            )}
          </div>

          {/* Right Controls: Quick Switcher & User Profile */}
          <div className="flex items-center space-x-2.5">
            {/* Language Switcher */}
            <button
              type="button"
              onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
              className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-2.5 py-1 rounded text-xs font-semibold transition min-h-[36px]"
              title="Switch Language / भाषा बदलें"
            >
              <Globe className="w-3.5 h-3.5 text-teal-400" />
              <span>{language === 'en' ? 'हिंदी' : 'English'}</span>
            </button>

            {user ? (
              <>
                <button
                  type="button"
                  onClick={() => setIsSimulatorOpen(true)}
                  className="hidden sm:inline-flex items-center space-x-1.5 bg-indigo-950/80 hover:bg-indigo-900 border border-indigo-700/60 text-indigo-300 px-2.5 py-1 rounded text-xs font-semibold transition"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  <span>{t('nav.simulator')}</span>
                </button>

                <div className="hidden sm:flex items-center space-x-1.5 bg-slate-800/80 px-2 py-1 rounded border border-slate-700 text-xs">
                  <ArrowRightLeft className="w-3.5 h-3.5 text-slate-400" />
                  <select
                    value={user.username}
                    onChange={(e) => switchAccount(e.target.value)}
                    className="bg-transparent text-slate-200 text-xs focus:outline-none cursor-pointer"
                    title="Switch Demo Role & Account"
                  >
                    {demoAccounts.map((acc) => (
                      <option key={acc.username} value={acc.username} className="bg-slate-900 text-white">
                        {acc.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center space-x-2 text-right">
                  <div>
                    <div className="text-xs font-semibold text-white">{user.username}</div>
                    <div className="text-[10px] text-teal-400 font-medium capitalize">
                      {user.role} {user.profile_type ? `(${user.profile_type})` : ''}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded transition"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            ) : (
              <Link
                to="/login"
                className="bg-teal-500 hover:bg-teal-600 text-slate-950 font-semibold px-3 py-1.5 rounded text-xs transition"
              >
                Demo Login
              </Link>
            )}
          </div>
        </div>
      </div>
      <DemoSimulatorModal
        isOpen={isSimulatorOpen}
        onClose={() => setIsSimulatorOpen(false)}
      />
    </header>
  );
};
