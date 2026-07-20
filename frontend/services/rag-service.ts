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

/** Opens a local SOP document (authenticated, unlike a Confluence source_uri
 * which is already a plain external URL) in a new browser tab.
 *
 * `newTab` must come from a `window.open()` call made synchronously inside
 * the click handler, before any `await` (e.g. `getToken()`) — once the
 * handler has awaited anything, a `window.open()` call is no longer tied to
 * the original user gesture and browsers silently block it as a popup. This
 * function only ever navigates an already-opened tab; it never opens one
 * itself, or the same bug just moves one call frame deeper.
 */
export async function openLocalSopDocument(
  relativePath: string,
  token: string | null,
  newTab: Window | null,
): Promise<void> {
  try {
    if (!newTab) {
      throw new RagError(
        "Pop-up blocked — allow pop-ups for this site to open documents.",
      );
    }

    const encodedPath = relativePath.split("/").map(encodeURIComponent).join("/");
    const response = await fetch(`${API_BASE_URL}/api/v1/rag/sops/${encodedPath}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
    });
    if (!response.ok) {
      throw new RagError(`Couldn't open document (status ${response.status}).`);
    }

    const blobUrl = URL.createObjectURL(await response.blob());
    newTab.location.href = blobUrl;
    // Revoked well after the new tab has had time to load the blob, rather
    // than immediately — revoking too early breaks that navigation.
    setTimeout(() => URL.revokeObjectURL(blobUrl), 60_000);
  } catch (err) {
    newTab?.close();
    throw err;
  }
}
