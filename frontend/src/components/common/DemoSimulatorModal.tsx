import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, RotateCcw, Clock, AlertTriangle, ShieldCheck, ShieldAlert, X, Sparkles } from 'lucide-react';
import { api, getErrorMessage } from '../../services/api';

interface DemoSimulatorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onScenarioSelect?: (scenario: any) => void;
}

export const DemoSimulatorModal: React.FC<DemoSimulatorModalProps> = ({ isOpen, onClose, onScenarioSelect }) => {
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [resetting, setResetting] = useState<boolean>(false);
  const [resetMessage, setResetMessage] = useState<string | null>(null);
  const [confirmReset, setConfirmReset] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      loadScenarios();
      setResetMessage(null);
      setError(null);
      setConfirmReset(false);
    }
  }, [isOpen]);

  async function loadScenarios() {
    setLoading(true);
    try {
      const data = await api.getScenarios();
      setScenarios(data.scenarios || []);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleResetDemo() {
    setResetting(true);
    setError(null);
    try {
      const res = await api.resetDemo();
      setResetMessage(`Demo database successfully restored in ${res.duration_seconds}s.`);
      setConfirmReset(false);
      setTimeout(() => {
        window.location.reload();
      }, 1000);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setResetting(false);
    }
  }

  function handleSelectScenario(scenario: any) {
    if (onScenarioSelect) {
      onScenarioSelect(scenario);
    } else {
      // Store in session storage for NewPaymentPage to pick up
      sessionStorage.setItem('prefilled_scenario', JSON.stringify(scenario));
      navigate('/pay');
    }
    onClose();
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Header */}
        <div className="bg-linear-to-r from-slate-900 to-indigo-950 px-6 py-4 flex items-center justify-between text-white">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 bg-indigo-500/20 rounded-lg border border-indigo-400/30">
              <Sparkles className="w-5 h-5 text-indigo-300" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold tracking-tight">Demo Risk Simulator</h3>
                <span className="text-[10px] font-semibold uppercase bg-amber-400/20 text-amber-300 border border-amber-400/30 px-2 py-0.5 rounded-full flex items-center space-x-1">
                  <Clock className="w-3 h-3 inline mr-1" />
                  <span>Simulated Time Available</span>
                </span>
              </div>
              <p className="text-xs text-slate-300">Test deterministic risk detection with pre-configured attack presets</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-white/10 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4 max-h-[70vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg text-xs text-rose-700 flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {resetMessage && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-xs text-emerald-700 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 shrink-0" />
              <span>{resetMessage} Refreshing...</span>
            </div>
          )}

          {/* Reset Demo Section */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 flex items-center justify-between">
            <div>
              <span className="text-xs font-bold text-slate-800 block">Clean State Demo Reset</span>
              <span className="text-[11px] text-slate-500 block">Restores demo database and seeded accounts in under 5.0 seconds.</span>
            </div>
            {confirmReset ? (
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setConfirmReset(false)}
                  className="px-2.5 py-1 text-xs text-slate-600 hover:bg-slate-200 rounded transition"
                  disabled={resetting}
                >
                  Cancel
                </button>
                <button
                  onClick={handleResetDemo}
                  disabled={resetting}
                  className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center space-x-1"
                >
                  {resetting ? (
                    <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <RotateCcw className="w-3.5 h-3.5 mr-1" />
                  )}
                  <span>Confirm Reset</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => setConfirmReset(true)}
                className="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 rounded-lg text-xs font-medium shadow-2xs transition flex items-center space-x-1.5"
              >
                <RotateCcw className="w-3.5 h-3.5 text-slate-500" />
                <span>Reset Demo State</span>
              </button>
            )}
          </div>

          <div className="border-t border-slate-200 pt-3">
            <h4 className="text-xs font-bold text-slate-600 uppercase tracking-wider mb-3">
              One-Click Scenario Presets (§16)
            </h4>

            {loading ? (
              <div className="py-8 text-center space-y-2">
                <div className="w-6 h-6 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
                <p className="text-xs text-slate-500">Loading demo presets...</p>
              </div>
            ) : (
              <div className="space-y-3">
                {scenarios.map((sc) => {
                  let bandColor = 'bg-emerald-50 text-emerald-700 border-emerald-200';
                  let Icon = ShieldCheck;
                  if (sc.id.startsWith('medium')) {
                    bandColor = 'bg-amber-50 text-amber-700 border-amber-200';
                    Icon = AlertTriangle;
                  } else if (sc.id.startsWith('high')) {
                    bandColor = 'bg-rose-50 text-rose-700 border-rose-200';
                    Icon = ShieldAlert;
                  }

                  return (
                    <div
                      key={sc.id}
                      className="p-3.5 rounded-xl border border-slate-200 hover:border-indigo-300 hover:shadow-xs transition bg-white flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1">
                        <div className="flex items-center space-x-2">
                          <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${bandColor} flex items-center space-x-1`}>
                            <Icon className="w-3 h-3 mr-0.5" />
                            <span>{sc.fixture}</span>
                          </span>
                          <span className="text-xs font-bold text-slate-900">{sc.title}</span>
                        </div>
                        <p className="text-[11px] text-slate-500">{sc.description}</p>
                        {sc.payload?.simulated_at && (
                          <div className="flex items-center space-x-1 text-[10px] text-indigo-600 font-medium">
                            <Clock className="w-3 h-3" />
                            <span>Simulated Timestamp: {sc.payload.simulated_at}</span>
                          </div>
                        )}
                      </div>

                      <button
                        onClick={() => handleSelectScenario(sc)}
                        className="inline-flex items-center justify-center space-x-1.5 px-3 py-1.5 bg-indigo-50 hover:bg-indigo-600 text-indigo-700 hover:text-white rounded-lg text-xs font-semibold transition shrink-0 self-end sm:self-center"
                      >
                        <Play className="w-3.5 h-3.5" />
                        <span>Load Preset</span>
                      </button>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-slate-50 px-6 py-3 border-t border-slate-200 flex items-center justify-between text-[11px] text-slate-500">
          <span>Simulated demo mode active. No actual banking transfers take place.</span>
          <button
            onClick={onClose}
            className="px-3 py-1 bg-white border border-slate-300 rounded text-slate-700 hover:bg-slate-100 font-medium text-xs transition"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
