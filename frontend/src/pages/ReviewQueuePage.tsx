import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import type { ReviewCase } from '../types';
import { formatPaise } from '../types';

export const ReviewQueuePage: React.FC = () => {
  const { user } = useAuth();
  const [cases, setCases] = useState<ReviewCase[]>([]);

  useEffect(() => {
    async function loadCases() {
      try {
        const data = await api.getReviewCases().catch(() => []);
        setCases(data);
      } catch (e) {
        console.error(e);
      }
    }
    loadCases();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200/80 shadow-xs">
        <div>
          <span className="text-xs font-semibold text-purple-600 uppercase tracking-wider block mb-0.5">
            {user?.role === 'supervisor' ? 'Supervisor Risk Console' : 'Reviewer Queue'}
          </span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Held Payment Cases
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Evaluate flagged high-risk payments. Customer and payee references are strictly masked for privacy.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-slate-800">Pending Review Queue ({cases.length})</h2>
        </div>

        {cases.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500">
            No pending cases in queue. All payments have been evaluated.
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {cases.map((c) => (
              <div key={c.id} className="p-4 hover:bg-slate-50/80 transition flex items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="text-xs font-bold text-slate-900">Case #{c.id}</span>
                    <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-amber-100 text-amber-800">
                      Score: {c.score} ({c.band})
                    </span>
                    <span className="text-[10px] text-slate-400">Masked Customer: {c.masked_customer_ref}</span>
                  </div>
                  <div className="text-xs text-slate-600">
                    Amount: <span className="font-semibold">{formatPaise(c.amount_paise)}</span> • Payee: {c.masked_payee} • Method: {c.method}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <button className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded text-xs font-medium transition">
                    Inspect Case
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
