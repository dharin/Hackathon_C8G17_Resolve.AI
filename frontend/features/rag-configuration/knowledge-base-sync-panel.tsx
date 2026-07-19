"use client";

import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { AlertCircle, CheckCircle2, Loader2, RefreshCw } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatFullTimestamp } from "@/lib/format-date";
import { RagError, getRagSyncStatus, syncKnowledgeBase } from "@/services/rag-service";
import type { RagSyncResult } from "@/types/rag";

const SOURCE_LABEL: Record<string, string> = {
  confluence: "Confluence",
  local_sop: "Local SOP",
};

export function KnowledgeBaseSyncPanel() {
  const { getToken } = useAuth();
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastResult, setLastResult] = useState<RagSyncResult | null>(null);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      try {
        const token = await getToken();
        const status = await getRagSyncStatus(token);
        if (!cancelled) setLastSyncedAt(status.last_synced_at);
      } catch {
        // Leave last-synced-at unknown rather than blocking the page —
        // the button below still works regardless.
      } finally {
        if (!cancelled) setLoadingStatus(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const handleSync = useCallback(async () => {
    const previousSyncedAt = lastSyncedAt;
    setSyncing(true);
    setError(null);

    try {
      const token = await getToken();
      const result = await syncKnowledgeBase(token);
      setLastResult(result);

      if (result.errors.length > 0) {
        // The backend already leaves last_synced_at at its previous value
        // when a source fails outright — reflect that (the "rollback"),
        // not the in-flight optimistic state.
        setLastSyncedAt(result.last_synced_at);
        setError(result.errors.join("; "));
      } else {
        setLastSyncedAt(result.last_synced_at);
      }
    } catch (err) {
      // The request itself failed (network/500) — roll back to whatever
      // was last known good rather than show a stale "success".
      setLastSyncedAt(previousSyncedAt);
      setError(err instanceof RagError ? err.message : "Sync failed.");
    } finally {
      setSyncing(false);
    }
  }, [getToken, lastSyncedAt]);

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs text-muted-foreground">Last synced</p>
            {loadingStatus ? (
              <Skeleton className="mt-1 h-5 w-40" />
            ) : (
              <p className="text-sm font-medium">
                {lastSyncedAt ? formatFullTimestamp(lastSyncedAt) : "Never synced"}
              </p>
            )}
          </div>
          <Button disabled={syncing} onClick={handleSync}>
            {syncing ? (
              <>
                <Loader2 data-icon="inline-start" className="animate-spin" />
                Updating…
              </>
            ) : (
              <>
                <RefreshCw data-icon="inline-start" />
                Update Knowledgebase
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Alert variant="destructive">
          <AlertCircle />
          <AlertTitle>Knowledge base sync failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {!error && lastResult && (
        <Alert>
          <CheckCircle2 className="text-primary" />
          <AlertTitle>Knowledge base updated</AlertTitle>
          <AlertDescription>
            <ul className="flex flex-col gap-0.5">
              {lastResult.summaries.map((summary) => (
                <li key={summary.source_type}>
                  {SOURCE_LABEL[summary.source_type] ?? summary.source_type}:{" "}
                  {summary.documents_indexed} indexed,{" "}
                  {summary.documents_skipped_unchanged} unchanged
                  {summary.documents_failed > 0 &&
                    `, ${summary.documents_failed} failed`}
                </li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}
    </div>
  );
}
