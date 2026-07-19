"use client";

import { useState } from "react";
import { WorkflowStepper } from "@/components/workflow-stepper";
import { IncidentList } from "@/components/incident-list";
import { IncidentDetails } from "@/components/incident-details";
import type { Incident } from "@/types/incident";

export function DashboardShell({ incidents }: { incidents: Incident[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(
    incidents[0]?.id ?? null,
  );

  const selected = incidents.find((incident) => incident.id === selectedId);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 p-4 sm:p-6">
      {selected && <WorkflowStepper steps={selected.workflow} />}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 lg:grid-cols-[360px_1fr]">
        <div className="min-h-[420px] lg:min-h-0">
          <IncidentList
            incidents={incidents}
            selectedId={selectedId}
            onSelect={setSelectedId}
          />
        </div>
        <div className="min-h-[520px] lg:min-h-0">
          {selected ? (
            <IncidentDetails incident={selected} />
          ) : (
            <div className="flex h-full items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
              Select an incident to view details.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
