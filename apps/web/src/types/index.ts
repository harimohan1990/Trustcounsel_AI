export interface UserProfile {
  id: string;
  email: string;
  full_name: string;
  role: 'ADMINISTRATOR' | 'RESEARCHER' | 'REVIEWER';
  workspace_id: string;
}

export interface DocumentItem {
  id: string;
  workspace_id: string;
  title: string;
  filename: string;
  file_size: number;
  content_hash: string;
  page_count: number;
  status: 'UPLOADED' | 'PROCESSING' | 'INDEXED' | 'FAILED';
  classification: string;
  error_message?: string;
  created_at: string;
}

export interface CitationItem {
  id: string;
  document_id: string;
  document_name: string;
  page_number: number;
  chunk_id: string;
  quote_snippet: string;
  verified: boolean;
}

export interface ClaimItem {
  id: string;
  claim_text: string;
  status: 'VERIFIED' | 'UNSUPPORTED' | 'CONTRADICTED';
  citation_ids: string[];
}

export interface ResearchResponse {
  run_id: string;
  session_id?: string;
  answer: string;
  claims: ClaimItem[];
  citations: CitationItem[];
  limitations: string[];
  confidence_score: number;
  status: 'COMPLETED' | 'ABSTAINED' | 'AWAITING_HUMAN_REVIEW';
  requires_review: boolean;
}

export interface ReviewTaskItem {
  id: string;
  run_id: string;
  query: string;
  trigger_reason: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVISION_REQUESTED';
  created_at: string;
}

export interface EvaluationRunSummary {
  run_id: string;
  model_identifier: string;
  recall_at_k: number;
  precision_at_k: number;
  mrr: number;
  ndcg: number;
  faithfulness_score: number;
  citation_precision: number;
  abstention_accuracy: number;
  p95_latency_ms: number;
  total_tokens: number;
  is_baseline: boolean;
  created_at: string;
}
