// Mirrors backend/models/*.py response shapes exactly (snake_case, as sent
// over the wire) — no mapping layer, so drift between frontend and backend
// is a type error, not a silent bug.

import type { Severity, SourceType } from "@/types/incident";

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

// A ranked, source-attributed retrieval result — mirrors
// backend/rag/models.py::RetrievedChunk exactly.
export interface RetrievedChunk {
  chunk_id: string;
  content: string;
  score: number;
  source_type: SourceType;
  title: string;
  source_uri: string;
  section_path: string[];
  updated_at: string | null;
  metadata: Record<string, unknown>;
}

export interface Recommendation {
  title: string;
  confidence: number;
  rationale: string;
  sources: RetrievedChunk[];
}

export interface JiraPayload {
  incident_id: string;
  summary: string;
  description: string;
  priority: string;
  issue_type: string;
  labels: string[];
}

// Populated automatically for CRITICAL incidents, or after a manual
// POST .../create-jira call for non-critical ones — see
// backend/api/analyze.py::get_incident_detail and backend/api/jira.py.
export interface JiraTicketReference {
  key: string;
  url: string;
  created_at: string;
}

// Populated automatically, only for CRITICAL incidents, and only once
// `jira_ticket` exists — never before or independently of it. See
// backend/api/analyze.py::get_incident_detail and backend/api/slack.py.
export interface SlackNotificationReference {
  channel_id: string;
  message_ts: string;
  permalink: string | null;
  sent_at: string;
}

// Every entry here is extracted verbatim from a recommendation's own
// retrieved source content — never generated — see
// backend/agents/cookbook.py.
export interface Cookbook {
  root_cause: string;
  steps: string[];
  commands: string[];
  validation: string[];
  rollback: string[];
}

export interface IncidentDetail {
  incident: LogIssue;
  rca: RCAReport | null;
  recommendations: Recommendation[] | null;
  cookbook: Cookbook | null;
  jira_ticket: JiraTicketReference | null;
  slack_notification: SlackNotificationReference | null;
}
