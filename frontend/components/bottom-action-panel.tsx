"use client";

import { useState } from "react";
import { CheckCircle2, Ticket, MessageSquare } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { Incident } from "@/types/incident";

export function BottomActionPanel({ incident }: { incident: Incident }) {
  const [manualTicketCreated, setManualTicketCreated] = useState(false);
  const isCritical = incident.severity === "critical";
  const notificationSent =
    incident.workflow.find((s) => s.id === "notification")?.status ===
    "complete";

  return (
    <div className="glass-surface sticky bottom-0 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border px-4 py-3">
      {isCritical ? (
        <div className="flex flex-wrap items-center gap-2 text-sm">
          <span className="text-muted-foreground">Critical incident —</span>
          <Badge variant={notificationSent ? "secondary" : "outline"}>
            <Ticket />
            Jira {notificationSent ? "created automatically" : "pending"}
          </Badge>
          <Badge variant={notificationSent ? "secondary" : "outline"}>
            <MessageSquare />
            Slack {notificationSent ? "notified automatically" : "pending"}
          </Badge>
        </div>
      ) : (
        <span className="text-sm text-muted-foreground">
          Non-critical incident — Jira creation is manual.
        </span>
      )}

      {!isCritical && (
        <Button
          disabled={manualTicketCreated}
          onClick={() => setManualTicketCreated(true)}
        >
          {manualTicketCreated ? (
            <>
              <CheckCircle2 data-icon="inline-start" />
              Ticket created
            </>
          ) : (
            <>
              <Ticket data-icon="inline-start" />
              Create Jira Ticket
            </>
          )}
        </Button>
      )}
    </div>
  );
}
