"use client";

import { useState } from "react";
import { CheckCircle2, Ticket, MessageSquare } from "lucide-react";
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
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <span className="text-muted-foreground">Critical incident —</span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
              notificationSent
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <Ticket className="size-3.5" />
            Jira {notificationSent ? "created automatically" : "pending"}
          </span>
          <span
            className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${
              notificationSent
                ? "bg-primary/10 text-primary"
                : "bg-muted text-muted-foreground"
            }`}
          >
            <MessageSquare className="size-3.5" />
            Slack {notificationSent ? "notified automatically" : "pending"}
          </span>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          <span className="text-sm text-muted-foreground">
            Non-critical incident — Jira creation is manual.
          </span>
        </div>
      )}

      {!isCritical && (
        <button
          type="button"
          disabled={manualTicketCreated}
          onClick={() => setManualTicketCreated(true)}
          className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {manualTicketCreated ? (
            <>
              <CheckCircle2 className="size-4" />
              Ticket created
            </>
          ) : (
            <>
              <Ticket className="size-4" />
              Create Jira Ticket
            </>
          )}
        </button>
      )}
    </div>
  );
}
