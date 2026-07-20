const STORAGE_KEY = "resolve-ai:active-analysis-id";

/** Persists the Dashboard's active analysis across navigation within the
 * same browser session (sessionStorage, not localStorage) — cleared on sign
 * out and naturally replaced the moment a new log is uploaded and analyzed.
 */
export function getPersistedAnalysisId(): string | null {
  if (typeof window === "undefined") return null;
  return window.sessionStorage.getItem(STORAGE_KEY);
}

export function setPersistedAnalysisId(analysisId: string): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(STORAGE_KEY, analysisId);
}

export function clearPersistedAnalysisId(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(STORAGE_KEY);
}
