import React, { useState } from 'react';
import { 
  Search, 
  Send, 
  CheckCircle, 
  AlertTriangle, 
  ShieldCheck, 
  FileText, 
  Clock, 
  ChevronRight,
  Sparkles,
  Info,
  ExternalLink,
  MessageSquare
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { ResearchResponse, CitationItem } from '../types';

interface ResearchViewProps {
  onInspectCitation: (citation: CitationItem) => void;
}

export const ResearchView: React.FC<ResearchViewProps> = ({ onInspectCitation }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ResearchResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeCitation, setActiveCitation] = useState<CitationItem | null>(null);

  const sampleQueries = [
    "What is the liability cap under the agreement?",
    "What are the non-disclosure obligations and survival period?",
    "Does the counterparty have unilateral termination rights?",
    "What is the penalty for international maritime collisions? (Abstention Test)",
  ];

  const handleSearch = async (queryString?: string) => {
    const q = queryString || query;
    if (!q.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await ApiClient.post<ResearchResponse>('/research', { query: q });
      setResult(res);
      if (res.citations && res.citations.length > 0) {
        setActiveCitation(res.citations[0]);
      } else {
        setActiveCitation(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to execute research workflow.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-140px)] animate-in fade-in duration-200">
      {/* LEFT PANEL: Sessions & Sample Queries (3 cols) */}
      <div className="lg:col-span-3 legal-card p-4 flex flex-col justify-between overflow-y-auto">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
            <MessageSquare className="w-3.5 h-3.5 text-amber-400" />
            <span>Research Sessions & Vault</span>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 font-medium block mb-2">Sample Research Scenarios</label>
            <div className="space-y-2">
              {sampleQueries.map((sq, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setQuery(sq);
                    handleSearch(sq);
                  }}
                  className="w-full text-left p-2.5 rounded-xl bg-slate-900/60 hover:bg-slate-800/80 border border-slate-800 hover:border-amber-500/30 text-xs text-slate-300 transition-all flex items-start justify-between group"
                >
                  <span className="line-clamp-2 leading-snug">{sq}</span>
                  <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-amber-400 shrink-0 mt-0.5 ml-1 transition-transform group-hover:translate-x-0.5" />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Grounding Policy Card */}
        <div className="p-3.5 rounded-xl bg-[#111D36]/70 border border-slate-800 text-[11px] text-slate-400 space-y-1.5 mt-4">
          <div className="flex items-center gap-1.5 font-semibold text-slate-200">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Zero-Hallucination Policy</span>
          </div>
          <p className="leading-relaxed">
            Every factual proposition is linked to an underlying text passage. Unsubstantiated claims are flagged or trigger abstention.
          </p>
        </div>
      </div>

      {/* CENTER PANEL: Answer & Claims Synthesis (6 cols) */}
      <div className="lg:col-span-6 legal-card flex flex-col justify-between overflow-hidden">
        {/* Research Output Viewport */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          {error && (
            <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-start gap-2.5">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold text-rose-200">Execution Error:</span> {error}
              </div>
            </div>
          )}

          {loading ? (
            <div className="py-24 text-center space-y-4">
              <div className="w-12 h-12 rounded-full border-2 border-amber-500/20 border-t-amber-500 animate-spin mx-auto" />
              <div>
                <h4 className="text-sm font-semibold text-white">Executing LangGraph Research Workflow...</h4>
                <p className="text-xs text-slate-400 mt-1">
                  Hybrid retrieval → RRF rank fusion → Claim synthesis → Quote verification
                </p>
              </div>
            </div>
          ) : result ? (
            <div className="space-y-6 animate-in fade-in duration-200">
              {/* Header Status & Confidence */}
              <div className="flex flex-wrap items-center justify-between gap-3 pb-4 border-b border-slate-800">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-slate-400">Workflow Status:</span>
                  {result.status === 'COMPLETED' ? (
                    <span className="badge-verified">
                      <CheckCircle className="w-3 h-3" /> Fully Verified
                    </span>
                  ) : result.status === 'ABSTAINED' ? (
                    <span className="badge-gold">
                      <Info className="w-3 h-3" /> Abstention Triggered
                    </span>
                  ) : (
                    <span className="badge-review">
                      <AlertTriangle className="w-3 h-3" /> In Review Queue
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 text-xs">
                  <span className="text-slate-400">Grounding Confidence:</span>
                  <div className="w-24 h-2 rounded-full bg-slate-800 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all ${
                        result.confidence_score >= 0.85
                          ? 'bg-emerald-500'
                          : result.confidence_score >= 0.60
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${Math.round(result.confidence_score * 100)}%` }}
                    />
                  </div>
                  <span className="font-mono font-bold text-slate-200">
                    {(result.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              {/* Synthesized Answer */}
              <div className="space-y-3">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Evidence-Backed Legal Synthesis
                </label>
                <div className="p-5 rounded-2xl bg-slate-900/50 border border-slate-800 text-slate-200 text-sm leading-relaxed whitespace-pre-wrap font-serif">
                  {result.answer}
                </div>
              </div>

              {/* Claim-Level Evidence Coverage */}
              {result.claims && result.claims.length > 0 && (
                <div className="space-y-3">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Claim-Level Grounding Assessment ({result.claims.length} Claims)
                  </label>
                  <div className="space-y-2">
                    {result.claims.map((claim) => (
                      <div
                        key={claim.id}
                        className="p-3.5 rounded-xl bg-[#111D36]/50 border border-slate-800/80 flex items-start justify-between gap-3 text-xs"
                      >
                        <div className="space-y-1">
                          <p className="text-slate-200">{claim.claim_text}</p>
                          <span className="text-[10px] text-slate-400">Claim ID: {claim.id}</span>
                        </div>
                        {claim.status === 'VERIFIED' ? (
                          <span className="badge-verified shrink-0">
                            <CheckCircle className="w-3 h-3" /> Grounded
                          </span>
                        ) : (
                          <span className="badge-unsupported shrink-0">
                            <AlertTriangle className="w-3 h-3" /> Unsupported
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Limitations & Legal Caveats */}
              {result.limitations && result.limitations.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs text-amber-200/90 space-y-1">
                  <div className="font-semibold text-amber-300 flex items-center gap-1.5 mb-1">
                    <Info className="w-3.5 h-3.5" />
                    <span>Statutory Limitations & Scope</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-slate-300">
                    {result.limitations.map((lim, i) => (
                      <li key={i}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ) : (
            <div className="py-24 text-center space-y-3 text-slate-400">
              <Search className="w-10 h-10 mx-auto text-slate-400" />
              <h4 className="text-sm font-semibold text-slate-300">Submit a Research Question</h4>
              <p className="text-xs max-w-sm mx-auto">
                Type your inquiry below or select a sample scenario from the left panel to execute an evidence-backed search.
              </p>
            </div>
          )}
        </div>

        {/* Input Bar */}
        <div className="p-4 border-t border-slate-800 bg-[#0B132B]/90">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSearch();
            }}
            className="flex items-center gap-3"
          >
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask a legal or contractual question (e.g. 'What is the indemnification trigger?')..."
              className="flex-1 bg-[#0D1527] border border-slate-700/80 rounded-xl px-4 py-2.5 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors"
            />
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold text-xs shadow-md shadow-amber-500/10 disabled:opacity-50 transition-all flex items-center gap-1.5 cursor-pointer"
            >
              <span>Verify</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>
      </div>

      {/* RIGHT PANEL: Source Citations & Document Passage Inspector (3 cols) */}
      <div className="lg:col-span-3 legal-card p-4 overflow-y-auto space-y-4">
        <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400 pb-2 border-b border-slate-800">
          <FileText className="w-3.5 h-3.5 text-blue-400" />
          <span>Source Evidence Chunks</span>
        </div>

        {result && result.citations && result.citations.length > 0 ? (
          <div className="space-y-3">
            {result.citations.map((cit, idx) => (
              <div
                key={cit.id}
                onClick={() => {
                  setActiveCitation(cit);
                  onInspectCitation(cit);
                }}
                className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all space-y-2 ${
                  activeCitation?.id === cit.id
                    ? 'bg-[#1C2541] border-amber-500/50 shadow-md shadow-amber-500/5'
                    : 'bg-slate-900/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-amber-300">Citation [{idx + 1}]</span>
                  {cit.verified ? (
                    <span className="badge-verified text-[10px]">Verified</span>
                  ) : (
                    <span className="badge-unsupported text-[10px]">Unverified</span>
                  )}
                </div>

                <div className="font-serif text-slate-300 text-xs italic line-clamp-3 bg-black/20 p-2 rounded-lg border border-slate-800">
                  "{cit.quote_snippet}"
                </div>

                <div className="flex items-center justify-between text-[10px] text-slate-400 pt-1">
                  <span>{cit.document_name}</span>
                  <span>p. {cit.page_number}</span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-20 text-center text-xs text-slate-400 space-y-2">
            <FileText className="w-8 h-8 mx-auto text-slate-400 opacity-60" />
            <p>No citations loaded.</p>
            <p className="text-[11px] text-slate-400">Execute a query to inspect verified passages.</p>
          </div>
        )}
      </div>
    </div>
  );
};
