export type Severity = "critical" | "high" | "medium" | "low";

export type WorkflowStepId =
  | "log-reader"
  | "rca"
  | "remediation"
  | "cookbook"
  | "notification";

export type WorkflowStepStatus = "complete" | "current" | "pending";

export interface WorkflowStep {
  id: WorkflowStepId;
  label: string;
  status: WorkflowStepStatus;
}

// Only Confluence and the local SOP directory are in scope for the RAG
// pipeline (see project-spec.md "RAG Design" / Phase 6) — no Google Drive,
// no historical-incident source.
export type SourceType = "confluence" | "local_sop";

export interface SourceReference {
  id: string;
  title: string;
  type: SourceType;
  section: string;
  lastUpdated: string;
  url: string;
}

// Recommendation/Cookbook are still placeholder shapes for the UI built
// ahead of Phase 8/9 — no incident currently has real data for these, so
// IncidentDetails always passes an empty array / null until those phases
// introduce the real backend models.
export interface Recommendation {
  id: string;
  title: string;
  confidence: number;
  reason: string;
  sources: SourceReference[];
}

export interface Cookbook {
  rootCause: string;
  steps: string[];
  commands: string[];
  validation: string[];
  rollback: string[];
}
