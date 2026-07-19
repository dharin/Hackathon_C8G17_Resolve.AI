"use client";

import Link from "next/link";
import { SignedIn, SignedOut, SignOutButton, useUser } from "@clerk/nextjs";

/**
 * Placeholder header for Phase 2 (auth only). Phase 3 replaces this with the
 * full dashboard header (sidebar, workflow stepper, etc.) per project-spec.md.
 */
export function Header() {
  const { user, isLoaded } = useUser();

  return (
    <header className="flex items-center justify-between border-b border-border px-6 py-3">
      <span className="text-sm font-medium">
        DevOps Incident Analysis Suite
      </span>

      <div className="flex items-center gap-3 text-sm">
        {!isLoaded && (
          <span className="text-muted-foreground">Loading session…</span>
        )}

        {isLoaded && (
          <>
            <SignedIn>
              <span data-testid="username">
                {user?.username ??
                  user?.primaryEmailAddress?.emailAddress ??
                  user?.fullName ??
                  "Signed in"}
              </span>
              <SignOutButton>
                <button className="rounded-md border border-border px-3 py-1 hover:bg-accent">
                  Sign out
                </button>
              </SignOutButton>
            </SignedIn>
            <SignedOut>
              <Link
                href="/sign-in"
                className="rounded-md border border-border px-3 py-1 hover:bg-accent"
              >
                Sign in
              </Link>
            </SignedOut>
          </>
        )}
      </div>
    </header>
  );
}
