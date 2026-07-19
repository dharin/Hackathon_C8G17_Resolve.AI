"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  LayoutDashboard,
  Upload,
  BookOpen,
  SlidersHorizontal,
  Plug,
  ScrollText,
  Settings,
  HelpCircle,
  Menu,
  Activity,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
  SheetTitle,
} from "@/components/ui/sheet";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/upload-logs", label: "Upload Logs", icon: Upload },
  { href: "/knowledge-base", label: "Knowledge Base", icon: BookOpen },
  { href: "/rag-configuration", label: "RAG Configuration", icon: SlidersHorizontal },
  { href: "/integrations", label: "Integrations", icon: Plug },
  { href: "/audit-logs", label: "Audit Logs", icon: ScrollText },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/help", label: "Help", icon: HelpCircle },
] as const;

function Brand() {
  return (
    <div className="flex items-center gap-2 px-2 py-1.5">
      <div className="flex size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
        <Activity className="size-4" />
      </div>
      <span className="text-sm font-semibold text-sidebar-foreground">
        Incident Analysis
      </span>
    </div>
  );
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-1 flex-col gap-1 px-2">
      {NAV_ITEMS.map(({ href, label, icon: Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            onClick={onNavigate}
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              active
                ? "bg-sidebar-primary text-sidebar-primary-foreground"
                : "text-sidebar-foreground/80 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
            )}
          >
            <Icon className="size-4 shrink-0" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

/** Fixed desktop sidebar. Dark surface, independent of the light workspace theme. */
export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar py-4 lg:flex">
      <Brand />
      <div className="mt-4 flex flex-1 flex-col">
        <NavList />
      </div>
    </aside>
  );
}

/** Off-canvas sidebar for small screens, with its own trigger button. */
export function MobileSidebar() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <button
            className="flex size-9 items-center justify-center rounded-lg border border-border hover:bg-accent lg:hidden"
            aria-label="Open navigation"
          />
        }
      >
        <Menu className="size-4" />
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-64 border-sidebar-border bg-sidebar p-0 py-4 text-sidebar-foreground [&_svg]:text-sidebar-foreground"
      >
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <Brand />
        <div className="mt-4 flex flex-1 flex-col">
          <NavList onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  );
}
