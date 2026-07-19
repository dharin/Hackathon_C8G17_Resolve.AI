// Mirrors backend/rag/models.py::SourceSyncSummary and
// backend/models/rag_sync_result.py exactly (snake_case, as sent over the
// wire).

import type { SourceType } from "@/types/incident";

export interface SourceSyncSummary {
  source_type: SourceType;
  documents_discovered: number;
  documents_indexed: number;
  documents_skipped_unchanged: number;
  documents_marked_unavailable: number;
  documents_failed: number;
  errors: string[];
}

export interface RagSyncStatus {
  last_synced_at: string | null;
}

export interface RagSyncResult {
  summaries: SourceSyncSummary[];
  last_synced_at: string | null;
  errors: string[];
}
