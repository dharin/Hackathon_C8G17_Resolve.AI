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
import type { RCAReport } from "@/types/incident";

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

export function RcaPanel({ rca }: { rca: RCAReport | null }) {
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
          <CardAction>
            <ConfidenceMeter value={rca.confidence} />
          </CardAction>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground/90">{rca.primaryCause}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Evidence</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-col gap-1.5">
            {rca.evidence.map((item) => (
              <li
                key={item}
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
          {rca.alternativeCauses.length === 0 ? (
            <p className="text-sm text-muted-foreground">None identified.</p>
          ) : (
            <ul className="flex flex-col gap-1.5 text-sm text-foreground/80">
              {rca.alternativeCauses.map((item) => (
                <li key={item} className="flex gap-2">
                  <span className="text-muted-foreground">–</span>
                  {item}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
