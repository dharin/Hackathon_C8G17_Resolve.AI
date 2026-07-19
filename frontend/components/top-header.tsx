"use client";

import { SignedIn, SignedOut, SignOutButton, useUser } from "@clerk/nextjs";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { MobileSidebar } from "@/components/sidebar";

export function TopHeader() {
  const { user, isLoaded } = useUser();

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
                {user?.username ??
                  user?.primaryEmailAddress?.emailAddress ??
                  user?.fullName ??
                  "Signed in"}
              </span>
              <SignOutButton>
                <Button variant="outline" size="sm">
                  Sign out
                </Button>
              </SignOutButton>
            </SignedIn>
            <SignedOut>
              <Button
                variant="outline"
                size="sm"
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
