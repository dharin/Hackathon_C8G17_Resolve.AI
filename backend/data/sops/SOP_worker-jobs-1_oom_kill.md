# Standard Operating Procedure (SOP)
## OOM Kill (Out of Memory) — worker-jobs-1 (java process)

| Field | Value |
|---|---|
| Service | worker-jobs-1 |
| Failure Mode | Kernel OOM-killer terminates process → process restart masks underlying issue |
| Severity | SEV-1 (data/job loss risk — process was killed mid-execution, not gracefully stopped) |
| Owner | Platform/Infra On-Call + Service Owner |
| Last Updated | 2026-07-19 |

---

## 1. Trigger / Detection

This SOP applies when logs show this pattern:

```
ERROR  kernel: Out of memory: Killed process <PID> (<process-name>) total-vm:<size>kB
ERROR  kernel: oom-killer invoked, gfp_mask=0x...
INFO   heartbeat ok   <-- reappears after restart, does NOT mean the cause is fixed
```

**Reference incident timeline:**

| Time (UTC) | Level | Event | Meaning |
|---|---|---|---|
| 02:10:01 | INFO | heartbeat ok | Service healthy |
| 02:14:22 | ERROR | Killed process 4821 (java) total-vm:4200000kB | Kernel forcibly killed the JVM — it had ~4.2GB virtual memory allocated |
| 02:14:23 | ERROR | oom-killer invoked, gfp_mask=0x140cca | Confirms this was a kernel-level OOM event, not an app-level crash |
| 02:15:00 | INFO | heartbeat ok | **Process restarted (likely via systemd/supervisor) — heartbeat passing again, but memory pressure cause is unaddressed** |

**Key insight — a returning heartbeat here almost certainly means an auto-restart occurred, not that anything was fixed.** The OOM-killer is a last-resort kernel action: it only fires when the system is critically low on memory and something must die *right now* to keep the host alive. Whatever job(s) the java process was running at 02:14:22 were terminated **mid-execution**, with no graceful shutdown — treat this as a probable data-loss/incomplete-job event, not just a blip.

---

## 2. Immediate Response (Target: first 5–10 minutes)

**Goal: confirm the process is stable post-restart, assess what was lost, and check if the host is still under memory pressure.**

1. **Confirm current process state**
   ```
   systemctl status worker-jobs-1
   ps aux | grep java
   ```
   Verify the restarted process is actually up and not in a crash loop.

2. **Check current memory pressure on the host** (the OOM condition may still be active/recurring)
   ```
   free -h
   dmesg -T | grep -i "oom\|killed process" | tail -20
   ```
   If OOM events are recurring (multiple kills in the dmesg output), this is still an active incident, not a one-off.

3. **Identify what job(s) were in-flight at time of kill**
   - Check worker-jobs-1's job queue/tracking system for any job marked "in progress" with a start time before 02:14:22 that never completed.
   - These jobs likely need to be identified as failed/incomplete and re-queued — a killed process does not get to checkpoint or clean up.

4. **Check for other processes affected**
   - The OOM-killer can kill *any* process on the host, not necessarily the one causing the pressure. Confirm no other critical services on the same host were also killed:
   ```
   dmesg -T | grep -i "killed process"
   ```

5. **If memory pressure is ongoing**, consider immediate relief:
   - Restart other non-critical processes on the same host to free memory, or
   - If containerized/orchestrated, cordon the node and let the scheduler reschedule pods elsewhere while you investigate.

---

## 3. Root Cause Investigation (Target: next 20–40 minutes)

