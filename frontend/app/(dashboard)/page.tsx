import { DashboardShell } from "@/features/dashboard/dashboard-shell";
import { mockIncidents } from "@/lib/mock-incidents";

export default function DashboardPage() {
  return <DashboardShell incidents={mockIncidents} />;
}
