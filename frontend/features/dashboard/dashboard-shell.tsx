"use client";

import { useState } from "react";
import { MousePointerClick } from "lucide-react";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
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
            <Empty className="h-full border border-dashed">
              <EmptyHeader>
                <EmptyMedia variant="icon">
                  <MousePointerClick />
                </EmptyMedia>
                <EmptyTitle>No incident selected</EmptyTitle>
                <EmptyDescription>
                  Select an incident from the list to view its analysis.
                </EmptyDescription>
              </EmptyHeader>
            </Empty>
          )}
        </div>
      </div>
    </div>
  );
}
