import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Severity } from "@/types/incident";

// Severity is domain state, not theme state — critical maps to the
// destructive variant; the other tiers need distinct hues the Badge
// variants don't carry, so they tint via className on top of `outline`.
const SEVERITY_CLASSES: Record<Severity, string> = {
  critical: "",
  high: "border-transparent bg-orange-100 text-orange-700 dark:bg-orange-500/15 dark:text-orange-400",
  medium: "border-transparent bg-amber-100 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  low: "border-transparent bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400",
};

const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "Critical",
  high: "High",
  medium: "Medium",
  low: "Low",
};

export function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <Badge
      variant={severity === "critical" ? "destructive" : "outline"}
      className={cn(SEVERITY_CLASSES[severity])}
    >
      {SEVERITY_LABELS[severity]}
    </Badge>
  );
}
