"use client";

import { useCallback, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { CheckCircle2, HeartPulse, XCircle } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverDescription,
  PopoverTitle,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { getIntegrationHealth, HealthCheckError } from "@/services/health-service";
import type { IntegrationHealth } from "@/types/health";

/** Health Check trigger + popover, shared by the desktop sidebar and the
 * mobile off-canvas nav — fetches fresh status from the backend each time
 * it's opened rather than on every sidebar render.
 */
export function HealthCheckButton() {
  const { getToken } = useAuth();
  const [integrations, setIntegrations] = useState<IntegrationHealth[] | null>(
    null,
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      const result = await getIntegrationHealth(token);
      setIntegrations(result.integrations);
    } catch (err) {
      setIntegrations(null);
      setError(
        err instanceof HealthCheckError
          ? err.message
          : "Failed to load integration health.",
      );
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  return (
    <Popover
      onOpenChange={(open) => {
        if (open) load();
      }}
    >
      <PopoverTrigger
        render={
          <button
            type="button"
            aria-label="Integration health"
            className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-sidebar-foreground/80 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
          />
        }
      >
        <HeartPulse className="size-4 shrink-0" />
        Health Check
      </PopoverTrigger>
      <PopoverContent>
        <div className="border-b border-border p-4">
          <PopoverTitle>Integration Health</PopoverTitle>
          <PopoverDescription className="mt-0.5">
            Current status of external services
          </PopoverDescription>
        </div>

        <div className="flex flex-col gap-1 p-2">
          {loading && (
            <div className="flex flex-col gap-2 p-1">
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
              <Skeleton className="h-10 w-full rounded-lg" />
            </div>
          )}

          {!loading && error && (
            <p className="p-2 text-xs text-destructive">{error}</p>
          )}

          {!loading &&
            !error &&
            integrations?.map((integration) => (
              <IntegrationRow key={integration.key} integration={integration} />
            ))}
        </div>
      </PopoverContent>
    </Popover>
  );
}

function IntegrationRow({ integration }: { integration: IntegrationHealth }) {
  const StatusIcon = integration.healthy ? CheckCircle2 : XCircle;

  return (
    <div className="flex items-center justify-between gap-3 rounded-lg px-2 py-1.5">
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{integration.name}</p>
        {integration.detail && (
          <p className="truncate text-xs text-muted-foreground">
            {integration.detail}
          </p>
        )}
      </div>
      <div className="flex shrink-0 items-center gap-1.5">
        <span className="text-xs text-muted-foreground">
          {integration.status_text}
        </span>
        <StatusIcon
          className={cn(
            "size-4",
            integration.healthy ? "text-emerald-500" : "text-destructive",
          )}
        />
      </div>
    </div>
  );
}