| # | Check | How |
|---|---|---|
| 1 | **JVM heap vs. container/host memory limit mismatch** | Check `-Xmx` heap setting vs. actual container memory limit (if containerized) or host RAM. A common cause: `-Xmx` set close to or above the container's memory limit, leaving no room for off-heap memory (metaspace, thread stacks, direct buffers). |
| 2 | **Memory leak** | Check if RSS/heap usage for this process has been trending upward over hours/days prior to the kill (via monitoring/APM if available). A leak looks like steady growth with no correlated drop (no GC recovery). |
| 3 | **Sudden spike from job size** | Check if the specific job(s) running at 02:14:22 processed an unusually large payload/batch compared to normal. |
| 4 | **Other memory consumers on host** | `ps aux --sort=-%mem | head -10` (post-incident, or check historical monitoring) — confirm no other process/container was co-located and competing for the same memory. |
| 5 | **Missing/misconfigured memory limits or swap** | Confirm whether swap is enabled (masking pressure until it's severe) and whether the process has appropriate `cgroup`/container memory limits set so it fails predictably rather than taking down the host. |
| 6 | **GC configuration** | Check GC logs (if enabled) for signs the JVM was thrashing (frequent full GCs, `GC overhead limit exceeded`) just before the kill — indicates heap was undersized for the actual working set. |

---

## 4. Remediation Actions

Apply based on confirmed root cause from Section 3:

- **Heap/container mismatch:** Set `-Xmx` conservatively below the container/host memory limit (commonly 60–75% of the limit, leaving room for off-heap usage), or set `-XX:MaxRAMPercentage` instead of a fixed `-Xmx` so it scales correctly with the container.
- **Memory leak:** Capture a heap dump on next occurrence (`-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=...`) and profile it to find the leaking object graph; patch and deploy.
- **Job size spike:** Add batch-size limits/pagination so a single job can't unboundedly grow memory usage; consider streaming instead of loading full payloads into memory.
- **Host contention:** Move co-located processes to separate hosts/nodes, or set proper resource requests/limits so the scheduler doesn't over-pack the host.
- **No safety net configured:** At minimum, enable heap dump on OOM and add process-level memory alerting so you get a warning before the kernel intervenes.

---

## 5. Verification (Recovery Confirmation)

Before closing the incident, confirm **all** of the following:

- [ ] `dmesg` shows no further OOM-kill events for this host over a sustained monitoring window
- [ ] worker-jobs-1 process memory usage stable/within expected bounds (not climbing)
- [ ] All in-flight jobs from the kill window identified and re-queued/reprocessed as needed
- [ ] Heartbeat confirmed alongside actual job throughput — not heartbeat alone
- [ ] JVM heap/container memory settings reviewed and corrected if mismatched

---

## 6. Post-Incident Actions

1. **Write postmortem** — explicitly note that the 02:15:00 heartbeat was a restart artifact, not confirmation of resolution, and that job(s) in flight at kill time were lost mid-execution.
2. **Assess and recover lost work** — confirm whether any customer-facing or downstream impact resulted from the killed job(s); reprocess as needed.
3. **Right-size memory configuration** — align JVM heap flags with actual container/host limits (see Section 4).
4. **Add proactive memory alerting** — alert on sustained high memory usage (e.g., >85%) before OOM-killer intervention, not just on kernel kill events after the fact.
5. **Enable heap dump on OOM** going forward so any recurrence is immediately diagnosable without waiting to reproduce.
6. **Review process supervision behavior** — confirm systemd/supervisor restart policy is appropriate (e.g., not restart-looping if OOM recurs rapidly) and alerts on repeated restarts.

---

## 7. Escalation Path

| Condition | Action |
|---|---|
| Repeated OOM kills within a short window (crash loop) | Escalate to Infra/SRE — likely needs immediate resource limit fix or node cordon |
| Confirmed job/data loss with downstream impact | Loop in service owner + affected downstream teams |
| Root cause not identified within 1 hour | Escalate to engineering manager; consider capturing heap dump on next occurrence as a forcing function |

---

## Appendix: Quick Reference Commands

```bash
# Check current memory state
free -h

# Review kernel OOM history
dmesg -T | grep -i "oom\|killed process"

# Check process status
systemctl status worker-jobs-1

# Top memory consumers right now
ps aux --sort=-%mem | head -10

# Confirm JVM heap flags in use
ps -p <PID> -o cmd | grep -o '\-Xmx[^ ]*'

# Enable heap dump on next OOM (add to JVM startup flags)
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/var/dumps/

# Check container memory limit (if containerized)
cat /sys/fs/cgroup/memory/memory.limit_in_bytes   # cgroup v1
cat /sys/fs/cgroup/memory.max                      # cgroup v2
```
