# Hosting & keep-warm

The web interface is a small FastAPI app, so it runs comfortably on free
hosting tiers. The one rough edge those tiers share is the **cold start**:
platforms such as Render's free plan spin an instance down after a period
of inactivity (around 15 minutes), and the next visitor has to wait while
the container is started again.

This page explains how to make the hosted demo feel instant.

## The `/healthz` endpoint

The app exposes a lightweight liveness probe:

```text
GET /healthz  ->  200 {"status": "ok", "version": "<app version>"}
```

It returns immediately without touching the database or rendering a
template, which makes it cheap to call frequently — ideal as a keep-warm
and uptime-monitor target.

## Option 1 — Keep the instance warm (free)

Point an external uptime monitor at the app so it never goes idle:

1. Sign up for a free monitor such as [UptimeRobot](https://uptimerobot.com/)
   or [cron-job.org](https://cron-job.org/).
2. Add an HTTP(s) check for your deployment, e.g.
   `https://<your-app>.onrender.com/healthz`.
3. Set the interval to **5–10 minutes** (shorter than the host's idle
   timeout).

That keeps the container running, so visitors skip the cold start.

!!! note "Free-tier hours"
    Render's free plan includes a fixed number of instance-hours per month
    (about 750). A single always-on service fits within that budget, but if
    you run several free services they will share — and can exhaust — the
    same pool. Prefer a dedicated uptime monitor over a CI cron job for
    pinging: schedulers like GitHub Actions cron can drift by 15+ minutes,
    which is longer than the idle timeout.

## Option 2 — Use an always-on host (most reliable)

If you would rather not rely on pinging:

- **Render Starter** (paid) does not spin down — no code changes, just a
  plan upgrade.
- **[Fly.io](https://fly.io/)** can keep a minimum machine running
  (`min_machines_running = 1`) so there is effectively no cold start.
- **[Railway](https://railway.app/)** does not sleep services and bills by
  usage.

## Data persistence caveat

By default the app stores assessments in a local SQLite database. On hosts
with **ephemeral filesystems** (including Render's free tier), that file is
reset on every spin-down and redeploy — registered users and assessment
history will not survive. That is usually fine for a public demo.

To retain data, point the app at a managed database (for example a free
Postgres instance from Render, [Neon](https://neon.tech/), or
[Supabase](https://supabase.com/)) instead of file-backed SQLite.
