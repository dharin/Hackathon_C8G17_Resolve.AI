# Standard Operating Procedure (SOP)
## HTTP 5xx Error Burst — checkout-api (POST /checkout)

| Field | Value |
|---|---|
| Service | checkout-api |
| Failure Mode | Mixed 503/500 error burst on critical checkout endpoint |
| Severity | SEV-1 (directly blocks revenue-critical checkout flow) |
| Owner | Checkout Platform On-Call |
| Last Updated | 2026-07-19 |

---

## 1. Trigger / Detection

This SOP applies when logs show a burst pattern like:

```
ERROR  "POST /checkout HTTP/1.1" 503 Service Unavailable
ERROR  "POST /checkout HTTP/1.1" 500 Internal Server Error
INFO   heartbeat ok   <-- can look "resolved" while root cause is still live
```

**Reference incident timeline:**

| Time (UTC) | Level | Event | Meaning |
|---|---|---|---|
| 09:00:00 | INFO | heartbeat ok | Service reporting healthy |
| 09:00:05 | ERROR | POST /checkout → 503 | Request rejected — no healthy backend/capacity to serve it |
| 09:00:06 | ERROR | POST /checkout → 503 | Same failure mode repeats |
| 09:00:07 | ERROR | POST /checkout → 500 | **Different status code** — an unhandled exception occurred, not just unavailability |
| 09:00:08 | ERROR | POST /checkout → 503 | Reverts to 503 |
| 09:00:20 | INFO | heartbeat ok | Heartbeat recovers ~12s after the last error — does not confirm checkout traffic is succeeding |

**Key insight — the 503/500 mix matters.** These are different failure signatures:
- **503** = something upstream had no capacity to handle the request (overloaded instance, no healthy targets behind the load balancer, connection refused, or an explicit "shedding load" response).
- **500** = a request *was* handled but threw an unhandled exception inside the application.

Seeing both in the same burst usually means **multiple instances/replicas were in different states simultaneously** — e.g., some pods mid-restart or unhealthy (503) while another pod was up but hit a bug or dependency failure (500). Treat this as a fleet-wide instability event, not a single bad request.

As with prior incidents on this service: **heartbeat recovering does not confirm checkout is actually working.** Heartbeat checks typically don't exercise the full checkout code path (payment processing, DB writes, etc.), so verify with a real transaction, not just the health endpoint.

---

## 2. Immediate Response (Target: first 5 minutes)

**Goal: confirm current impact and stop active customer-facing failures.**

1. **Confirm whether the burst is ongoing or over**
   - Check real-time error rate/dashboard for `/checkout` — is it still producing 5xx after 09:00:20, or was this an isolated ~15-second blip?

2. **Check instance/pod health across the fleet**
   ```
   kubectl get pods -l app=checkout-api -o wide
   ```
   Look for pods in `CrashLoopBackOff`, `Pending`, `NotReady`, or recent restarts — this would explain the 503s (no healthy targets to route to).

3. **Check load balancer / target group health**
   - Confirm how many backend targets were marked healthy at 09:00:05–09:00:08. A dip in healthy target count directly explains 503s (load balancer has nowhere to send the request, or sheds load).

4. **Check for an in-flight deployment**
   ```
   kubectl rollout history deployment/checkout-api
   ```
   A rolling deploy where old pods are terminating and new pods aren't yet ready is one of the most common causes of a short, self-resolving 503 burst like this one.

5. **Pull the stack trace for the 500**
   - Find the application log/exception trace corresponding to the 09:00:07 event specifically — this is the one entry that tells you *why*, not just *that*, something failed.

6. **Verify checkout is genuinely working now — not just heartbeat**
   - Run a synthetic/test checkout transaction end-to-end (not just hitting a `/health` endpoint) to confirm real success, given the pattern seen in prior incidents on this service.

---

## 3. Root Cause Investigation (Target: next 15–30 minutes)

