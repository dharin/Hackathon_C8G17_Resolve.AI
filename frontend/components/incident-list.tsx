import { ScrollArea } from "@/components/ui/scroll-area";
import { IncidentCard } from "@/components/incident-card";
import type { LogIssue } from "@/types/analysis";

export function IncidentList({
  incidents,
  selectedId,
  analyzingId,
  onSelect,
}: {
  incidents: LogIssue[];
  selectedId: string | null;
  analyzingId?: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="flex h-full flex-col rounded-2xl border border-border bg-card/50">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold">Incidents</h2>
        <p className="text-xs text-muted-foreground">
          {incidents.length} detected from the latest log upload
        </p>
      </div>
      <ScrollArea className="flex-1">
        <div className="flex flex-col gap-2 p-3">
          {incidents.map((incident) => (
            <IncidentCard
              key={incident.id}
              incident={incident}
              selected={incident.id === selectedId}
              analyzing={incident.id === analyzingId}
              onSelect={() => onSelect(incident.id)}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
