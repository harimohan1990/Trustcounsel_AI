import React, { useState } from 'react';
import { 
  FileText, 
  Upload, 
  Trash2, 
  CheckCircle, 
  Clock, 
  AlertTriangle, 
  FileCheck, 
  Hash,
  RefreshCw
} from 'lucide-react';
import { ApiClient } from '../api/client';
import { DocumentItem } from '../types';

interface DocumentsViewProps {
  documents: DocumentItem[];
  onRefresh: () => void;
}

export const DocumentsView: React.FC<DocumentsViewProps> = ({ documents, onRefresh }) => {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', file);
    formData.append('title', file.name.replace(/\.[^/.]+$/, ''));
    formData.append('classification', 'GENERAL_CONTRACT');

    try {
      await ApiClient.post('/documents', formData, false);
      setSuccess(`"${file.name}" uploaded and indexed successfully.`);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to upload document.');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (docId: string, filename: string) => {
    if (!confirm(`Are you sure you want to delete "${filename}" and its vector index?`)) return;
    try {
      await ApiClient.delete(`/documents/${docId}`);
      onRefresh();
    } catch (err: any) {
      setError(err.message || 'Failed to delete document.');
    }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-200">
      {/* Header and Upload Dropzone */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-800">
        <div>
          <h2 className="text-xl font-serif font-bold text-white">Document Vault & Ingestion Pipeline</h2>
          <p className="text-xs text-slate-400">
            Upload legal instruments for text extraction, chunking, and hybrid vector indexing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onRefresh}
            className="p-2 rounded-xl bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-white transition-colors"
            title="Refresh documents"
          >
            <RefreshCw className="w-4 h-4" />
          </button>

          <label className="flex items-center gap-2 px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-semibold text-xs shadow-md shadow-amber-500/10 cursor-pointer transition-all">
            <Upload className="w-4 h-4" />
            <span>{uploading ? 'Indexing Document...' : 'Upload Contract (PDF/TXT)'}</span>
            <input
              type="file"
              accept=".pdf,.txt,.md"
              onChange={handleFileUpload}
              disabled={uploading}
              className="hidden"
            />
          </label>
        </div>
      </div>

      {/* Notifications */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-950/40 border border-rose-800/60 text-xs text-rose-300 flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="p-4 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-xs text-emerald-300 flex items-center gap-2">
          <CheckCircle className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* Document Table */}
      <div className="legal-card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#111D36]/80 border-b border-slate-800 text-slate-400 uppercase font-medium">
              <tr>
                <th className="px-6 py-3.5">Instrument / Filename</th>
                <th className="px-6 py-3.5">Classification</th>
                <th className="px-6 py-3.5">Status</th>
                <th className="px-6 py-3.5">Pages</th>
                <th className="px-6 py-3.5">Content Hash</th>
                <th className="px-6 py-3.5">Uploaded</th>
                <th className="px-6 py-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {documents.length > 0 ? (
                documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-slate-900/40 transition-colors">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-200">{doc.title || doc.filename}</div>
                          <div className="text-[11px] text-slate-400">{doc.filename} • {(doc.file_size / 1024).toFixed(1)} KB</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-[10px] text-slate-300 border border-slate-700">
                        {doc.classification}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {doc.status === 'INDEXED' ? (
                        <span className="badge-verified">
                          <CheckCircle className="w-3 h-3" /> Indexed
                        </span>
                      ) : doc.status === 'PROCESSING' ? (
                        <span className="badge-gold">
                          <Clock className="w-3 h-3 animate-spin" /> Processing
                        </span>
                      ) : (
                        <span className="badge-unsupported">
                          <AlertTriangle className="w-3 h-3" /> Failed
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-slate-300">{doc.page_count || 1}</td>
                    <td className="px-6 py-4 font-mono text-[10px] text-slate-400">
                      {doc.content_hash.slice(0, 12)}...
                    </td>
                    <td className="px-6 py-4 text-slate-400">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={() => handleDelete(doc.id, doc.filename)}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-950/30 transition-colors cursor-pointer"
                        title="Delete Document"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="px-6 py-16 text-center text-slate-400">
                    <FileCheck className="w-10 h-10 mx-auto text-slate-400 mb-2 opacity-50" />
                    <p className="font-medium text-slate-300">No documents indexed in active workspace</p>
                    <p className="text-[11px] text-slate-400 mt-1">Upload a PDF or TXT contract to start indexing.</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
