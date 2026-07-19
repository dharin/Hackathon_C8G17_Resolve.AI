import { SearchX } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardAction,
} from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import type { RCAReport } from "@/types/analysis";

function ConfidenceMeter({ value }: { value: number }) {
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-primary"
          style={{ width: `${Math.round(value * 100)}%` }}
        />
      </div>
      <span className="text-xs font-medium text-muted-foreground">
        {Math.round(value * 100)}%
      </span>
    </div>
  );
}

function RcaPanelSkeleton() {
  return (
    <div className="flex flex-col gap-5">
      <Skeleton className="h-24 rounded-2xl" />
      <Skeleton className="h-32 rounded-2xl" />
      <Skeleton className="h-24 rounded-2xl" />
    </div>
  );
}

export function RcaPanel({
  rca,
  loading = false,
}: {
  rca: RCAReport | null;
  loading?: boolean;
}) {
  if (loading) {
    return <RcaPanelSkeleton />;
  }

  if (!rca) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <SearchX />
          </EmptyMedia>
          <EmptyTitle>No RCA yet</EmptyTitle>
          <EmptyDescription>
            Root cause analysis has not been generated for this incident.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Primary Cause</CardTitle>
          <CardAction className="flex items-center gap-2">
            <Badge variant="secondary" className="capitalize">
              {rca.method}
            </Badge>
            <ConfidenceMeter value={rca.confidence} />
          </CardAction>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground/90">{rca.primary_cause}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidence</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-1.5">
            {rca.evidence.map((item, index) => (
              <li
                key={`${index}-${item}`}
                className="rounded-lg bg-muted px-3 py-2 font-mono text-xs text-foreground/80"
              >
                {item}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Alternative Causes</CardTitle>
        </CardHeader>
        <CardContent>
          {rca.alternative_causes.length === 0 ? (
            <p className="text-sm text-muted-foreground">None identified.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {rca.alternative_causes.map((alt, index) => (
                <li key={`${index}-${alt.cause}`} className="flex flex-col gap-1">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-sm text-foreground/80">
                      {alt.cause}
                    </span>
                    <span className="shrink-0 text-xs font-medium text-muted-foreground">
                      {Math.round(alt.confidence * 100)}%
                    </span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
