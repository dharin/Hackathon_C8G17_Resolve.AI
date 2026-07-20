import { API_BASE_URL } from "@/lib/upload-config";
import type { HealthCheckResult } from "@/types/health";

export class HealthCheckError extends Error {}

export async function getIntegrationHealth(
  token: string | null,
): Promise<HealthCheckResult> {
  const response = await fetch(`${API_BASE_URL}/api/v1/health/integrations`, {
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  if (!response.ok) {
    throw new HealthCheckError(
      `Failed to load integration health (status ${response.status}).`,
    );
  }

  return (await response.json()) as HealthCheckResult;
}
