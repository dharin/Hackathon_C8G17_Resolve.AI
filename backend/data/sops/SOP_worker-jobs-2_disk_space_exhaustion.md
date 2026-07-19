# Standard Operating Procedure (SOP)
## Disk Space Exhaustion — worker-jobs-2 (/var/log)

| Field | Value |
|---|---|
| Service | worker-jobs-2 |
| Failure Mode | Disk full on `/var/log` → write failures → silent partial recovery |
| Severity | SEV-2 (degraded/at-risk; escalates to SEV-1 if job writes fail) |
| Owner | Platform/Infra On-Call |
| Last Updated | 2026-07-19 |

---

## 1. Trigger / Detection

This SOP applies when logs show this pattern:

```
ERROR  write failed: no space left on device
WARN   disk usage at NN% full on /var/<path>
INFO   heartbeat ok   <-- can reappear even though disk is still nearly full
```

**Reference incident timeline:**

| Time (UTC) | Level | Event | Meaning |
|---|---|---|---|
| 03:01:00 | INFO | heartbeat ok | Service healthy |
| 03:05:10 | ERROR | write failed: no space left on device | A write operation was actively rejected by the OS |
| 03:05:11 | WARN | disk usage at 96% full on /var/log | Confirms root cause: log partition near capacity |
| 03:06:00 | INFO | heartbeat ok | **Heartbeat recovered — but disk is still ~96% full** |

**Key insight — do not close this as resolved just because heartbeat is green again.** A heartbeat check typically doesn't write meaningful volume to disk, so it can pass while the disk is still critically full. The underlying condition (96% full) has **not** been fixed by the heartbeat succeeding. Treat this as still-active until disk usage is verified below a safe threshold.

---

## 2. Immediate Response (Target: first 5 minutes)

**Goal: prevent total disk exhaustion (100%) and any resulting job/data loss.**

1. **Acknowledge & confirm current state**
   ```
   df -h /var/log
   ```
   Confirm current usage % — don't rely on the log timestamp alone, it may already have changed.

2. **Identify what's consuming the space**
   ```
   du -sh /var/log/* | sort -rh | head -20
   ```
   Look specifically for:
   - A single runaway log file (common: verbose/debug logging left on, or a crash loop spamming logs)
   - Old rotated logs (`.gz`, `.1`, `.log.old`) that were never cleaned up
   - Core dumps in the same partition

3. **Free space immediately (safe actions first)**
   ```
   # Remove old compressed/rotated logs (safe — already rotated)
   find /var/log -name "*.gz" -mtime +7 -delete
   find /var/log -name "*.log.[0-9]*" -mtime +7 -delete

   # If a specific log file is the runaway offender, truncate (don't delete a file
   # a process still has open — deleting won't free space until the process restarts)
   truncate -s 0 /var/log/<offending-file>.log
   ```
   > **Do not** `rm` a log file that a running process still has open — the space won't be reclaimed until the process exits/restarts, and you lose the ability to inspect it. Use `truncate` instead, or `> /var/log/file.log`.

4. **Re-check usage**
   ```
   df -h /var/log
   ```
   Target: below 85% before moving on.

5. **Confirm worker-jobs-2 is actually writing successfully again**
   - Don't trust heartbeat alone — check application logs for new `write failed` entries after your cleanup, and confirm any job that failed at 03:05:10 either completed or was retried.

---

## 3. Root Cause Investigation (Target: next 15–30 minutes)

| # | Check | How |
|---|---|---|
| 1 | **Log verbosity misconfiguration** | Check if log level was recently changed to DEBUG/TRACE, or a new deploy added noisy logging. |
| 2 | **Missing/broken log rotation** | `cat /etc/logrotate.d/<service>` — confirm a logrotate config exists, is syntactically valid, and cron/systemd timer for logrotate is actually running (`systemctl status logrotate.timer` or check cron logs). |
| 3 | **Crash loop / retry storm** | Check for a process repeatedly crashing and re-logging startup errors — this can fill disk fast. `journalctl -u worker-jobs-2 --since "1 hour ago" | wc -l` to gauge log volume rate. |
| 4 | **Undersized volume** | Confirm whether `/var/log` has adequate allocated capacity for this service's normal log volume, or whether this is a recurring pattern (check disk usage trend over past weeks). |
| 5 | **Shared partition contention** | Confirm `/var/log` isn't shared with other services/containers that are also writing heavily, masking the true source. |
| 6 | **Job-specific artifact leak** | If worker-jobs-2 writes job output/temp files under `/var/log` by mistake (wrong path config), confirm intended log path vs. actual write path. |

---

## 4. Remediation Actions

Apply based on confirmed root cause from Section 3:

- **Verbosity misconfig:** Revert log level to INFO/WARN in prod; redeploy or hot-reload config.
- **Broken/missing rotation:** Install or fix `logrotate` config with sane `rotate`, `maxsize`, and `compress` settings; verify the timer/cron actually fires (test with `logrotate -f <config>`).
- **Crash loop:** Fix the underlying crash cause (see application error logs); the log growth is a symptom, not the disease.
- **Undersized volume:** Expand the volume/partition, or move logs to a dedicated larger volume separate from OS/app-critical paths.
- **No single cause / recurring risk:** Set up a disk usage alert well before critical (e.g., WARN at 75%, page at 90%) so this is caught before write failures occur.

---

## 5. Verification (Recovery Confirmation)

Before closing the incident, confirm **all** of the following:

- [ ] `df -h /var/log` shows usage below a safe threshold (e.g., <70%)
- [ ] No new `write failed: no space left on device` entries in logs
- [ ] Root cause of space consumption identified and addressed (not just cleaned up)
- [ ] Logrotate (or equivalent) confirmed working going forward
- [ ] worker-jobs-2 heartbeat *and* actual job writes both confirmed successful — not heartbeat alone
- [ ] Any job(s) that failed during the write error window have been identified, and re-run/reprocessed if needed

---

## 6. Post-Incident Actions

1. **Write postmortem** — note that heartbeat falsely signaled recovery at 03:06 while disk was still ~96% full; flag this as a monitoring gap.
2. **Fix the monitoring gap** — heartbeat/health checks should ideally include a disk-space check, not just process liveness, so "healthy" actually means healthy.
3. **Add proactive disk usage alerting** with staged thresholds (e.g., 75% WARN, 90% CRITICAL) instead of discovering issues via write-failure errors.
4. **Audit logrotate configs** across other services for the same gap if one is found here.
5. **Check for data loss** — confirm whether the write at 03:05:10 represented lost job data, and whether it needs to be replayed/recovered.

---

## 7. Escalation Path

| Condition | Action |
|---|---|
| Disk hits 100% / cannot free space via safe cleanup | Escalate to Infra/SRE for emergency volume expansion |
| Job data loss confirmed | Loop in service owner + data team to assess reprocessing needs |
| Recurs within 24h after cleanup | Escalate — indicates active runaway process, not one-time spike |

---

## Appendix: Quick Reference Commands

```bash
# Check disk usage
df -h /var/log

# Find largest space consumers
du -sh /var/log/* | sort -rh | head -20

# Safely clear old rotated logs
find /var/log -name "*.gz" -mtime +7 -delete

# Truncate a file still held open by a running process (safe, doesn't break the file handle)
truncate -s 0 /var/log/<file>.log

# Force a logrotate test run
logrotate -f /etc/logrotate.d/<service>

# Check whether logrotate timer is active
systemctl status logrotate.timer

# Watch disk usage live during remediation
watch -n 5 df -h /var/log
```
