import React, { useState } from 'react';
import { 
  GitCompare, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  ArrowRight,
  ListFilter,
  Sparkles
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { DocumentItem } from '../types';

interface ContractAnalysisViewProps {
  documents: DocumentItem[];
}

export const ContractAnalysisView: React.FC<ContractAnalysisViewProps> = ({ documents }) => {
  const [activeSubTab, setActiveSubTab] = useState<'compare' | 'summary' | 'clauses' | 'obligations'>('compare');
  const [docA, setDocA] = useState<string>(documents[0]?.id || '');
  const [docB, setDocB] = useState<string>(documents[1]?.id || documents[0]?.id || '');
  const [loading, setLoading] = useState(false);
  const [diffResult, setDiffResult] = useState<any | null>(null);
  const [summaryResult, setSummaryResult] = useState<any | null>(null);
  const [clausesResult, setClausesResult] = useState<any[]>([]);
  const [obligationsResult, setObligationsResult] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!docA || !docB) return;
    setLoading(true);
    setError(null);
    try {
      const res = await ApiClient.post('/analysis/compare', {
        document_a_id: docA,
        document_b_id: docB,
      });
      setDiffResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to compare contract versions.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchSummary = async () => {
    if (!docA) return;
    setLoading(true);
    try {
      const res = await ApiClient.post('/analysis/summarize', { document_id: docA });
      setSummaryResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch summary.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchClauses = async () => {
    if (!docA) return;
    setLoading(true);
    try {
      const res: any = await ApiClient.post('/analysis/extract-clauses', { document_id: docA });
      setClausesResult(res.clauses || []);
    } catch (err: any) {
      setError(err.message || 'Failed to extract clauses.');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchObligations = async () => {
    if (!docA) return;
    setLoading(true);
    try {
      const res: any = await ApiClient.post('/analysis/extract-obligations', { document_id: docA });
      setObligationsResult(res.obligations || []);
    } catch (err: any) {
      setError(err.message || 'Failed to extract obligations.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header and Sub-tabs */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-serif font-bold text-white">Contract Intelligence & Redline Diff</h2>
          <p className="text-xs text-slate-400">
            Automated clause extraction, structured obligations, and side-by-side version comparison with risk flagging.
          </p>
        </div>

        {/* Sub-tab navigation */}
        <div className="flex items-center gap-1 bg-[#0D1527] p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveSubTab('compare')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeSubTab === 'compare' ? 'bg-amber-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Redline Comparison
          </button>
          <button
            onClick={() => {
              setActiveSubTab('summary');
              if (!summaryResult) handleFetchSummary();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeSubTab === 'summary' ? 'bg-amber-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Executive Summary
          </button>
          <button
            onClick={() => {
              setActiveSubTab('clauses');
              if (clausesResult.length === 0) handleFetchClauses();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeSubTab === 'clauses' ? 'bg-amber-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Clause Extraction
          </button>
          <button
            onClick={() => {
              setActiveSubTab('obligations');
              if (obligationsResult.length === 0) handleFetchObligations();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeSubTab === 'obligations' ? 'bg-amber-500 text-slate-950 font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            Obligations
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* COMPARISON SUB-TAB */}
      {activeSubTab === 'compare' && (
        <div className="space-y-6">
          {/* Selector controls */}
          <div className="legal-card p-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-center">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Baseline Version (Document A)</label>
                <select
                  value={docA}
                  onChange={(e) => setDocA(e.target.value)}
                  className="w-full bg-[#070C18] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                >
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title || d.filename}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Counterparty Draft (Document B)</label>
                <select
                  value={docB}
                  onChange={(e) => setDocB(e.target.value)}
                  className="w-full bg-[#070C18] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white"
                >
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.title || d.filename}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="mt-4 flex justify-end">
              <button
                onClick={handleCompare}
                disabled={loading || !docA || !docB}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold text-xs shadow-md shadow-amber-500/10 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
              >
                <GitCompare className="w-4 h-4" />
                <span>{loading ? 'Analyzing Differences...' : 'Run Redline Comparison'}</span>
              </button>
            </div>
          </div>

          {/* Diff Results */}
          {diffResult ? (
            <div className="space-y-6">
              {/* Summary of Changes Banner */}
              <div className="p-4 rounded-xl bg-blue-950/40 border border-blue-800/60 text-xs text-blue-200 flex items-center justify-between">
                <span>{diffResult.summary_of_changes}</span>
                <span className="badge-verified">Semantic Alignment Complete</span>
              </div>

              {/* Modified Clauses Cards */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-white">Modified Provisions & Material Risks</h3>

                {diffResult.modified_clauses?.map((mod: any, idx: number) => (
                  <div key={idx} className="legal-card p-5 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-xs text-white">{mod.clause_type}</span>
                      {mod.materiality === 'HIGH' ? (
                        <span className="badge-unsupported">
                          <ShieldAlert className="w-3 h-3" /> High Risk Change
                        </span>
                      ) : (
                        <span className="badge-gold">
                          <AlertTriangle className="w-3 h-3" /> Medium Materiality
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-serif">
                      <div className="p-3.5 rounded-xl bg-rose-950/20 border border-rose-900/30 text-rose-200">
                        <span className="text-[10px] uppercase font-sans font-bold text-rose-400 block mb-1">Original Draft (A)</span>
                        <p>{mod.text_a}</p>
                      </div>

                      <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-900/30 text-emerald-200">
                        <span className="text-[10px] uppercase font-sans font-bold text-emerald-400 block mb-1">Proposed Modification (B)</span>
                        <p>{mod.text_b}</p>
                      </div>
                    </div>

                    {mod.risk_rationale && (
                      <div className="text-xs text-amber-300/90 bg-amber-500/10 p-2.5 rounded-lg border border-amber-500/20">
                        <span className="font-semibold">Counsel Note:</span> {mod.risk_rationale}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-slate-400 space-y-2">
              <GitCompare className="w-8 h-8 mx-auto text-slate-400 opacity-60" />
              <p>Select two contract instruments and run comparison.</p>
            </div>
          )}
        </div>
      )}

      {/* EXECUTIVE SUMMARY SUB-TAB */}
      {activeSubTab === 'summary' && summaryResult && (
        <div className="legal-card p-6 space-y-4">
          <h3 className="text-sm font-semibold text-white">{summaryResult.title}</h3>
          <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 text-slate-200 text-xs leading-relaxed whitespace-pre-wrap font-serif">
            {summaryResult.summary}
          </div>
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">Key Extracted Terms</label>
            <div className="flex flex-wrap gap-2">
              {summaryResult.key_terms?.map((term: string, i: number) => (
                <span key={i} className="px-3 py-1 rounded-lg bg-[#111D36] border border-slate-700 text-xs text-slate-200">
                  {term}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* CLAUSE EXTRACTION SUB-TAB */}
      {activeSubTab === 'clauses' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {clausesResult.map((c, i) => (
            <div key={i} className="legal-card p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-amber-300">{c.clause_type}</span>
                <span className="text-[10px] text-slate-400">Page {c.page_number}</span>
              </div>
              <p className="font-serif text-slate-300 bg-slate-900/40 p-2.5 rounded-lg border border-slate-800">
                "{c.clause_text}..."
              </p>
            </div>
          ))}
        </div>
      )}

      {/* OBLIGATIONS SUB-TAB */}
      {activeSubTab === 'obligations' && (
        <div className="space-y-4">
          {obligationsResult.map((o, i) => (
            <div key={i} className="legal-card p-5 space-y-2 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-white">{o.responsible_party}</span>
                <span className="badge-verified">Binding Covenant</span>
              </div>
              <p className="text-slate-200 font-serif leading-relaxed">{o.action_required}</p>
              <div className="text-[11px] text-amber-400/90 font-medium">
                Trigger / Survival: {o.deadline_or_trigger}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
