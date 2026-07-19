"use client";

import { useEffect, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  AlertCircle,
  CheckCircle2,
  ExternalLink,
  Loader2,
  MessageSquare,
  Ticket,
} from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { AnalysisError, createJiraTicket } from "@/services/analysis-service";
import type { Severity } from "@/types/incident";
import type { JiraTicketReference, SlackNotificationReference } from "@/types/analysis";

const SUCCESS_ALERT_TIMEOUT_MS = 6000;

export function BottomActionPanel({
  severity,
  analysisId,
  incidentId,
  jiraTicket,
  slackNotification,
  onTicketCreated,
}: {
  severity: Severity;
  analysisId: string;
  incidentId: string;
  jiraTicket: JiraTicketReference | null;
  slackNotification: SlackNotificationReference | null;
  onTicketCreated: (ticket: JiraTicketReference) => void;
}) {
  const isCritical = severity === "critical";
  const { getToken } = useAuth();
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdTicket, setCreatedTicket] = useState<JiraTicketReference | null>(null);
  const dismissTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (dismissTimeoutRef.current) clearTimeout(dismissTimeoutRef.current);
    };
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    setError(null);
    try {
      const token = await getToken();
      const ticket = await createJiraTicket(analysisId, incidentId, token);
      onTicketCreated(ticket);
      setCreatedTicket(ticket);
      if (dismissTimeoutRef.current) clearTimeout(dismissTimeoutRef.current);
      dismissTimeoutRef.current = setTimeout(
        () => setCreatedTicket(null),
        SUCCESS_ALERT_TIMEOUT_MS,
      );
    } catch (err) {
      setError(
        err instanceof AnalysisError ? err.message : "Failed to create ticket.",
      );
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex flex-col gap-2">
      {createdTicket && (
        <Alert>
          <CheckCircle2 className="text-primary" />
          <AlertTitle>Jira ticket created successfully</AlertTitle>
          <AlertDescription>
            Ticket ID:{" "}
            <a href={createdTicket.url} target="_blank" rel="noopener noreferrer">
              {createdTicket.key}
            </a>
          </AlertDescription>
        </Alert>
      )}

      <div className="glass-surface sticky bottom-0 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border px-4 py-3">
        {isCritical ? (
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="text-muted-foreground">Critical incident —</span>
            {jiraTicket ? (
              <JiraTicketBadge ticket={jiraTicket} />
            ) : (
              <Badge variant="outline">
                <Ticket />
                Jira not created (Jira integration unconfigured)
              </Badge>
            )}
            {jiraTicket &&
              (slackNotification ? (
                <SlackNotifiedBadge notification={slackNotification} />
              ) : (
                <Badge variant="outline">
                  <MessageSquare />
                  Slack not notified (Slack integration unconfigured)
                </Badge>
              ))}
          </div>
        ) : (
          <span className="text-sm text-muted-foreground">
            Non-critical incident — Jira creation is manual.
          </span>
        )}

        {!isCritical &&
          (jiraTicket ? (
            <JiraTicketBadge ticket={jiraTicket} />
          ) : (
            <div className="flex items-center gap-2">
              {error && (
                <span className="flex items-center gap-1 text-xs text-destructive">
                  <AlertCircle className="size-3.5" />
                  {error}
                </span>
              )}
              <Button disabled={creating} onClick={handleCreate}>
                {creating ? (
                  <>
                    <Loader2 data-icon="inline-start" className="animate-spin" />
                    Creating…
                  </>
                ) : (
                  <>
                    <Ticket data-icon="inline-start" />
                    Create Jira Ticket
                  </>
                )}
              </Button>
            </div>
          ))}
      </div>
    </div>
  );
}

function JiraTicketBadge({ ticket }: { ticket: JiraTicketReference }) {
  return (
    <Button
      variant="outline"
      size="sm"
      nativeButton={false}
      render={<a href={ticket.url} target="_blank" rel="noopener noreferrer" />}
    >
      <CheckCircle2 data-icon="inline-start" className="text-primary" />
      {ticket.key}
      <ExternalLink data-icon="inline-end" className="size-3.5" />
    </Button>
  );
}

function SlackNotifiedBadge({
  notification,
}: {
  notification: SlackNotificationReference;
}) {
  if (!notification.permalink) {
    return (
      <Badge variant="secondary">
        <CheckCircle2 className="text-primary" />
        Slack notified
      </Badge>
    );
  }
  return (
    <Button
      variant="outline"
      size="sm"
      nativeButton={false}
      render={
        <a href={notification.permalink} target="_blank" rel="noopener noreferrer" />
      }
    >
      <CheckCircle2 data-icon="inline-start" className="text-primary" />
      Slack notified
      <ExternalLink data-icon="inline-end" className="size-3.5" />
    </Button>
  );
}
