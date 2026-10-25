import React, { useState } from 'react';
import { 
  CheckSquare, 
  CheckCircle, 
  XCircle, 
  RotateCcw, 
  AlertTriangle, 
  FileText, 
  UserCheck,
  ShieldCheck,
  MessageSquare
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { ReviewTaskItem } from '../types';

interface ReviewQueueViewProps {
  reviews: ReviewTaskItem[];
  onRefresh: () => void;
}

export const ReviewQueueView: React.FC<ReviewQueueViewProps> = ({ reviews, onRefresh }) => {
  const [selectedTask, setSelectedTask] = useState<any | null>(null);
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSelectTask = async (task: ReviewTaskItem) => {
    setLoading(true);
    setSuccess(null);
    try {
      const details = await ApiClient.get(`/reviews/${task.id}`);
      setSelectedTask(details);
    } catch (err: any) {
      alert(err.message || 'Failed to load task details.');
    } finally {
      setLoading(false);
    }
  };

  const handleDecision = async (decision: 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED') => {
    if (!selectedTask) return;
    if (!notes.trim()) {
      alert('Reviewer audit notes are mandatory before recording a sign-off decision.');
      return;
    }

    setSubmitting(true);
    try {
      await ApiClient.post(`/reviews/${selectedTask.id}/decision`, {
        decision,
        notes,
      });
      setSuccess(`Decision "${decision}" recorded with permanent audit log.`);
      setNotes('');
      setSelectedTask(null);
      onRefresh();
    } catch (err: any) {
      alert(err.message || 'Failed to record decision.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-serif font-bold text-white">Human Review & Sign-Off Queue</h2>
          <p className="text-xs text-slate-400">
            Mandatory gatekeeper workflow for low-confidence (&lt;0.85), conflicting, or high-risk legal outputs.
          </p>
        </div>
        <span className="badge-review text-xs font-semibold px-3 py-1">
          {reviews.filter(r => r.status === 'PENDING').length} Pending Review
        </span>
      </div>

      {success && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Task List (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
            Review Queue Items
          </label>

          {reviews.length > 0 ? (
            reviews.map((task) => (
              <div
                key={task.id}
                onClick={() => handleSelectTask(task)}
                className={`p-4 rounded-xl border text-xs cursor-pointer transition-all space-y-2 ${
                  selectedTask?.id === task.id
                    ? 'bg-[#1C2541] border-purple-500/60 shadow-lg shadow-purple-500/10'
                    : 'legal-card hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-slate-200 truncate pr-2">{task.query}</span>
                  {task.status === 'PENDING' ? (
                    <span className="badge-review shrink-0">Pending</span>
                  ) : (
                    <span className="badge-verified shrink-0">{task.status}</span>
                  )}
                </div>

                <div className="text-[11px] text-amber-300/90 flex items-center gap-1.5">
                  <AlertTriangle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>{task.trigger_reason}</span>
                </div>

                <div className="text-[10px] text-slate-400 pt-1 flex justify-between">
                  <span>Task ID: {task.id.slice(0, 8)}...</span>
                  <span>{new Date(task.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))
          ) : (
            <div className="legal-card p-12 text-center text-xs text-slate-400 space-y-2">
              <CheckSquare className="w-8 h-8 mx-auto text-slate-400 opacity-60" />
              <p>Queue is empty. No tasks require human intervention.</p>
            </div>
          )}
        </div>

        {/* Task Inspector & Decision Action (7 cols) */}
        <div className="lg:col-span-7">
          {selectedTask ? (
            <div className="legal-card p-6 space-y-6">
              <div className="border-b border-slate-800 pb-3 flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-semibold text-white">Review Draft Answer</h3>
                  <p className="text-[11px] text-slate-400">Trigger: {selectedTask.trigger_reason}</p>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Confidence</div>
                  <div className="text-xs font-mono font-bold text-amber-400">
                    {(selectedTask.confidence_score * 100).toFixed(1)}%
                  </div>
                </div>
              </div>

              {/* Draft Answer */}
              <div className="space-y-2">
                <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                  Draft Generated Text
                </label>
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 font-serif text-slate-200 text-xs leading-relaxed whitespace-pre-wrap">
                  {selectedTask.draft_answer}
                </div>
              </div>

              {/* Supporting Passages */}
              {selectedTask.citations && selectedTask.citations.length > 0 && (
                <div className="space-y-2">
                  <label className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block">
                    Cited Evidence Passages ({selectedTask.citations.length})
                  </label>
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {selectedTask.citations.map((c: any, i: number) => (
                      <div key={i} className="p-3 rounded-lg bg-black/30 border border-slate-800 text-[11px] font-serif text-slate-300">
                        <span className="font-sans font-semibold text-amber-400 text-[10px] block mb-1">
                          {c.document_name} • Page {c.page_number}
                        </span>
                        "{c.quote_snippet}"
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Reviewer Audit Decision Form */}
              <div className="space-y-3 pt-3 border-t border-slate-800">
                <label className="text-xs font-semibold text-slate-200 block">
                  Reviewer Audit Notes & Justification <span className="text-rose-400">*</span>
                </label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Enter detailed reviewer rationale (e.g. 'Verified against amendment terms in Exhibit B; indemnity is acceptable.')..."
                  className="w-full bg-[#070C18] border border-slate-700 rounded-xl p-3 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-500 transition-colors h-24"
                />

                <div className="flex flex-wrap gap-3 justify-end pt-2">
                  <button
                    onClick={() => handleDecision('REJECTED')}
                    disabled={submitting}
                    className="px-4 py-2 rounded-xl bg-rose-950/60 hover:bg-rose-900/80 text-rose-300 border border-rose-800 text-xs font-medium flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-colors"
                  >
                    <XCircle className="w-3.5 h-3.5" />
                    <span>Reject & Discard</span>
                  </button>

                  <button
                    onClick={() => handleDecision('REVISION_REQUESTED')}
                    disabled={submitting}
                    className="px-4 py-2 rounded-xl bg-purple-950/60 hover:bg-purple-900/80 text-purple-300 border border-purple-800 text-xs font-medium flex items-center gap-1.5 cursor-pointer disabled:opacity-50 transition-colors"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Request Revision</span>
                  </button>

                  <button
                    onClick={() => handleDecision('APPROVED')}
                    disabled={submitting}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-400 hover:to-emerald-500 text-slate-950 text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-emerald-500/10 cursor-pointer disabled:opacity-50 transition-all"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                    <span>Approve & Finalize</span>
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="legal-card p-16 text-center text-xs text-slate-400 space-y-2">
              <UserCheck className="w-10 h-10 mx-auto text-slate-400 opacity-50" />
              <p>Select a review task from the left list to inspect evidence and submit a sign-off decision.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
