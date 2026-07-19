import { Suspense } from "react";
import { DashboardShell } from "@/features/dashboard/dashboard-shell";

export default function DashboardPage() {
  return (
    // useSearchParams (inside DashboardShell) opts this route out of full
    // static rendering unless wrapped in Suspense — see Next.js app router.
    <Suspense fallback={null}>
      <DashboardShell />
    </Suspense>
  );
}
