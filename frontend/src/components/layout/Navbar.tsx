import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { ShieldCheck, LogOut, LayoutDashboard, Send, History, PieChart, BookOpen, Globe } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { useLanguage } from '../../contexts/LanguageContext';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const { language, setLanguage, t } = useLanguage();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login/customer');
  };

  const isCustomer = user?.role === 'customer';
  const isReviewer = user?.role === 'reviewer' || user?.role === 'supervisor';

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
                <span className="block text-[10px] text-slate-400 tracking-wider uppercase font-medium">
                  {isReviewer ? 'Banking Operations Portal' : 'Customer Banking Portal'}
                </span>
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
                        location.pathname === '/dashboard' ? 'bg-slate-800 text-teal-400 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
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
                        location.pathname === '/budgets' ? 'bg-slate-800 text-teal-400 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <PieChart className="w-4 h-4" />
                      <span>{t('nav.budgets')}</span>
                    </Link>
                    <Link
                      to="/learn"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/learn' ? 'bg-slate-800 text-teal-400 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
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
                        location.pathname === '/review' ? 'bg-slate-800 text-amber-400 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
                      }`}
                    >
                      <ShieldCheck className="w-4 h-4" />
                      <span>Clearance Queue</span>
                    </Link>
                    <Link
                      to="/review/audit"
                      className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition ${
                        location.pathname === '/review/audit' ? 'bg-slate-800 text-amber-400 font-semibold' : 'text-slate-300 hover:text-white hover:bg-slate-800/60'
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

          {/* Right Controls: Language & Authenticated User Profile */}
          <div className="flex items-center space-x-3">
            {/* Language Switcher */}
            <button
              type="button"
              onClick={() => setLanguage(language === 'en' ? 'hi' : 'en')}
              className="flex items-center space-x-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-200 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition"
              title="Switch Language / भाषा बदलें"
            >
              <Globe className="w-3.5 h-3.5 text-teal-400" />
              <span>{language === 'en' ? 'हिंदी' : 'English'}</span>
            </button>

            {user ? (
              <div className="flex items-center space-x-2.5">
                <div className="bg-slate-800/90 border border-slate-700/80 px-3 py-1.5 rounded-lg flex items-center space-x-2">
                  <span className={`w-2 h-2 rounded-full ${isReviewer ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400'}`} />
                  <div>
                    <div className="text-xs font-semibold text-white leading-tight">{user.username}</div>
                    <div className="text-[10px] text-teal-400 font-medium capitalize leading-tight">
                      {user.role} {user.profile_type ? `• ${user.profile_type}` : ''}
                    </div>
                  </div>
                </div>

                <button
                  onClick={handleLogout}
                  className="p-2 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <Link
                to="/login/customer"
                className="bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold px-3.5 py-1.5 rounded-lg text-xs transition shadow-xs"
              >
                Sign In
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
