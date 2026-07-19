"use client";

import { Ticket, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Severity } from "@/types/incident";

export function BottomActionPanel({ severity }: { severity: Severity }) {
  const isCritical = severity === "critical";

  return (
    <div className="glass-surface sticky bottom-0 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border px-4 py-3">
      {isCritical ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">Critical incident —</span>
          <Badge variant="outline">
            <Ticket />
            Jira pending (Phase 10)
          </Badge>
          <Badge variant="outline">
            <MessageSquare />
            Slack pending (Phase 11)
          </Badge>
        </div>
      ) : (
        <span className="text-sm text-muted-foreground">
          Non-critical incident — Jira creation is manual.
        </span>
      )}

      {!isCritical && (
        <Button disabled title="Available once Phase 10 (Jira integration) is implemented">
          <Ticket data-icon="inline-start" />
          Create Jira Ticket
        </Button>
      )}
    </div>
  );
}
