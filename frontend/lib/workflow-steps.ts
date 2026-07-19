import type { WorkflowStep } from "@/types/incident";

const STEP_DEFS: { id: WorkflowStep["id"]; label: string }[] = [
  { id: "log-reader", label: "Log Reader" },
  { id: "rca", label: "RCA" },
  { id: "remediation", label: "Remediation" },
  { id: "cookbook", label: "Cookbook" },
  { id: "notification", label: "Notification" },
];

/** Derives workflow-stepper status from what's actually been computed for
 * the selected incident so far — log-reader is always complete (the
 * incident exists), rca reflects the real fetch state, and
 * remediation/cookbook/notification stay pending until Phases 8-11 exist.
 */
export function computeWorkflowSteps({
  hasRca,
  loadingDetail,
}: {
  hasRca: boolean;
  loadingDetail: boolean;
}): WorkflowStep[] {
  return STEP_DEFS.map((step, index): WorkflowStep => {
    if (index === 0) return { ...step, status: "complete" };
    if (index === 1) {
      return {
        ...step,
        status: hasRca ? "complete" : loadingDetail ? "current" : "pending",
      };
    }
    return { ...step, status: "pending" };
  });
}
