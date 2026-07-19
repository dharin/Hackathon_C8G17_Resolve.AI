import type { NextConfig } from "next";
import path from "path";
import { config as loadEnv } from "dotenv";

// Repo-root .env is the single shared source of env vars for both apps (see
// project-spec.md). Next.js only auto-loads .env files inside frontend/, so
// without this, NEXT_PUBLIC_* and server-only vars here silently fall back
// to Clerk's keyless dev mode instead of the real configured keys.
loadEnv({ path: path.join(__dirname, "..", ".env") });

const nextConfig: NextConfig = {
  turbopack: {
    root: path.join(__dirname),
  },
};

export default nextConfig;
