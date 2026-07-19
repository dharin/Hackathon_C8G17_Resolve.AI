import { BookX } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import type { Cookbook } from "@/types/incident";

function StepList({ items }: { items: string[] }) {
  return (
    <ol className="flex flex-col gap-1.5">
      {items.map((item, index) => (
        <li key={item} className="flex gap-2.5 text-sm text-foreground/90">
          <span className="flex size-5 shrink-0 items-center justify-center rounded-full bg-muted text-[11px] font-medium text-muted-foreground">
            {index + 1}
          </span>
          {item}
        </li>
      ))}
    </ol>
  );
}

export function CookbookPanel({ cookbook }: { cookbook: Cookbook | null }) {
  if (!cookbook) {
    return (
      <Empty className="border border-dashed">
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <BookX />
          </EmptyMedia>
          <EmptyTitle>No runbook yet</EmptyTitle>
          <EmptyDescription>
            A runbook has not been generated for this incident.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <Card>
        <CardHeader>
          <CardTitle>Root Cause</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-foreground/90">{cookbook.rootCause}</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recommended Steps</CardTitle>
        </CardHeader>
        <CardContent>
          <StepList items={cookbook.steps} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Executable Commands</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col gap-1.5">
            {cookbook.commands.map((command) => (
              <pre
                key={command}
                className="overflow-x-auto rounded-lg bg-muted px-3 py-2 font-mono text-xs text-foreground/80"
              >
                {command}
              </pre>
            ))}
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-5 sm:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Validation</CardTitle>
          </CardHeader>
          <CardContent>
            <StepList items={cookbook.validation} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Rollback</CardTitle>
          </CardHeader>
          <CardContent>
            <StepList items={cookbook.rollback} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
