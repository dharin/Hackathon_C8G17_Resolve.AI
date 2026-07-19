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
