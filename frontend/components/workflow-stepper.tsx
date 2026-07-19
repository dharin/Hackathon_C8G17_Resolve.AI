import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import type { WorkflowStep } from "@/types/incident";

export function WorkflowStepper({ steps }: { steps: WorkflowStep[] }) {
  return (
    <ol className="flex items-center gap-1 overflow-x-auto rounded-2xl border border-border bg-card px-3 py-3 sm:gap-2 sm:px-4">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        return (
          <li key={step.id} className="flex shrink-0 items-center gap-1 sm:gap-2">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex size-6 shrink-0 items-center justify-center rounded-full text-xs font-medium",
                  step.status === "complete" &&
                    "bg-primary text-primary-foreground",
                  step.status === "current" &&
                    "bg-primary/15 text-primary ring-2 ring-primary",
                  step.status === "pending" &&
                    "bg-muted text-muted-foreground",
                )}
              >
                {step.status === "complete" ? (
                  <Check className="size-3.5" />
                ) : (
                  index + 1
                )}
              </span>
              <span
                className={cn(
                  "whitespace-nowrap text-xs font-medium sm:text-sm",
                  step.status === "pending"
                    ? "text-muted-foreground"
                    : "text-foreground",
                )}
              >
                {step.label}
              </span>
            </div>
            {!isLast && (
              <span
                className={cn(
                  "mx-1 h-px w-6 shrink-0 sm:w-10",
                  step.status === "complete" ? "bg-primary" : "bg-border",
                )}
              />
            )}
          </li>
        );
      })}
    </ol>
  );
}
