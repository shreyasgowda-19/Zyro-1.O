import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  HelpCircle, 
  PhoneCall, 
  ExternalLink, 
  AlertTriangle, 
  CheckCircle2, 
  Search, 
  Lock, 
  CheckSquare, 
  Info,
  Loader2,
  RefreshCw
} from 'lucide-react';
import { api, getErrorMessage } from '../services/api';
import type { GuidanceItem, ScamCheckResult } from '../types';
import { useLanguage } from '../contexts/LanguageContext';

export const LearnPage: React.FC = () => {
  const { language, t } = useLanguage();
  const [guidanceItems, setGuidanceItems] = useState<GuidanceItem[]>([]);
  const [loadingGuidance, setLoadingGuidance] = useState<boolean>(true);
  const [guidanceError, setGuidanceError] = useState<string | null>(null);

  // Scam Checker State
  const [scamInput, setScamInput] = useState<string>('');
  const [checkingScam, setCheckingScam] = useState<boolean>(false);
  const [scamResult, setScamResult] = useState<ScamCheckResult | null>(null);
  const [scamError, setScamError] = useState<string | null>(null);

  // Checklist State
  const [checkedItems, setCheckedItems] = useState<Record<number, boolean>>({
    1: false,
    2: false,
    3: false,
    4: false,
    5: false,
  });

  useEffect(() => {
    fetchGuidance();
  }, [language]);

  const fetchGuidance = async () => {
    setLoadingGuidance(true);
    setGuidanceError(null);
    try {
      const data = await api.getGuidance(language);
      setGuidanceItems(data);
    } catch (err: any) {
      setGuidanceError(getErrorMessage(err));
    } finally {
      setLoadingGuidance(false);
    }
  };

  const handleScamCheck = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!scamInput.trim()) return;

    setCheckingScam(true);
    setScamError(null);
    setScamResult(null);

    try {
      const result = await api.checkScamMessage(scamInput.trim());
      setScamResult(result);
    } catch (err: any) {
      setScamError(getErrorMessage(err));
    } finally {
      setCheckingScam(false);
    }
  };

  const toggleChecklist = (id: number) => {
    setCheckedItems((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const checklistPoints = [
    { id: 1, text: t('pay.checklist_1') },
    { id: 2, text: t('pay.checklist_2') },
    { id: 3, text: t('pay.checklist_3') },
    { id: 4, text: t('pay.checklist_4') },
    { id: 5, text: t('pay.checklist_5') },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div>
        <div className="flex items-center space-x-3 mb-2">
          <div className="w-10 h-10 rounded-lg bg-teal-500/10 border border-teal-500/30 flex items-center justify-center text-teal-400">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">{t('learn.title')}</h1>
            <p className="text-sm text-slate-400">{t('learn.subtitle')}</p>
          </div>
        </div>
      </div>

      {/* Credential Safety Notice */}
      <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start space-x-3">
        <Lock className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
        <div>
          <h4 className="text-sm font-semibold text-amber-200">
            {t('app.credential_warning')}
          </h4>
          <p className="text-xs text-amber-300/80 mt-0.5">
            Real banks, merchants, and authorities will never ask you to disclose your UPI PIN, ATM PIN, OTP, or passwords.
          </p>
        </div>
      </div>

      {/* Grid: Scam Checker (Left) and Checklist (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Scam-Message Checker */}
        <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Search className="w-5 h-5 text-teal-400" />
                <h2 className="text-base font-semibold text-white">{t('learn.scam_checker_title')}</h2>
              </div>
              <span className="text-[11px] bg-teal-500/10 text-teal-300 border border-teal-500/30 px-2 py-0.5 rounded font-mono">
                No ML • Zero Retention
              </span>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              {t('learn.scam_checker_subtitle')}
            </p>

            <form onSubmit={handleScamCheck} className="space-y-4">
              <div>
                <textarea
                  value={scamInput}
                  onChange={(e) => setScamInput(e.target.value)}
                  maxLength={1000}
                  rows={4}
                  placeholder={t('learn.scam_checker_placeholder')}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-teal-500"
                />
                <div className="flex justify-between items-center text-[11px] text-slate-500 mt-1">
                  <span>Input is never saved or logged in the database.</span>
                  <span>{scamInput.length}/1000</span>
                </div>
              </div>

              {scamError && (
                <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs p-3 rounded-lg flex items-start space-x-2">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <span>{scamError}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={checkingScam || !scamInput.trim()}
                className="w-full sm:w-auto inline-flex items-center justify-center space-x-2 bg-teal-500 hover:bg-teal-600 disabled:opacity-50 text-slate-950 font-semibold px-4 py-2 rounded-lg text-xs transition min-h-[44px]"
              >
                {checkingScam ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Evaluating signals...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>{t('learn.scam_checker_submit')}</span>
                  </>
                )}
              </button>
            </form>
          </div>

          {/* Results Output */}
          {scamResult && (
            <div 
              aria-live="polite"
              className={`mt-6 border rounded-xl p-4 transition ${
                scamResult.risk_level === 'high'
                  ? 'bg-rose-950/20 border-rose-800/60'
                  : scamResult.risk_level === 'medium'
                  ? 'bg-amber-950/20 border-amber-800/60'
                  : 'bg-teal-950/20 border-teal-800/60'
              }`}
            >
              <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
                <div className="flex items-center space-x-2">
                  {scamResult.is_suspicious ? (
                    <AlertTriangle className={`w-5 h-5 ${scamResult.risk_level === 'high' ? 'text-rose-400' : 'text-amber-400'}`} />
                  ) : (
                    <CheckCircle2 className="w-5 h-5 text-teal-400" />
                  )}
                  <h3 className="text-sm font-bold text-white">
                    {scamResult.is_suspicious
                      ? t('learn.scam_checker_suspicious')
                      : t('learn.scam_checker_clean')}
                  </h3>
                </div>
                <span className={`text-[11px] font-bold uppercase px-2.5 py-0.5 rounded border ${
                  scamResult.risk_level === 'high'
                    ? 'bg-rose-500/20 border-rose-500/40 text-rose-300'
                    : scamResult.risk_level === 'medium'
                    ? 'bg-amber-500/20 border-amber-500/40 text-amber-300'
                    : 'bg-teal-500/20 border-teal-500/40 text-teal-300'
                }`}>
                  {scamResult.risk_level} Risk
                </span>
              </div>

              {/* Matched Signals */}
              {scamResult.matched_signals.length > 0 && (
                <div className="mb-3 space-y-1.5">
                  <div className="text-xs font-semibold text-slate-300">Detected Indicators:</div>
                  {scamResult.matched_signals.map((sig, idx) => (
                    <div key={idx} className="bg-slate-900/80 border border-slate-800 rounded p-2 text-xs">
                      <div className="font-semibold text-amber-300">{sig.name}</div>
                      <div className="text-slate-400 text-[11px] mt-0.5">{sig.description}</div>
                    </div>
                  ))}
                </div>
              )}

              {/* Recommended Action / Advice */}
              <div className="space-y-1 mb-3">
                <div className="text-xs font-semibold text-slate-300">Official Safety Recommendations:</div>
                <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
                  {scamResult.advice_codes.map((code, idx) => (
                    <li key={idx}>{t(code)}</li>
                  ))}
                </ul>
              </div>

              {/* Disclaimer */}
              <div className="text-[11px] text-slate-500 italic pt-2 border-t border-slate-800/60">
                {scamResult.disclaimer}
              </div>
            </div>
          )}
        </div>

        {/* Before-You-Pay Checklist */}
        <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-sm">
          <div className="flex items-center space-x-2 mb-3">
            <CheckSquare className="w-5 h-5 text-teal-400" />
            <h2 className="text-base font-semibold text-white">{t('learn.checklist_heading')}</h2>
          </div>
          <p className="text-xs text-slate-400 mb-4">
            Practice this 5-point verification standard before executing any UPI or online transaction:
          </p>

          <div className="space-y-3">
            {checklistPoints.map((item) => (
              <label
                key={item.id}
                onClick={() => toggleChecklist(item.id)}
                className={`flex items-start space-x-3 p-3 rounded-lg border transition cursor-pointer select-none min-h-[44px] ${
                  checkedItems[item.id]
                    ? 'bg-teal-500/10 border-teal-500/40 text-teal-200'
                    : 'bg-slate-950 border-slate-800 text-slate-300 hover:border-slate-700'
                }`}
              >
                <input
                  type="checkbox"
                  checked={checkedItems[item.id]}
                  onChange={() => {}}
                  className="mt-0.5 rounded border-slate-700 text-teal-500 focus:ring-teal-400"
                />
                <span className="text-xs leading-relaxed">{item.text}</span>
              </label>
            ))}
          </div>

          <div className="mt-4 pt-4 border-t border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
            <span>Standard: NPCI & RBI Fraud Prevention</span>
            <span className="text-teal-400 font-semibold">
              {Object.values(checkedItems).filter(Boolean).length}/5 Verified
            </span>
          </div>
        </div>
      </div>

      {/* Verified Static Guidance Library */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Info className="w-5 h-5 text-teal-400" />
            <h2 className="text-lg font-bold text-white">Verified Guidance & Official Resources</h2>
          </div>
          <button
            onClick={fetchGuidance}
            className="text-xs text-slate-400 hover:text-teal-400 flex items-center space-x-1"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Refresh</span>
          </button>
        </div>

        {loadingGuidance ? (
          <div className="flex items-center justify-center p-8 bg-slate-900 border border-slate-800 rounded-xl">
            <Loader2 className="w-6 h-6 animate-spin text-teal-400" />
          </div>
        ) : guidanceError ? (
          <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs p-4 rounded-xl">
            {guidanceError}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {guidanceItems.map((item) => (
              <div
                key={item.id}
                className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col justify-between hover:border-slate-700 transition"
              >
                <div>
                  <div className="flex items-center space-x-2 mb-2">
                    {item.topic === 'helpline' ? (
                      <PhoneCall className="w-4 h-4 text-rose-400" />
                    ) : item.topic === 'sanchar_saathi' ? (
                      <ShieldAlert className="w-4 h-4 text-amber-400" />
                    ) : (
                      <HelpCircle className="w-4 h-4 text-teal-400" />
                    )}
                    <h3 className="text-sm font-bold text-white leading-snug">{item.title}</h3>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed mt-2">{item.body}</p>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] text-slate-400 space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-300">{item.source_label}</span>
                    {item.source_url && (
                      <a
                        href={item.source_url}
                        target="_blank"
                        rel="noreferrer noopener"
                        className="text-teal-400 hover:underline flex items-center space-x-0.5"
                      >
                        <span>Visit</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                  <div className="text-slate-500">
                    Last verified: {item.last_verified} • Prototype guidance — confirm with official sources
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
