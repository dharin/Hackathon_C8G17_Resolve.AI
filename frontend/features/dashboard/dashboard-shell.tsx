"use client";

import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { AlertCircle, MousePointerClick, UploadCloud } from "lucide-react";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { IncidentList } from "@/components/incident-list";
import { IncidentDetails } from "@/components/incident-details";
import { computeWorkflowSteps } from "@/lib/workflow-steps";
import {
  AnalysisError,
  getAnalysisIncidents,
  getIncidentDetail,
} from "@/services/analysis-service";
import type { IncidentDetail, LogIssue } from "@/types/analysis";

export function DashboardShell() {
  const analysisId = useSearchParams().get("analysis");
  const { getToken } = useAuth();

  const [incidents, setIncidents] = useState<LogIssue[] | null>(null);
  const [incidentsError, setIncidentsError] = useState<string | null>(null);
  const [loadingIncidents, setLoadingIncidents] = useState(false);
  const [retryCount, setRetryCount] = useState(0);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<IncidentDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    if (!analysisId) {
      setIncidents(null);
      setIncidentsError(null);
      return;
    }

    let cancelled = false;
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
  }, [analysisId, getToken, retryCount]);

  useEffect(() => {
    if (!analysisId || !selectedId) {
      setDetail(null);
      return;
    }

    let cancelled = false;
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

  const retry = useCallback(() => setRetryCount((n) => n + 1), []);

  if (!analysisId) {
    return (
      <div className="flex flex-1 items-center justify-center p-4 sm:p-6">
        <Empty className="max-w-md border border-dashed">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <UploadCloud />
            </EmptyMedia>
            <EmptyTitle>No log analyzed yet</EmptyTitle>
            <EmptyDescription>
              Upload an application log to detect incidents and start an
              analysis.
            </EmptyDescription>
          </EmptyHeader>
          <Button
            nativeButton={false}
            render={<a href="/upload-logs" />}
            className="mt-2 w-fit"
          >
            <UploadCloud data-icon="inline-start" />
            Upload Logs
          </Button>
        </Empty>
      </div>
    );
  }

  if (incidentsError) {
    return (
      <div className="flex flex-1 items-center justify-center p-4 sm:p-6">
        <div className="flex w-full max-w-md flex-col gap-3">
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>Couldn&apos;t load incidents</AlertTitle>
            <AlertDescription>{incidentsError}</AlertDescription>
          </Alert>
          <Button variant="outline" className="w-fit" onClick={retry}>
            Try again
          </Button>
        </div>
      </div>
    );
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
              incident={selectedIncident}
              detail={detail}
              loadingDetail={loadingDetail}
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
