import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatShortTimestamp } from "@/lib/format-date";
import { SeverityBadge } from "@/components/severity-badge";
import type { LogIssue } from "@/types/analysis";

export function IncidentCard({
  incident,
  selected,
  analyzing = false,
  onSelect,
}: {
  incident: LogIssue;
  selected: boolean;
  analyzing?: boolean;
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
          {incident.service ?? "Unknown service"}
        </span>
        <span aria-hidden>·</span>
        <span>
          {incident.timestamp
            ? formatShortTimestamp(incident.timestamp)
            : "Unknown time"}
        </span>
      </div>
      {analyzing && (
        <div className="mt-2 flex items-center gap-1.5 text-xs font-medium text-primary">
          <Loader2 className="size-3.5 animate-spin" />
          Analyzing…
        </div>
      )}
    </button>
  );
}
