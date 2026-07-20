export type IntegrationHealth = {
  key: string;
  name: string;
  healthy: boolean;
  status_text: string;
  detail: string | null;
};

export type HealthCheckResult = {
  integrations: IntegrationHealth[];
};
