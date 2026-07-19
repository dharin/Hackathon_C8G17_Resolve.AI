import { cn } from "@/lib/utils";
import { SeverityBadge } from "@/components/severity-badge";
import type { Incident } from "@/types/incident";

function formatTimestamp(iso: string) {
  // Fixed locale + timeZone so server and client render identical text —
  // otherwise this mismatches the browser's locale/TZ and breaks hydration.
  return new Date(iso).toLocaleString("en-US", {
    timeZone: "UTC",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function IncidentCard({
  incident,
  selected,
  onSelect,
}: {
  incident: Incident;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className={cn(
        "w-full rounded-2xl border p-3.5 text-left transition-colors",
        selected
          ? "border-primary bg-accent"
          : "border-border bg-card hover:border-primary/40 hover:bg-accent/50",
      )}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-semibold leading-snug">{incident.title}</p>
        <SeverityBadge severity={incident.severity} />
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground/70">
          {incident.service}
        </span>
        <span aria-hidden>·</span>
        <span>{formatTimestamp(incident.timestamp)}</span>
      </div>
    </button>
  );
}
