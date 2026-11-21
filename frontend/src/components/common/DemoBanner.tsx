import React, { useState } from 'react';
import { AlertTriangle, ShieldAlert, RefreshCw, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';
import { useLanguage } from '../../contexts/LanguageContext';

export const DemoBanner: React.FC = () => {
  const { t } = useLanguage();
  const [resetting, setResetting] = useState(false);
  const [resetSuccess, setResetSuccess] = useState(false);

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset the demo database? All newly submitted transactions and review actions will be restored to the seeded state.")) {
      return;
    }
    setResetting(true);
    setResetSuccess(false);
    try {
      await api.resetDemo();
      setResetSuccess(true);
      setTimeout(() => {
        window.location.reload();
      }, 800);
    } catch (err) {
      alert("Failed to reset demo: " + (err as Error).message);
    } finally {
      setResetting(false);
    }
  };

  return (
    <div className="bg-amber-500 text-navy-950 px-4 py-2 text-xs md:text-sm font-semibold shadow-sm border-b border-amber-600 flex flex-wrap items-center justify-between gap-2">
      <div className="flex items-center space-x-2">
        <AlertTriangle className="w-4 h-4 shrink-0 text-navy-950" />
        <span className="tracking-wide uppercase font-bold">{t('app.demo_mode')}</span>
        <span className="hidden md:inline text-amber-950">• Synthetic Data Prototype</span>
      </div>

      <div className="flex items-center space-x-4">
        <div className="hidden lg:flex items-center space-x-1.5 text-navy-900 bg-amber-400/80 px-2.5 py-0.5 rounded-full text-xs font-medium border border-amber-600/30">
          <ShieldAlert className="w-3.5 h-3.5 text-navy-950" />
          <span>{t('app.credential_warning')}</span>
        </div>

        <button
          onClick={handleReset}
          disabled={resetting}
          className="flex items-center space-x-1.5 bg-navy-900 hover:bg-navy-950 text-white px-2.5 py-1 rounded text-xs transition font-medium shadow-sm disabled:opacity-50"
          title="Reset simulated transactions and accounts to default seed state (< 5s)"
        >
          {resetSuccess ? (
            <>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              <span>Reset Done!</span>
            </>
          ) : (
            <>
              <RefreshCw className={`w-3.5 h-3.5 ${resetting ? 'animate-spin' : ''}`} />
              <span>{resetting ? 'Resetting...' : 'Reset Demo'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
