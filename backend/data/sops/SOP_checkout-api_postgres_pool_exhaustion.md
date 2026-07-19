# Standard Operating Procedure (SOP)
## Postgres Connection Pool Exhaustion — checkout-api

| Field | Value |
|---|---|
| Service | checkout-api |
| Failure Mode | Postgres connection pool exhaustion → elevated error rate |
| Severity | SEV-1 (customer-impacting, revenue-critical path) |
| Owner | Checkout Platform On-Call |
| Last Updated | 2026-07-19 |

---

## 1. Trigger / Detection

This SOP applies when logs show this progression pattern:

```
ERROR  postgres connection pool timeout after Nms
FATAL  postgres connection pool exhausted: X/X connections in use
WARN   checkout-api error rate NN% over last 60s
```

**Reference incident timeline:**

| Time (UTC) | Level | Event | Meaning |
|---|---|---|---|
| 08:09:00 | INFO | heartbeat ok | Service healthy |
| 08:09:14 | ERROR | pool timeout after 5000ms | Early warning — connections becoming scarce |
| 08:11:02 | FATAL | pool exhausted 100/100 | Total saturation — no headroom left |
| 08:12:40 | WARN | error rate 62% over 60s | Customer impact confirmed |

**Key insight:** the ERROR → FATAL gap here was under 2 minutes. Treat the *first* timeout ERROR as an actionable early-warning signal, not noise — waiting for FATAL means you're already too late.

---

## 2. Immediate Response (Target: first 5 minutes)

**Goal in this phase: stop the bleeding, not find the root cause.**

1. **Acknowledge & declare incident**
   - Ack the alert, open an incident channel/ticket, page secondary if pool has been at FATAL >2 min.
2. **Confirm blast radius**
   - Check error rate trend (climbing / plateaued / recovering?) and whether other services sharing the same DB are affected.
3. **Check current pool state**
   ```sql
   SELECT count(*), state FROM pg_stat_activity
   WHERE datname = 'checkout' GROUP BY state;
   ```
4. **Identify and clear stuck connections**
   ```sql
   -- Find long-running idle-in-transaction connections (common leak signature)
   SELECT pid, state, now() - state_change AS idle_duration, query
   FROM pg_stat_activity
   WHERE state = 'idle in transaction'
     AND now() - state_change > interval '2 minutes'
   ORDER BY idle_duration DESC;

   -- Terminate the worst offenders (validate before mass-killing)
   SELECT pg_terminate_backend(pid) FROM pg_stat_activity
   WHERE state = 'idle in transaction'
     AND now() - state_change > interval '5 minutes';
   ```
5. **Relieve pressure on the app side**
   - Restart the checkout-api pods/instances in rolling fashion (releases leaked client-side connections without full downtime):
     ```
     kubectl rollout restart deployment/checkout-api -n <namespace>
     ```
   - If using PgBouncer/pooler in front of Postgres, restart or reload it to reset its internal pool state.
6. **Protect the DB from a repeat spike**
   - If traffic-driven, enable/verify rate limiting or circuit breaker on checkout-api's DB client so it fails fast instead of queueing and holding connections.
7. **Re-check error rate** every 60–120s until it trends back toward baseline.

**Do not proceed to Section 3 until error rate has stabilized or is clearly declining.**

---

## 3. Root Cause Investigation (Target: next 15–30 minutes)

Work through these in order — stop at the first confirmed cause:

| # | Check | How |
|---|---|---|
| 1 | **Connection leak in app code** | Search recent deploys for DB calls missing `release()`/`close()`, especially in error/catch paths. Check if pool "in use" count grows monotonically even under flat traffic. |
| 2 | **Traffic spike** | Compare request rate to normal baseline for this time of day. Check for bot traffic, retries-storm from a downstream caller, or a marketing/promo event. |
| 3 | **Slow / blocking queries holding connections** | `SELECT pid, now()-query_start AS runtime, query FROM pg_stat_activity WHERE state='active' ORDER BY runtime DESC;` — look for missing indexes, lock waits, or a new query pattern from a recent release. |
| 4 | **Pool misconfiguration** | Confirm configured max pool size vs. actual DB `max_connections`, and whether multiple app replicas × pool size can exceed DB capacity. |
| 5 | **Downstream/network issue** | Check for recent network blips, DB failover, or replica lag causing connections to hang instead of closing cleanly. |
| 6 | **Recent deploy correlation** | Check deploy timeline — did the first ERROR (08:09:14) follow a release? |

---

## 4. Remediation Actions

Apply based on confirmed root cause from Section 3:

- **Leak in code:** Patch the code path to guarantee connection release (`finally` blocks / context managers); hotfix and deploy.
- **Traffic spike:** Scale checkout-api horizontally; consider read replicas for read-heavy queries; add caching for hot lookups.
- **Slow queries:** Add missing index, optimize query, or move heavy reporting queries off the primary transactional path.
- **Pool misconfig:** Right-size `max_pool_size × replica_count` to stay under Postgres `max_connections` with headroom; consider introducing PgBouncer (transaction pooling mode) to multiplex connections.
- **No single root cause found:** Add connection acquisition timeout + max lifetime (recycle connections periodically) as a safety net while investigation continues.

---

## 5. Verification (Recovery Confirmation)

Before closing the incident, confirm **all** of the following for 15+ consecutive minutes:

- [ ] Postgres active connections stable and below configured max (e.g., <80/100)
- [ ] No new `pool timeout` or `pool exhausted` log entries
- [ ] checkout-api error rate back to baseline (<1–2%)
- [ ] Synthetic/canary checkout transaction succeeds end-to-end
- [ ] No abnormal idle-in-transaction connections accumulating

---

## 6. Post-Incident Actions

1. **Write postmortem** within 48 hours — include the ERROR→FATAL→WARN timeline, root cause, and time-to-detect/time-to-mitigate.
2. **Tune alerting** — alert on pool utilization **percentage** (e.g., >70%) rather than waiting for exhaustion, so the team acts at the 08:09:14-equivalent event, not the 08:11:02 one.
3. **Add a dashboard panel** for: active/idle/idle-in-transaction connections, pool utilization %, and query latency p99.
4. **Capacity review** — validate pool sizing math against real replica count and DB limits.
5. **Regression test** — if a code leak was the cause, add a test or lint rule to catch unreleased connections in review.

---

## 7. Escalation Path

| Condition | Action |
|---|---|
| Error rate >50% for >5 min after mitigation attempts | Page secondary on-call + DB team |
| Root cause not identified in 30 min | Escalate to service owner + engineering manager |
| Suspected data integrity issue | Loop in DBA immediately, halt further deploys |

---

## Appendix: Quick Reference Commands

```sql
-- Connection count by state
SELECT state, count(*) FROM pg_stat_activity GROUP BY state;

-- Longest-running active queries
SELECT pid, now()-query_start AS runtime, query
FROM pg_stat_activity WHERE state='active' ORDER BY runtime DESC LIMIT 10;

-- Current max_connections setting
SHOW max_connections;
```

```
# Rolling restart of app to release client-side connections
kubectl rollout restart deployment/checkout-api -n <namespace>

# Check current replica count / pool math
kubectl get pods -l app=checkout-api -n <namespace> | wc -l
```
