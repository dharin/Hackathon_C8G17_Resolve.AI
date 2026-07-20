"use client";

import { SignedIn, SignedOut, useClerk, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MobileSidebar } from "@/components/sidebar";
import { clearPersistedAnalysisId } from "@/lib/analysis-session";

export function TopHeader() {
  const { user, isLoaded } = useUser();
  const { signOut } = useClerk();

  return (
    <header className="glass-surface sticky top-0 z-20 flex items-center justify-between gap-3 border-b border-border px-4 py-3 sm:px-6">
      <div className="flex items-center gap-3">
        <MobileSidebar />
        <div>
          <h1 className="text-sm font-semibold">Incident Workspace</h1>
          <p className="text-xs text-muted-foreground">
            DevOps Incident Analysis Suite
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3 text-sm">
        {!isLoaded && (
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-8 rounded-full" />
          </div>
        )}

        {isLoaded && (
          <>
            <SignedIn>
              <span
                data-testid="username"
                className="hidden text-muted-foreground sm:inline"
              >
                {user?.fullName ??
                  user?.username ??
                  user?.primaryEmailAddress?.emailAddress ??
                  "Signed in"}
              </span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  clearPersistedAnalysisId();
                  signOut();
                }}
              >
                Sign out
              </Button>
            </SignedIn>
            <SignedOut>
              <Button
                variant="outline"
                size="sm"
                nativeButton={false}
                render={<Link href="/sign-in" />}
              >
                Sign in
              </Button>
            </SignedOut>
          </>
        )}
      </div>
    </header>
  );
}
