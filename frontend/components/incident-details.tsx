import { FileSearch } from "lucide-react";
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
import { SeverityBadge } from "@/components/severity-badge";
import { RcaPanel } from "@/components/rca-panel";
import { RecommendationCard } from "@/components/recommendation-card";
import { CookbookPanel } from "@/components/cookbook-panel";
import { BottomActionPanel } from "@/components/bottom-action-panel";
import type { Incident } from "@/types/incident";

const LOG_LEVEL_STYLES: Record<string, string> = {
  INFO: "text-muted-foreground",
  WARN: "text-amber-600 dark:text-amber-400",
  ERROR: "text-red-600 dark:text-red-400",
  FATAL: "text-red-700 dark:text-red-300 font-semibold",
};

export function IncidentDetails({ incident }: { incident: Incident }) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-border bg-card/50">
      <div className="border-b border-border p-4">
        <div className="flex flex-wrap items-start justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold">{incident.title}</h2>
            <p className="mt-1 text-xs text-muted-foreground">
              {incident.metadata.incidentId} · {incident.service} ·{" "}
              {formatFullTimestamp(incident.timestamp)}
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
                  {incident.overview}
                </p>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Category
                    </dt>
                    <dd className="font-medium capitalize">
                      {incident.category}
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
                    <dt className="text-xs text-muted-foreground">
                      Environment
                    </dt>
                    <dd className="font-medium">
                      {incident.metadata.environment}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Region</dt>
                    <dd className="font-medium">{incident.metadata.region}</dd>
                  </div>
                </dl>
              </div>
            </TabsContent>

            <TabsContent value="rca" className="mt-0">
              <RcaPanel rca={incident.rca} />
            </TabsContent>

            <TabsContent value="recommendations" className="mt-0">
              {incident.recommendations.length === 0 ? (
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
                  {incident.recommendations.map((recommendation) => (
                    <RecommendationCard
                      key={recommendation.id}
                      recommendation={recommendation}
                    />
                  ))}
                </div>
              )}
            </TabsContent>

            <TabsContent value="cookbook" className="mt-0">
              <CookbookPanel cookbook={incident.cookbook} />
            </TabsContent>

            <TabsContent value="logs" className="mt-0">
              <div className="flex flex-col gap-1 rounded-2xl border border-border bg-card p-4 font-mono text-xs">
                {incident.logs.map((log, index) => (
                  <div
                    key={`${log.timestamp}-${index}`}
                    className="flex gap-3"
                  >
                    <span className="shrink-0 text-muted-foreground">
                      {log.timestamp}
                    </span>
                    <span
                      className={`shrink-0 ${LOG_LEVEL_STYLES[log.level]}`}
                    >
                      {log.level}
                    </span>
                    <span className="text-foreground/80">{log.message}</span>
                  </div>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="metadata" className="mt-0">
              <div className="rounded-2xl border border-border bg-card p-4">
                <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Incident ID
                    </dt>
                    <dd className="font-medium">
                      {incident.metadata.incidentId}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Detected By
                    </dt>
                    <dd className="font-medium">
                      {incident.metadata.detectedBy}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">
                      Affected Hosts
                    </dt>
                    <dd className="font-medium">
                      {incident.metadata.affectedHosts.join(", ")}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Tags</dt>
                    <dd className="flex flex-wrap gap-1.5">
                      {incident.metadata.tags.map((tag) => (
                        <Badge key={tag} variant="secondary">
                          {tag}
                        </Badge>
                      ))}
                    </dd>
                  </div>
                </dl>
              </div>
            </TabsContent>
          </div>
        </ScrollArea>
      </Tabs>

      <div className="border-t border-border p-3">
        <BottomActionPanel incident={incident} />
      </div>
    </div>
  );
}
