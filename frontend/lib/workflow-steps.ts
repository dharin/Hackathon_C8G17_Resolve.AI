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
 * incident exists), rca/remediation/cookbook reflect the real fetch state
 * (an empty recommendations array still counts as "ran" — it's a
 * legitimate "no supporting documentation found" outcome, not "not run
 * yet"), and notification stays pending until Phase 11 exists.
 */
export function computeWorkflowSteps({
  hasRca,
  remediationRan,
  hasCookbook,
  loadingDetail,
}: {
  hasRca: boolean;
  remediationRan: boolean;
  hasCookbook: boolean;
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
    if (index === 2) {
      return {
        ...step,
        status: remediationRan
          ? "complete"
          : loadingDetail
            ? "current"
            : "pending",
      };
    }
    if (index === 3) {
      return {
        ...step,
        status: hasCookbook
          ? "complete"
          : loadingDetail
            ? "current"
            : "pending",
      };
    }
    return { ...step, status: "pending" };
  });
}
