// Mirrors backend/models/*.py response shapes exactly (snake_case, as sent
// over the wire) — no mapping layer, so drift between frontend and backend
// is a type error, not a silent bug.

import type { Severity } from "@/types/incident";

export type IssueCategory =
  | "oom_kill"
  | "disk_space_exhaustion"
  | "auth_failure"
  | "timeout"
  | "database_connection_error"
  | "http_5xx_spike"
  | "unknown";

export type DetectionMethod = "rule" | "llm" | "unclassified";

export interface LogIssue {
  id: string;
  category: IssueCategory;
  severity: Severity;
  title: string;
  service: string | null;
  timestamp: string | null;
  confidence: number;
  fields: Record<string, unknown>;
  raw_excerpt: string[];
  detection_method: DetectionMethod;
}

export interface UploadAnalysisResult {
  analysis_id: string;
  upload_id: string;
  created_at: string;
  total_lines: number;
  incidents: LogIssue[];
}

export interface AlternativeCause {
  cause: string;
  confidence: number;
  evidence: string[];
}

export interface RCAReport {
  incident_id: string;
  primary_cause: string;
  evidence: string[];
  alternative_causes: AlternativeCause[];
  confidence: number;
  generated_at: string;
  method: "llm" | "heuristic";
}

// `recommendations`/`cookbook` stay untyped placeholders until Phase 8/9
// introduce their real models — see backend/models/incident_detail.py.
export interface IncidentDetail {
  incident: LogIssue;
  rca: RCAReport | null;
  recommendations: unknown[] | null;
  cookbook: unknown | null;
}