| # | Check | How |
|---|---|---|
| 1 | **Deployment rollout in progress** | Correlate 09:00:00–09:00:20 window against deploy timestamps. If a rollout was happening, 503s during pod replacement are expected but should be brief and shouldn't include 500s from application bugs. |
| 2 | **Downstream dependency failure** | Check payment gateway, inventory service, or DB latency/error rates in the same window — a downstream timeout is a common cause of both 503 (circuit breaker open, shedding load) and 500 (unhandled timeout exception). |
| 3 | **Resource exhaustion recurrence** | Given this service's prior Postgres connection pool exhaustion incident, check `pg_stat_activity` and connection pool metrics for the same window — a partial repeat could produce this exact mixed-error signature. |
| 4 | **Autoscaling lag** | Check if a traffic spike outpaced autoscaler response time, leaving too few healthy instances momentarily. |
| 5 | **Load balancer health check misconfiguration** | Confirm health check interval/threshold isn't so aggressive that transient pod slowness (e.g., GC pause) gets misread as unhealthy and pulls capacity out unnecessarily. |
| 6 | **Unhandled exception (500) — isolate the trigger** | From the stack trace, identify whether this was a code bug, a null/edge-case input, or a downstream call that wasn't wrapped in proper error handling. |

---

## 4. Remediation Actions

Apply based on confirmed root cause from Section 3:

- **Deployment-caused:** Adjust rollout strategy (increase `maxUnavailable`/`minReadySeconds` tuning, or switch to blue/green) so old capacity isn't removed before new capacity is confirmed ready.
- **Downstream dependency failure:** Add/verify circuit breaker and sane timeout values so failures degrade gracefully (clear 503 with retry-after) instead of surfacing as unhandled 500s.
- **Resource exhaustion recurrence:** Apply the remediation steps from the existing connection-pool-exhaustion SOP for this service.
- **Autoscaling lag:** Tune scale-up thresholds/cooldowns to react faster to traffic spikes; consider pre-warming capacity for known high-traffic periods.
- **Health check misconfig:** Relax overly aggressive liveness/readiness thresholds, or separate liveness (process alive) from readiness (can serve traffic) checks if not already split.
- **Application bug (500):** Patch the specific exception path identified in the stack trace; add input validation/error handling around the failing call.

---

## 5. Verification (Recovery Confirmation)

Before closing the incident, confirm **all** of the following:

- [ ] `/checkout` error rate back to baseline (near 0% 5xx) for 15+ consecutive minutes
- [ ] All checkout-api pods/instances healthy and passing readiness checks
- [ ] Load balancer reports full expected healthy target count
- [ ] A real synthetic checkout transaction succeeds end-to-end (not just heartbeat)
- [ ] No recurrence of the specific 500 stack trace identified in Section 2
- [ ] No related connection pool or resource pressure signals in the same window

---

## 6. Post-Incident Actions

1. **Write postmortem** — include the 503/500 mix as a signal of fleet-wide instability, and note the heartbeat-recovered-but-unverified pattern consistent with prior incidents on this service.
2. **If deployment-caused:** update the deploy runbook/rollout config to prevent capacity gaps during future releases.
3. **If dependency-caused:** review circuit breaker and timeout configuration for all checkout-critical downstream calls.
4. **Add synthetic transaction monitoring** for `/checkout` specifically (not just heartbeat) so real checkout failures are detected directly rather than inferred from raw error logs.
5. **Correlate with other checkout-api incidents** (e.g., the Postgres pool exhaustion SOP) — repeated instability on this service may point to a broader capacity/dependency issue worth a dedicated review.

---

## 7. Escalation Path

| Condition | Action |
|---|---|
| 5xx errors continue >5 min past initial detection | Page secondary on-call |
| Root cause traces to a downstream dependency outage | Loop in the owning team for that dependency immediately |
| 500 stack trace indicates data corruption/payment risk | Escalate to service owner + engineering manager immediately, halt further deploys |
| Recurs within 24h | Escalate — treat as a systemic issue, not an isolated blip |

---

## Appendix: Quick Reference Commands

```bash
# Pod health across the fleet
kubectl get pods -l app=checkout-api -o wide

# Recent restarts / crash loops
kubectl get pods -l app=checkout-api -o json | jq '.items[].status.containerStatuses[].restartCount'

# Deployment/rollout history
kubectl rollout history deployment/checkout-api

# Tail application logs for the exact error window
kubectl logs -l app=checkout-api --since=5m | grep -E "500|503"

# Manual synthetic checkout test (adjust to your API)
curl -i -X POST https://internal-checkout-api/checkout \
  -H "Content-Type: application/json" \
  -d '{"test":"synthetic-check"}'

# Check load balancer target health (AWS ALB example)
aws elbv2 describe-target-health --target-group-arn <arn>
```
