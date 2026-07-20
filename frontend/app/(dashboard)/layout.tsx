import { Sidebar } from "@/components/sidebar";
import { TopHeader } from "@/components/top-header";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen lg:h-screen lg:overflow-hidden">
      <Sidebar />
      <div className="flex min-h-screen flex-1 flex-col">
        <TopHeader />
        <main className="no-scrollbar flex min-h-0 flex-1 flex-col lg:overflow-y-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
