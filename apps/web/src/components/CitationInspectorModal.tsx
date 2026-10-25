import React, { useEffect } from 'react';
import { X, CheckCircle, AlertTriangle, FileText, Hash, ExternalLink } from 'lucide-react';
import { CitationItem } from '../types';

interface CitationInspectorModalProps {
  citation: CitationItem | null;
  onClose: () => void;
}

export const CitationInspectorModal: React.FC<CitationInspectorModalProps> = ({ citation, onClose }) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  if (!citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-150">
      <div 
        className="w-full max-w-2xl bg-[#0D1527] border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#111D36]/80">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                <span>Citation Grounding Inspector</span>
                {citation.verified ? (
                  <span className="badge-verified text-[10px]">
                    <CheckCircle className="w-3 h-3" /> Grounded & Verified
                  </span>
                ) : (
                  <span className="badge-unsupported text-[10px]">
                    <AlertTriangle className="w-3 h-3" /> Unverified Quote
                  </span>
                )}
              </h3>
              <p className="text-xs text-slate-400">{citation.document_name} • Page {citation.page_number}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-5">
          {/* Quoted Passage */}
          <div>
            <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2 block">
              Quoted Text Snippet
            </label>
            <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 font-serif text-slate-200 text-sm leading-relaxed relative">
              <span className="text-amber-500/40 text-3xl font-serif absolute top-1 left-2 pointer-events-none">“</span>
              <p className="pl-3">{citation.quote_snippet}</p>
            </div>
          </div>

          {/* Verification Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1.5 mb-1">
                <Hash className="w-3 h-3 text-slate-400" />
                <span>Chunk UUID</span>
              </div>
              <div className="text-xs font-mono text-slate-300 truncate" title={citation.chunk_id}>
                {citation.chunk_id}
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-medium flex items-center gap-1.5 mb-1">
                <FileText className="w-3 h-3 text-slate-400" />
                <span>Source Document</span>
              </div>
              <div className="text-xs font-medium text-slate-300 truncate">
                {citation.document_name}
              </div>
            </div>
          </div>

          {/* Legal Disclosure Note */}
          <div className="p-3.5 rounded-xl bg-blue-950/30 border border-blue-900/40 text-xs text-blue-300/90 leading-relaxed">
            <span className="font-semibold text-blue-200">Integrity Guarantee:</span> This citation was verified against immutable text chunks extracted during document indexing. Quotation alignment is checked via deterministic string comparison and Levenshtein similarity to prevent model-generated hallucinations.
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3.5 bg-slate-900/80 border-t border-slate-800 flex items-center justify-between">
          <span className="text-[11px] text-slate-400">TrustCounsel AI Trust Engine • Rule TR-001</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
