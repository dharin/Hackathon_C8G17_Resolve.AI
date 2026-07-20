"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { MousePointerClick } from "lucide-react";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { IncidentList } from "@/components/incident-list";
import { IncidentDetails } from "@/components/incident-details";
import { computeWorkflowSteps } from "@/lib/workflow-steps";
import {
  clearPersistedAnalysisId,
  getPersistedAnalysisId,
  setPersistedAnalysisId,
} from "@/lib/analysis-session";
import {
  AnalysisError,
  getAnalysisIncidents,
  getIncidentDetail,
} from "@/services/analysis-service";
import type { IncidentDetail, JiraTicketReference, LogIssue } from "@/types/analysis";

export function DashboardShell() {
  const router = useRouter();
  const urlAnalysisId = useSearchParams().get("analysis");
  const { getToken } = useAuth();

  // Mirrors the URL's `analysis` param, but survives navigating away and
  // back (e.g. to another sidebar item) via sessionStorage — see
  // lib/analysis-session.ts. Starts equal to the URL param (matches SSR;
  // sessionStorage is only ever consulted client-side, in the effect below,
  // to avoid a hydration mismatch).
  const [analysisId, setAnalysisId] = useState<string | null>(urlAnalysisId);
  // True once the sessionStorage restore below has actually run — until
  // then, `!analysisId` doesn't yet mean "nothing to show", it might just
  // mean restoration hasn't happened yet (see the redirect effect further
  // down, which is gated on this).
  const [resolved, setResolved] = useState(false);

  useEffect(() => {
    // Same documented "sync with an external system" pattern as the
    // fetch effects below (URL / sessionStorage here, rather than a
    // network request) — see their comment for the rule this suppresses.
    if (urlAnalysisId) {
      setPersistedAnalysisId(urlAnalysisId);
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setAnalysisId(urlAnalysisId);
      setResolved(true);
      return;
    }
    const persisted = getPersistedAnalysisId();
    if (persisted) {
      // Restore into the URL too, so refresh/copy-link keep working.
      router.replace(`/?analysis=${persisted}`, { scroll: false });
      setAnalysisId(persisted);
    } else {
      setAnalysisId(null);
    }
    setResolved(true);
  }, [urlAnalysisId, router]);

  const [incidents, setIncidents] = useState<LogIssue[] | null>(null);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);
  const [loadingIncidents, setLoadingIncidents] = useState(false);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<IncidentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    // Nothing to fetch — the component renders its own "no analysis yet"
    // state directly from `analysisId` below, without needing `incidents`.
    if (!analysisId) return;

    let cancelled = false;
    // This is React's own documented "fetch on mount/dependency change"
    // pattern (see "You Might Not Need an Effect" > Fetching data) — the
    // synchronous setState here starts the loading state before the async
    // fetch below resolves; there's no Suspense/data-library in this repo
    // to express it declaratively instead.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoadingIncidents(true);
    setIncidentsError(null);

    (async () => {
      try {
        const token = await getToken();
        const result = await getAnalysisIncidents(analysisId, token);
        if (cancelled) return;
        setIncidents(result);
        setSelectedId(result[0]?.id ?? null);
      } catch (err) {
        if (cancelled) return;
        setIncidents(null);
        setIncidentsError(
          err instanceof AnalysisError
            ? err.message
            : "Failed to load incidents.",
        );
      } finally {
        if (!cancelled) setLoadingIncidents(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [analysisId, getToken]);

  useEffect(() => {
    // Dashboard is locked behind having a *working* analysis — no inline
    // "no analysis" / "couldn't load" states to click past. Once
    // restoration has actually run (see `resolved` above) and there's
    // still nothing usable — never uploaded, or a stale/expired analysis
    // id that failed to load — send the user to upload a log instead.
    if (!resolved) return;
    if (analysisId && !incidentsError) return;

    clearPersistedAnalysisId();
    router.replace("/upload-logs");
  }, [resolved, analysisId, incidentsError, router]);

  useEffect(() => {
    // Nothing to fetch — `selectedIncident` (derived below) is undefined
    // without a `selectedId`, so `detail` never gets read in that case.
    if (!analysisId || !selectedId) return;

    let cancelled = false;
    // Same documented pattern as the incidents effect above.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setLoadingDetail(true);
    setDetail(null);

    (async () => {
      try {
        const token = await getToken();
        const result = await getIncidentDetail(
          analysisId,
          selectedId,
          token,
        );
        if (!cancelled) setDetail(result);
      } catch {
        // Detail (RCA) failing to load shouldn't block viewing the
        // incident itself — the RCA tab just shows its own error state.
        if (!cancelled) setDetail(null);
      } finally {
        if (!cancelled) setLoadingDetail(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [analysisId, selectedId, getToken]);

  const handleTicketCreated = useCallback((ticket: JiraTicketReference) => {
    setDetail((prev) => (prev ? { ...prev, jira_ticket: ticket } : prev));
  }, []);

  // Either still resolving (brief, see `resolved` above), or the redirect
  // effect above is on its way to /upload-logs — nothing valid to show
  // either way, so render nothing rather than flash stale/wrong UI.
  if (!resolved || !analysisId || incidentsError) {
    return null;
  }

  if (loadingIncidents || incidents === null) {
    return (
      <div className="flex min-h-0 flex-1 flex-col gap-4 p-4 sm:p-6">
        <Skeleton className="h-14 w-full rounded-2xl" />
        <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[360px_1fr]">
          <Skeleton className="min-h-[420px] rounded-2xl lg:min-h-0" />
          <Skeleton className="min-h-[520px] rounded-2xl lg:min-h-0" />
        </div>
      </div>
    );
  }

  const selectedIncident = incidents.find(
    (incident) => incident.id === selectedId,
  );

  const workflowSteps = selectedIncident
    ? computeWorkflowSteps({
        hasRca: Boolean(detail?.rca),
        remediationRan: detail?.recommendations != null,
        hasCookbook: Boolean(detail?.cookbook),
        notified: Boolean(detail?.jira_ticket) || Boolean(detail?.slack_notification),
        loadingDetail,
      })
    : null;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 p-4 sm:p-6">
      {workflowSteps && <WorkflowStepper steps={workflowSteps} />}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[360px_1fr]">
        <div className="min-h-[420px] lg:min-h-0">
          <IncidentList
            incidents={incidents}
            selectedId={selectedId}
            analyzingId={loadingDetail ? selectedId : null}
            onSelect={setSelectedId}
          />
        </div>
        <div className="min-h-[520px] lg:min-h-0">
          {incidents.length === 0 ? (
            <Empty className="h-full border border-dashed">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <MousePointerClick />
                </EmptyMedia>
                <EmptyTitle>No incidents detected</EmptyTitle>
                <EmptyDescription>
                  This log didn&apos;t contain any recognizable incidents.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          ) : selectedIncident ? (
            <IncidentDetails
              analysisId={analysisId}
              incident={selectedIncident}
              detail={detail}
              loadingDetail={loadingDetail}
              onTicketCreated={handleTicketCreated}
            />
          ) : (
            <Empty className="h-full border border-dashed">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <MousePointerClick />
                </EmptyMedia>
                <EmptyTitle>No incident selected</EmptyTitle>
                <EmptyDescription>
                  Select an incident from the list to view its analysis.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </div>
      </div>
    </div>
  );
}
