import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { CitationInspectorModal } from './components/CitationInspectorModal';
import { DashboardView } from './views/DashboardView';
import { ResearchView } from './views/ResearchView';
import { DocumentsView } from './views/DocumentsView';
import { ContractAnalysisView } from './views/ContractAnalysisView';
import { ReviewQueueView } from './views/ReviewQueueView';
import { EvaluationView } from './views/EvaluationView';
import { AuthModal } from './views/AuthModal';
import { ApiClient } from './api/client';
import { UserProfile, DocumentItem, ReviewTaskItem, CitationItem } from './types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [user, setUser] = useState<UserProfile | null>(null);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [reviews, setReviews] = useState<ReviewTaskItem[]>([]);
  const [inspectedCitation, setInspectedCitation] = useState<CitationItem | null>(null);

  // Initial load
  const loadProfile = async () => {
    if (!ApiClient.getToken()) return;
    try {
      const u = await ApiClient.get<UserProfile>('/auth/me');
      setUser(u);
    } catch {
      ApiClient.setToken(null);
      setUser(null);
    }
  };

  const loadDocuments = async () => {
    try {
      const res: any = await ApiClient.get('/documents');
      setDocuments(res.items || []);
    } catch {
      // Seed default demonstration documents for rich preview
      setDocuments([
        {
          id: 'doc-demo-01',
          workspace_id: 'ws-demo',
          title: 'Master Services Agreement (Apex v Counterparty)',
          filename: 'Master_Services_Agreement_2025.pdf',
          file_size: 412900,
          content_hash: '9f83a4c2e817456d98213b7a1e05d2f8314e912c4b',
          page_count: 14,
          status: 'INDEXED',
          classification: 'MSA',
          created_at: new Date(Date.now() - 86400000 * 2).toISOString(),
        },
        {
          id: 'doc-demo-02',
          workspace_id: 'ws-demo',
          title: 'Mutual Non-Disclosure Agreement (Exhibit A)',
          filename: 'Mutual_NDA_Bilateral.pdf',
          file_size: 154200,
          content_hash: '3e12c8b9d04f71a56291e843c09b2a7516d4e928a3',
          page_count: 5,
          status: 'INDEXED',
          classification: 'NDA',
          created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
        },
        {
          id: 'doc-demo-03',
          workspace_id: 'ws-demo',
          title: 'Counterparty Revised Redline Draft v2',
          filename: 'MSA_Amendment_Redline_v2.pdf',
          file_size: 421000,
          content_hash: '7a41d9c02e1b8543f987216a4c03b1e9842f1a78c9',
          page_count: 15,
          status: 'INDEXED',
          classification: 'MSA',
          created_at: new Date().toISOString(),
        },
      ]);
    }
  };

  const loadReviews = async () => {
    try {
      const res: any = await ApiClient.get('/reviews');
      setReviews(res.tasks || []);
    } catch {
      // Seed pending review for demonstration
      setReviews([
        {
          id: 'rev-demo-01',
          run_id: 'run-demo-01',
          query: 'What is the liability cap under the amended agreement?',
          trigger_reason: 'Contradictory evidence: 1x fee cap in master vs 3x fee cap in proposed amendment.',
          status: 'PENDING',
          created_at: new Date().toISOString(),
        },
      ]);
    }
  };

  useEffect(() => {
    loadProfile();
    loadDocuments();
    loadReviews();
  }, []);

  const handleLogout = () => {
    ApiClient.setToken(null);
    setUser(null);
  };

  return (
    <div className="min-h-screen bg-[#070C18] text-slate-100 flex flex-col font-sans">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        user={user}
        onOpenAuth={() => setAuthModalOpen(true)}
        onLogout={handleLogout}
        reviewCount={reviews.filter((r) => r.status === 'PENDING').length}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === 'dashboard' && (
          <DashboardView
            documents={documents}
            reviews={reviews}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}
        {activeTab === 'research' && (
          <ResearchView
            onInspectCitation={(cit) => setInspectedCitation(cit)}
          />
        )}
        {activeTab === 'documents' && (
          <DocumentsView
            documents={documents}
            onRefresh={loadDocuments}
          />
        )}
        {activeTab === 'analysis' && (
          <ContractAnalysisView
            documents={documents}
          />
        )}
        {activeTab === 'reviews' && (
          <ReviewQueueView
            reviews={reviews}
            onRefresh={loadReviews}
          />
        )}
        {activeTab === 'evaluations' && (
          <EvaluationView />
        )}
      </main>

      {/* Global Citation Inspector Modal */}
      <CitationInspectorModal
        citation={inspectedCitation}
        onClose={() => setInspectedCitation(null)}
      />

      {/* Global Auth Modal */}
      <AuthModal
        isOpen={authModalOpen}
        onClose={() => setAuthModalOpen(false)}
        onSuccess={(u) => {
          setUser(u);
          loadDocuments();
          loadReviews();
        }}
      />
    </div>
  );
};
