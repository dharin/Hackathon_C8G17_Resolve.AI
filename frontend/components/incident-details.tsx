import { Compass, FileSearch } from "lucide-react";
import { formatFullTimestamp } from "@/lib/format-date";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { SeverityBadge } from "@/components/severity-badge";
import { RcaPanel } from "@/components/rca-panel";
import { RecommendationCard } from "@/components/recommendation-card";
import { CookbookPanel } from "@/components/cookbook-panel";
import { BottomActionPanel } from "@/components/bottom-action-panel";
import type { IncidentDetail, JiraTicketReference, LogIssue } from "@/types/analysis";

export function IncidentDetails({
  analysisId,
  incident,
  detail,
  loadingDetail,
  onTicketCreated,
}: {
  analysisId: string;
  incident: LogIssue;
  detail: IncidentDetail | null;
  loadingDetail: boolean;
  onTicketCreated: (ticket: JiraTicketReference) => void;
}) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-border bg-card/50">
      <div className="border-b border-border p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold">{incident.title}</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {incident.id.slice(0, 8)} · {incident.service ?? "Unknown service"} ·{" "}
              {incident.timestamp
                ? formatFullTimestamp(incident.timestamp)
                : "Unknown time"}
            </p>
          </div>
          <SeverityBadge severity={incident.severity} />
        </div>
      </div>

      <Tabs defaultValue="overview" className="flex min-h-0 flex-1 flex-col">
        <div className="border-b border-border px-4 pt-2">
          <TabsList className="h-auto flex-wrap justify-start gap-1 bg-transparent p-0">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="rca">RCA</TabsTrigger>
            <TabsTrigger value="recommendations">
              Recommended Steps
            </TabsTrigger>
            <TabsTrigger value="cookbook">Cookbook</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
            <TabsTrigger value="metadata">Metadata</TabsTrigger>
          </TabsList>
        </div>

        <ScrollArea className="min-h-0 flex-1">
          <div className="p-4">
            <TabsContent value="overview" className="mt-0">
              <div className="rounded-2xl border border-border bg-card p-4">
                <p className="text-sm text-foreground/90">
                  Detected via{" "}
                  <span className="font-medium">
                    {DETECTION_METHOD_LABEL[incident.detection_method]}
                  </span>{" "}
                  detection.
                </p>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Category
                    </dt>
                    <dd className="font-medium capitalize">
                      {incident.category.replaceAll("_", " ")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Confidence
                    </dt>
                    <dd className="font-medium">
                      {Math.round(incident.confidence * 100)}%
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Service</dt>
                    <dd className="font-medium">
                      {incident.service ?? "—"}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Occurrences
                    </dt>
                    <dd className="font-medium">
                      {typeof incident.fields.occurrences === "number"
                        ? incident.fields.occurrences
                        : 1}
                    </dd>
                  </div>
                </dl>
              </div>
            </TabsContent>

            <TabsContent value="rca" className="mt-0">
              <RcaPanel rca={detail?.rca ?? null} loading={loadingDetail} />
            </TabsContent>

            <TabsContent value="recommendations" className="mt-0">
              {loadingDetail ? (
                <div className="flex flex-col gap-3">
                  <Skeleton className="h-28 rounded-2xl" />
                  <Skeleton className="h-28 rounded-2xl" />
                </div>
              ) : !detail?.recommendations || detail.recommendations.length === 0 ? (
                <Empty className="border border-dashed">
                  <EmptyHeader>
                    <EmptyMedia variant="icon">
                      <FileSearch />
                    </EmptyMedia>
                    <EmptyTitle>No supporting documentation found</EmptyTitle>
                    <EmptyDescription>
                      No grounded remediation could be recommended for this
                      incident.
                    </EmptyDescription>
                  </EmptyHeader>
                </Empty>
              ) : (
                <div className="flex flex-col gap-3">
                  {detail.recommendations.map((recommendation) => (
                    <RecommendationCard
                      key={recommendation.sources[0]?.chunk_id ?? recommendation.title}
                      recommendation={recommendation}
                    />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="cookbook" className="mt-0">
              <CookbookPanel
                cookbook={detail?.cookbook ?? null}
                loading={loadingDetail}
              />
            </TabsContent>

            <TabsContent value="logs" className="mt-0">
              {incident.raw_excerpt.length === 0 ? (
                <Empty className="border border-dashed">
                  <EmptyHeader>
                    <EmptyMedia variant="icon">
                      <Compass />
                    </EmptyMedia>
                    <EmptyTitle>No log excerpt captured</EmptyTitle>
                  </EmptyHeader>
                </Empty>
              ) : (
                <div className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-4 font-mono text-xs">
                  {incident.raw_excerpt.map((line, index) => (
                    <div key={index} className="text-foreground/80">
                      {line}
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="metadata" className="mt-0">
              <div className="rounded-2xl border border-border bg-card p-4">
                <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Incident ID
                    </dt>
                    <dd className="font-mono text-xs font-medium">
                      {incident.id}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Detected By
                    </dt>
                    <dd className="font-medium">
                      {DETECTION_METHOD_LABEL[incident.detection_method]}
                    </dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="text-xs text-muted-foreground">
                      Extracted Fields
                    </dt>
                    <dd className="mt-1 flex flex-wrap gap-1.5">
                      {Object.entries(incident.fields).length === 0 ? (
                        <span className="text-sm text-muted-foreground">
                          None extracted.
                        </span>
                      ) : (
                        Object.entries(incident.fields).map(([key, value]) => (
                          <Badge key={key} variant="secondary">
                            {key}: {String(value)}
                          </Badge>
                        ))
                      )}
                    </dd>
                  </div>
                </dl>
              </div>
            </TabsContent>
          </div>
        </ScrollArea>
      </Tabs>

      <div className="border-t border-border p-3">
        <BottomActionPanel
          severity={incident.severity}
          analysisId={analysisId}
          incidentId={incident.id}
          jiraTicket={detail?.jira_ticket ?? null}
          slackNotification={detail?.slack_notification ?? null}
          onTicketCreated={onTicketCreated}
        />
      </div>
    </div>
  );
}

const DETECTION_METHOD_LABEL: Record<LogIssue["detection_method"], string> = {
  rule: "deterministic rule",
  llm: "LLM classifier",
  unclassified: "unclassified anomaly",
};
