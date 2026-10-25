import React, { useState } from 'react';
import { 
  GitCompare, 
  FileText, 
  CheckCircle, 
  AlertTriangle, 
  ShieldAlert, 
  ArrowRight,
  ListFilter,
  Sparkles,
  Wand2,
  Copy,
  Check,
  ShieldCheck,
  BookOpen
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { DocumentItem } from '../types';

interface ContractAnalysisViewProps {
  documents: DocumentItem[];
}

export const ContractAnalysisView: React.FC<ContractAnalysisViewProps> = ({ documents }) => {
  const [activeSubTab, setActiveSubTab] = useState<'compare' | 'summary' | 'clauses' | 'obligations' | 'playbook'>('compare');
  const [docA, setDocA] = useState<string>(documents[0]?.id || '');
  const [docB, setDocB] = useState<string>(documents[1]?.id || documents[0]?.id || '');
  const [loading, setLoading] = useState(false);
  const [diffResult, setDiffResult] = useState<any | null>(null);
  const [summaryResult, setSummaryResult] = useState<any | null>(null);
  const [clausesResult, setClausesResult] = useState<any[]>([]);
  const [obligationsResult, setObligationsResult] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Playbook & Remediation State
  const [playbookClauseType, setPlaybookClauseType] = useState('Limitation of Liability');
  const [playbookOriginalText, setPlaybookOriginalText] = useState('In no event shall aggregate liability exceed three times (3x) the fees, excluding data breach indemnification which shall be uncapped.');
  const [negotiationStance, setNegotiationStance] = useState('BALANCED');
  const [remediationResult, setRemediationResult] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

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

  const handleRemediate = async () => {
    if (!playbookOriginalText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res: any = await ApiClient.post('/analysis/remediate-clause', {
        clause_type: playbookClauseType,
        original_text: playbookOriginalText,
        risk_level: 'HIGH',
        negotiation_stance: negotiationStance,
      });
      setRemediationResult(res);
    } catch (err: any) {
      setError(err.message || 'Failed to generate clause remediation.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
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
        <div className="flex flex-wrap items-center gap-1 bg-[#0D1527] p-1 rounded-xl border border-slate-800">
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
              setActiveSubTab('playbook');
              if (!remediationResult) handleRemediate();
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
              activeSubTab === 'playbook' ? 'bg-gradient-to-r from-amber-500 to-amber-600 text-slate-950 font-semibold shadow-sm' : 'text-amber-400/90 hover:text-amber-300'
            }`}
          >
            <Wand2 className="w-3.5 h-3.5" />
            <span>Playbook & Remediation</span>
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

      {/* PLAYBOOK & REMEDIATION SUB-TAB */}
      {activeSubTab === 'playbook' && (
        <div className="space-y-6">
          <div className="legal-card p-6 space-y-5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-400">
                  <Wand2 className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-white">Clause Risk Remediation Engine</h3>
                  <p className="text-xs text-slate-400">Transform unfavorable counterparty terms into balanced or protective language backed by market precedent.</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-[11px] font-medium text-amber-400">
                <BookOpen className="w-3.5 h-3.5" />
                <span>Firm Playbook AI</span>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Target Clause Category</label>
                <select
                  value={playbookClauseType}
                  onChange={(e) => setPlaybookClauseType(e.target.value)}
                  className="w-full bg-[#070C18] border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-500/50"
                >
                  <option value="Limitation of Liability">Limitation of Liability (Cap & Consequential Damages)</option>
                  <option value="Indemnification">Indemnification (IP, Gross Negligence & Third-Party Claims)</option>
                  <option value="Termination for Cause">Termination for Cause & Cure Notice Periods</option>
                  <option value="Confidentiality & Non-Disclosure">Confidentiality & Non-Disclosure (Standard of Care)</option>
                  <option value="Warranty & Disclaimer">Warranty & As-Is Disclaimers</option>
                  <option value="Governing Law & Jurisdiction">Governing Law, Exclusive Venue & Arbitration</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-1.5">Negotiation Stance</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'BALANCED', label: 'Balanced', desc: 'Market standard' },
                    { id: 'PROTECTIVE_CLIENT', label: 'Client First', desc: 'Strong shielding' },
                    { id: 'AGGRESSIVE_DEFENSE', label: 'Strict Defense', desc: 'Maximum carveouts' },
                  ].map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setNegotiationStance(s.id)}
                      className={`px-3 py-2 rounded-xl text-xs font-medium border text-left transition-all ${
                        negotiationStance === s.id
                          ? 'bg-amber-500/15 border-amber-500 text-amber-300 shadow-sm'
                          : 'bg-[#070C18] border-slate-800 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <div className="font-semibold">{s.label}</div>
                      <div className="text-[10px] opacity-75">{s.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Counterparty Clause Draft (To Remediate)
              </label>
              <textarea
                rows={3}
                value={playbookOriginalText}
                onChange={(e) => setPlaybookOriginalText(e.target.value)}
                className="w-full bg-[#070C18] border border-slate-700 rounded-xl p-3 text-xs text-slate-200 font-serif leading-relaxed focus:outline-none focus:border-amber-500/50"
                placeholder="Paste the high-risk or ambiguous counterparty language..."
              />
            </div>

            <div className="flex justify-end">
              <button
                onClick={handleRemediate}
                disabled={loading || !playbookOriginalText.trim()}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-400 hover:to-amber-500 text-slate-950 font-semibold text-xs shadow-md shadow-amber-500/10 disabled:opacity-50 transition-all flex items-center gap-2 cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>{loading ? 'Synthesizing Playbook Fallbacks...' : 'Generate Playbook Remediation'}</span>
              </button>
            </div>
          </div>

          {/* Remediation Results */}
          {remediationResult && (
            <div className="space-y-6">
              {/* Risk Diagnosis Banner */}
              <div className="p-4 rounded-2xl bg-amber-950/20 border border-amber-500/30 flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="text-xs font-semibold text-white">Risk Diagnosis: {remediationResult.clause_type}</h4>
                    <p className="text-xs text-slate-300 mt-0.5 leading-relaxed">
                      {remediationResult.risk_diagnosis}
                    </p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-md text-[10px] font-bold tracking-wider uppercase bg-rose-500/10 border border-rose-500/30 text-rose-300 shrink-0">
                  {remediationResult.risk_level} EXPOSURE
                </span>
              </div>

              {/* Side-by-side: Proposed Redline vs Fallback Compromise */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Proposed Primary Redline */}
                <div className="legal-card p-5 space-y-3 border-emerald-500/30 bg-emerald-950/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <ShieldCheck className="w-4 h-4 text-emerald-400" />
                      <span className="text-xs font-semibold text-emerald-300">Proposed Primary Redline</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(remediationResult.proposed_redline)}
                      className="px-2.5 py-1 rounded-lg bg-emerald-900/40 hover:bg-emerald-900/60 border border-emerald-700/50 text-[11px] text-emerald-200 transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                      <span>{copied ? 'Copied' : 'Copy Redline'}</span>
                    </button>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#070C18] border border-emerald-900/40 text-xs font-serif text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {remediationResult.proposed_redline}
                  </div>
                  <div className="text-[11px] text-emerald-400/90 flex items-center gap-1 font-medium">
                    <CheckCircle className="w-3 h-3" />
                    <span>Configured for {remediationResult.negotiation_stance.replace('_', ' ')} posture</span>
                  </div>
                </div>

                {/* Fallback Compromise Language */}
                <div className="legal-card p-5 space-y-3 border-amber-500/30 bg-amber-950/10">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Sparkles className="w-4 h-4 text-amber-400" />
                      <span className="text-xs font-semibold text-amber-300">Fallback / Compromise Language</span>
                    </div>
                    <button
                      onClick={() => copyToClipboard(remediationResult.fallback_compromise)}
                      className="px-2.5 py-1 rounded-lg bg-amber-900/40 hover:bg-amber-900/60 border border-amber-700/50 text-[11px] text-amber-200 transition-all flex items-center gap-1.5 cursor-pointer"
                    >
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy Fallback</span>
                    </button>
                  </div>
                  <div className="p-3.5 rounded-xl bg-[#070C18] border border-amber-900/40 text-xs font-serif text-slate-200 leading-relaxed whitespace-pre-wrap">
                    {remediationResult.fallback_compromise}
                  </div>
                  <div className="text-[11px] text-amber-400/90 flex items-center gap-1 font-medium">
                    <AlertTriangle className="w-3 h-3" />
                    <span>Concession position if counterparty rejects primary redline</span>
                  </div>
                </div>
              </div>

              {/* Legal Rationale & Negotiation Talking Points */}
              <div className="legal-card p-5 space-y-3">
                <div className="flex items-center gap-2">
                  <ListFilter className="w-4 h-4 text-amber-400" />
                  <h4 className="text-xs font-semibold text-white">Negotiation Talking Points for Legal Counsel</h4>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {remediationResult.negotiation_talking_points?.map((point: string, idx: number) => (
                    <div key={idx} className="p-3 rounded-xl bg-[#070C18] border border-slate-800 text-xs text-slate-300 flex items-start gap-2.5">
                      <span className="w-5 h-5 rounded-full bg-amber-500/20 text-amber-400 text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                        {idx + 1}
                      </span>
                      <span className="leading-relaxed">{point}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
