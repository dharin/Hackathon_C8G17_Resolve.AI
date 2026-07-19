import { API_BASE_URL } from "@/lib/upload-config";
import type {
  IncidentDetail,
  JiraTicketReference,
  LogIssue,
  UploadAnalysisResult,
} from "@/types/analysis";

export class AnalysisError extends Error {}

async function request<T>(path: string, token: string | null): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "GET",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return handleResponse<T>(response);
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  const body: unknown = await response.json().catch(() => null);
  const detail =
    body && typeof body === "object" && "detail" in body
      ? String((body as { detail: unknown }).detail)
      : `Request failed with status ${response.status}.`;
  throw new AnalysisError(detail);
}

export async function analyzeLog(
  uploadId: string,
  token: string | null,
): Promise<UploadAnalysisResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/logs/${uploadId}/analyze`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    },
  );
  return handleResponse<UploadAnalysisResult>(response);
}

export function getAnalysisIncidents(
  analysisId: string,
  token: string | null,
): Promise<LogIssue[]> {
  return request<LogIssue[]>(
    `/api/v1/analyses/${analysisId}/incidents`,
    token,
  );
}

export function getIncidentDetail(
  analysisId: string,
  incidentId: string,
  token: string | null,
): Promise<IncidentDetail> {
  return request<IncidentDetail>(
    `/api/v1/analyses/${analysisId}/incidents/${incidentId}`,
    token,
  );
}

export async function createJiraTicket(
  analysisId: string,
  incidentId: string,
  token: string | null,
): Promise<JiraTicketReference> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/analyses/${analysisId}/incidents/${incidentId}/create-jira`,
    {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    },
  );
  return handleResponse<JiraTicketReference>(response);
}
