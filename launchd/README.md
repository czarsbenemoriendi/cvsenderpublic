# launchd — nightly scout scheduling (macOS)

launchd (not cron) because a `StartCalendarInterval` job missed while the Mac
is **asleep fires on wake**; a missed cron job is lost. Research:
`research/2026-09-09-orchestration-tooling.md` §2 (Apple Daemons & Services
Guide, `launchd.plist(5)`).

Files:
- `pl.cvsender.scout.plist.template` — schedule: **08:07 and 17:42** daily
  (off-cron minutes on purpose), WorkingDirectory pinned to the repo, logs to
  `data/logs/`. Every `__HOME__` placeholder is substituted with your `$HOME`
  at install time — no machine-specific paths are committed.
- `bootstrap.sh` — renders the template into `~/Library/LaunchAgents/` and
  bootstraps the agent. Refuses to silently overwrite an edited installed
  plist (prints the diff instead).
- `scout.sh` — wrapper: self-locates the repo from its own path, `flock`
  guard against overlapping runs, then matcher + pruner (+ optional ATS
  watchlist poll) into `data/cvsender.db`, macOS notification with the
  fresh-queue count.

Interpreter: `scout.sh` uses `$CVSENDER_PYTHON` if set, then the Python.org
framework build, then `python3` from `PATH`.

## Install (once)

```bash
bash launchd/bootstrap.sh
```

(On older macOS where `bootstrap` is unknown: `launchctl load
~/Library/LaunchAgents/pl.cvsender.scout.plist`.)

## Verify it is loaded

```bash
launchctl print gui/$(id -u)/pl.cvsender.scout | head -20
launchctl list | grep cvsender
```

## Fire it manually (proof it works, ~1-2 min)

```bash
launchctl kickstart gui/$(id -u)/pl.cvsender.scout
tail -f data/logs/scout.out.log data/logs/scout.err.log
```

After the run: `sqlite3 data/cvsender.db 'SELECT source, COUNT(*) FROM offers
GROUP BY source;'` shows what the scout ingested.

## Changing the schedule

Edit `launchd/pl.cvsender.scout.plist.template` **in the repo**, then re-run
`bash launchd/bootstrap.sh` — if the installed copy diverges, the script
prints the diff and the exact `bootout`/`bootstrap` commands instead of
overwriting blindly.

## Uninstall

```bash
launchctl bootout gui/$(id -u)/pl.cvsender.scout
rm ~/Library/LaunchAgents/pl.cvsender.scout.plist
```

(`launchctl unload` + `rm` on older macOS.)
