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

export interface RCAReport {
  primaryCause: string;
  evidence: string[];
  alternativeCauses: string[];
  confidence: number;
}

export type SourceType = "confluence" | "google-drive" | "historical-incident";

export interface SourceReference {
  id: string;
  title: string;
  type: SourceType;
  section: string;
  lastUpdated: string;
  url: string;
}

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

export interface LogLine {
  timestamp: string;
  level: "INFO" | "WARN" | "ERROR" | "FATAL";
  message: string;
}

export interface IncidentMetadata {
  incidentId: string;
  environment: string;
  region: string;
  affectedHosts: string[];
  detectedBy: string;
  tags: string[];
}

export interface Incident {
  id: string;
  title: string;
  service: string;
  timestamp: string;
  severity: Severity;
  category: string;
  confidence: number;
  overview: string;
  rca: RCAReport | null;
  recommendations: Recommendation[];
  cookbook: Cookbook | null;
  logs: LogLine[];
  metadata: IncidentMetadata;
  workflow: WorkflowStep[];
}
