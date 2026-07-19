# Standard Operating Procedures

---

## SOP-01: Postgres Connection Pooling — Configuration & Recovery

**Owner:** Platform/Database team
**Applies to:** Any service backed by Postgres with a connection pool (app-level or PgBouncer)

### Purpose
Defines how connection pool settings are configured, monitored, and recovered when exhaustion occurs.

### Standard configuration
- Pool size per service instance should be set so that `(pool_size × instance_count) ≤ 80%` of the database's `max_connections`, leaving headroom for admin/migration connections.
- Idle connection timeout: 5 minutes.
- Connection acquisition timeout: 3 seconds (fail fast rather than queue indefinitely).

### Monitoring
- Alert when pool wait time exceeds 500ms sustained for 1 minute.
- Alert when active connections exceed 85% of pool size.
- Dashboard: connection pool utilization per service, refreshed every 30s.

### Recovery procedure (when exhaustion occurs)
1. Confirm exhaustion via `pg_stat_activity` — count active vs. idle-in-transaction connections.
2. Check for a recent deploy or config change that altered `max_connections` or pool size. If found, revert first — this resolves the majority of cases.
3. If no config change, check for idle-in-transaction connections older than 5 minutes — these indicate a leak. Identify the offending code path.
4. If load-driven (traffic genuinely grew), temporarily raise `max_connections` as a stopgap, then schedule a PgBouncer rollout (see SOP-03 / Confluence: PgBouncer Rollout Proposal) as the durable fix.
5. Validate: pool wait time returns to near-zero, error rate on dependent services returns to baseline.

### Change control
Any change to `max_connections` or pool size requires a peer review and must be tested in staging under representative load before production rollout.

---

## SOP-02: Incident Severity Classification & Jira Escalation

**Owner:** On-call engineering
**Applies to:** All incidents surfaced by the automated analysis suite or reported manually

### Purpose
Standardizes how incidents are classified by severity and what escalation action follows automatically vs. manually.

### Severity definitions
| Severity | Definition | Example |
|---|---|---|
| Critical | Customer-facing outage or data integrity risk, no workaround | DB connection pool fully exhausted, checkout down |
| High | Significant degradation, partial impact or workaround exists | 5xx spike affecting a subset of requests |
| Medium | Localized or intermittent issue, limited blast radius | Elevated timeout rate to one downstream dependency |
| Low | Anomaly worth tracking, no current user impact | Isolated auth failures for one account |

### Escalation rules
- **Critical:** a Jira ticket is created automatically by the system at detection time, and the on-call channel is notified via Slack immediately after ticket creation. No manual action needed to open the ticket.
- **High / Medium / Low:** no ticket is created automatically. The on-call engineer reviews the incident in the dashboard and creates a Jira ticket manually if it warrants tracking (e.g. recurring pattern, follow-up work needed).

### On-call responsibilities
1. Acknowledge the Slack notification for any Critical incident within 5 minutes.
2. Review the system's root cause analysis and recommended remediation before taking action — don't skip straight to a fix without confirming the RCA reasoning holds up.
3. For non-critical incidents reviewed manually, use judgment: an incident that recurs 3+ times in a week should get a ticket even at Low/Medium severity, to track the pattern.
4. Update the Jira ticket with the outcome (root cause confirmed / remediation applied / follow-up needed) before closing.

### Review cadence
Severity classifications and escalation rules are reviewed quarterly against actual incident outcomes to catch over- or under-escalation.

---

## SOP-03: Log Rotation & Disk Space Management

**Owner:** Platform team
**Applies to:** All services writing logs to local disk (`/var/log` or equivalent)

### Purpose
Prevents disk space exhaustion incidents caused by unrotated or excessive logging.

### Standard configuration
- All services must have `logrotate` (or platform equivalent) configured with:
  - Daily rotation
  - 7-day retention for local copies
  - Compression on rotated files
- Log verbosity in production must default to `INFO` or higher — `DEBUG` logging in production requires a time-boxed exception approved by the service owner.

### Monitoring
- Alert at 80% disk usage on any log-bearing mount (warning).
- Page at 90% disk usage (urgent — active risk of write failures).

### Recovery procedure (when exhaustion occurs)
1. Identify the full mount: `df -h`.
2. Identify the largest consumers: `du -sh /var/log/* | sort -rh | head`.
3. If rotated/compressed old logs are present but retention is misconfigured, manually clear anything beyond the 7-day policy to immediately free space.
4. If logs are not rotating at all, check `logrotate` configuration and cron/systemd timer status — fix and force a manual rotation.
5. If a single service is logging abnormally verbosely (e.g. `DEBUG` accidentally left on), reduce verbosity and redeploy.
6. Validate: disk usage drops below 80%, and confirm writes succeed again by tailing the previously affected service's logs.

### Prevention
Any new service must have log rotation configured as part of its initial deployment checklist — this is not an optional follow-up step.
