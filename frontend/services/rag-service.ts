import { API_BASE_URL } from "@/lib/upload-config";
import type { RagSyncResult, RagSyncStatus } from "@/types/rag";

export class RagError extends Error {}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return (await response.json()) as T;
  }

  const body: unknown = await response.json().catch(() => null);
  const detail =
    body && typeof body === "object" && "detail" in body
      ? String((body as { detail: unknown }).detail)
      : `Request failed with status ${response.status}.`;
  throw new RagError(detail);
}

export async function getRagSyncStatus(
  token: string | null,
): Promise<RagSyncStatus> {
  const response = await fetch(`${API_BASE_URL}/api/v1/rag/status`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return handleResponse<RagSyncStatus>(response);
}

export async function syncKnowledgeBase(
  token: string | null,
): Promise<RagSyncResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/rag/sync`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
  return handleResponse<RagSyncResult>(response);
}
