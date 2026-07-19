import type { Incident, WorkflowStep } from "@/types/incident";

function workflow(currentIndex: number): WorkflowStep[] {
  const steps: { id: WorkflowStep["id"]; label: string }[] = [
    { id: "log-reader", label: "Log Reader" },
    { id: "rca", label: "RCA" },
    { id: "remediation", label: "Remediation" },
    { id: "cookbook", label: "Cookbook" },
    { id: "notification", label: "Notification" },
  ];

  return steps.map((step, index) => ({
    ...step,
    status:
      index < currentIndex
        ? "complete"
        : index === currentIndex
          ? "current"
          : "pending",
  }));
}

export const mockIncidents: Incident[] = [
  {
    id: "inc-1042",
    title: "Checkout service returning 503s",
    service: "checkout-api",
    timestamp: "2026-07-19T08:12:00Z",
    severity: "critical",
    category: "availability",
    confidence: 0.94,
    overview:
      "Elevated 503 error rate on checkout-api starting 08:09 UTC, correlated with a connection pool exhaustion event on the primary Postgres instance. Error rate peaked at 62% before mitigation.",
    rca: {
      primaryCause:
        "Database connection pool exhausted after a slow-query regression in the pricing-service deploy at 08:05 UTC held connections open under load.",
      evidence: [
        "checkout-api logs show 'connection pool timeout' starting 08:09:14 UTC",
        "Postgres pg_stat_activity shows 100/100 connections held by pricing-service queries",
        "Deploy log: pricing-service v2.14.0 rolled out at 08:05 UTC, 4 minutes before onset",
      ],
      alternativeCauses: [
        "Upstream network partition between checkout-api and Postgres (ruled out — no packet loss in VPC flow logs)",
        "Postgres instance resource exhaustion (ruled out — CPU/memory nominal throughout)",
      ],
      confidence: 0.94,
    },
    recommendations: [
      {
        id: "rec-1",
        title: "Roll back pricing-service to v2.13.2",
        confidence: 0.91,
        reason:
          "The regression was introduced in v2.14.0's new pricing query; rolling back removes the slow query immediately while a fix is prepared.",
        sources: [
          {
            id: "src-1",
            title: "Incident Response: Connection Pool Exhaustion",
            type: "confluence",
            section: "Runbooks / Database",
            lastUpdated: "2026-05-02",
            url: "https://confluence.example.com/runbooks/db-pool-exhaustion",
          },
          {
            id: "src-2",
            title: "INC-0871 — Checkout 503s (Feb 2026)",
            type: "historical-incident",
            section: "Postmortem",
            lastUpdated: "2026-02-11",
            url: "https://confluence.example.com/postmortems/inc-0871",
          },
        ],
      },
      {
        id: "rec-2",
        title: "Increase Postgres max_connections with PgBouncer in front",
        confidence: 0.68,
        reason:
          "Reduces blast radius of future connection leaks, but does not address the root cause query regression.",
        sources: [
          {
            id: "src-3",
            title: "Database Scaling Guidelines",
            type: "google-drive",
            section: "Capacity Planning",
            lastUpdated: "2026-03-18",
            url: "https://drive.example.com/database-scaling-guidelines",
          },
        ],
      },
    ],
    cookbook: {
      rootCause:
        "pricing-service v2.14.0 introduced a slow query that holds Postgres connections open, exhausting the shared connection pool used by checkout-api.",
      steps: [
        "Confirm pricing-service v2.14.0 is the active deployed version",
        "Roll back pricing-service to v2.13.2",
        "Verify checkout-api error rate returns to baseline",
        "Notify #eng-database of the regression for a permanent query fix",
      ],
      commands: [
        "kubectl rollout undo deployment/pricing-service -n prod",
        "kubectl rollout status deployment/pricing-service -n prod",
        "curl -s https://internal.example.com/checkout-api/healthz",
      ],
      validation: [
        "checkout-api 5xx rate < 1% for 5 consecutive minutes",
        "Postgres active connections < 70/100",
      ],
      rollback: [
        "kubectl rollout undo deployment/pricing-service -n prod --to-revision=<previous>",
        "If error rate persists, fail over checkout-api to read replica per DB failover runbook",
      ],
    },
    logs: [
      { timestamp: "08:09:14", level: "ERROR", message: "connection pool timeout after 5000ms (checkout-api)" },
      { timestamp: "08:09:16", level: "ERROR", message: "503 Service Unavailable returned for POST /checkout" },
      { timestamp: "08:11:02", level: "FATAL", message: "pg pool exhausted: 100/100 connections in use" },
      { timestamp: "08:12:40", level: "WARN", message: "checkout-api error rate 62% over last 60s" },
    ],
    metadata: {
      incidentId: "INC-1042",
      environment: "production",
      region: "us-east-1",
      affectedHosts: ["checkout-api-7f9b", "checkout-api-3d1e"],
      detectedBy: "log-reader-agent",
      tags: ["database", "checkout", "connection-pool"],
    },
    workflow: workflow(4),
  },
  {
    id: "inc-1043",
    title: "Elevated latency on search-service",
    service: "search-service",
    timestamp: "2026-07-19T07:41:00Z",
    severity: "medium",
    category: "performance",
    confidence: 0.78,
    overview:
      "p95 latency on search-service rose from 180ms to 640ms starting 07:38 UTC. No errors, service remained available throughout.",
    rca: {
      primaryCause:
        "Elasticsearch shard rebalancing triggered by a node restart increased query latency across the search-service cluster.",
      evidence: [
        "ES cluster health transitioned green → yellow at 07:37 UTC",
        "search-service p95 latency graph shows correlated rise at 07:38 UTC",
      ],
      alternativeCauses: [
        "Increased query volume (ruled out — request rate flat over the window)",
      ],
      confidence: 0.78,
    },
    recommendations: [
      {
        id: "rec-3",
        title: "No action required — monitor until rebalancing completes",
        confidence: 0.72,
        reason:
          "Shard rebalancing is expected to self-resolve; historical incidents show latency recovers once cluster returns to green.",
        sources: [
          {
            id: "src-4",
            title: "Elasticsearch Operations Guide",
            type: "confluence",
            section: "Cluster Health",
            lastUpdated: "2026-01-22",
            url: "https://confluence.example.com/runbooks/es-operations",
          },
        ],
      },
    ],
    cookbook: null,
    logs: [
      { timestamp: "07:37:58", level: "WARN", message: "elasticsearch cluster health: yellow" },
      { timestamp: "07:38:20", level: "WARN", message: "search-service p95 latency 640ms (threshold 300ms)" },
    ],
    metadata: {
      incidentId: "INC-1043",
      environment: "production",
      region: "us-east-1",
      affectedHosts: ["search-es-node-4"],
      detectedBy: "log-reader-agent",
      tags: ["elasticsearch", "latency"],
    },
    workflow: workflow(2),
  },
  {
    id: "inc-1044",
    title: "Auth token refresh failures spiking",
    service: "auth-service",
    timestamp: "2026-07-19T06:55:00Z",
    severity: "high",
    category: "availability",
    confidence: 0.85,
    overview:
      "Token refresh failure rate rose to 18% starting 06:52 UTC. Root cause under investigation.",
    rca: {
      primaryCause:
        "Redis session store hit memory eviction threshold, dropping refresh tokens before expiry.",
      evidence: [
        "auth-service logs show 'refresh token not found' errors starting 06:52 UTC",
        "Redis used_memory reached maxmemory limit at 06:51 UTC, evicted 12k keys",
      ],
      alternativeCauses: [
        "Clock skew between auth-service instances (ruled out — NTP sync nominal)",
      ],
      confidence: 0.85,
    },
    recommendations: [],
    cookbook: null,
    logs: [
      { timestamp: "06:51:40", level: "WARN", message: "redis used_memory at 99.2% of maxmemory" },
      { timestamp: "06:52:03", level: "ERROR", message: "refresh token not found for session 8f21c" },
    ],
    metadata: {
      incidentId: "INC-1044",
      environment: "production",
      region: "eu-west-1",
      affectedHosts: ["auth-redis-primary"],
      detectedBy: "log-reader-agent",
      tags: ["redis", "auth", "session"],
    },
    workflow: workflow(1),
  },
  {
    id: "inc-1045",
    title: "Background job queue backlog growing",
    service: "worker-jobs",
    timestamp: "2026-07-19T05:20:00Z",
    severity: "low",
    category: "performance",
    confidence: 0.6,
    overview:
      "Job queue depth grew from ~200 to ~3,100 over the last hour. No customer-facing impact detected yet.",
    rca: null,
    recommendations: [],
    cookbook: null,
    logs: [
      { timestamp: "05:19:11", level: "INFO", message: "queue depth: 3104 (baseline ~200)" },
    ],
    metadata: {
      incidentId: "INC-1045",
      environment: "production",
      region: "us-east-1",
      affectedHosts: ["worker-jobs-1", "worker-jobs-2"],
      detectedBy: "log-reader-agent",
      tags: ["queue", "background-jobs"],
    },
    workflow: workflow(0),
  },
];
