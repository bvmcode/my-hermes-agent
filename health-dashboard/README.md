# Health Dashboard

A tailnet-only web dashboard over a SQLite health ledger: charts, a date-selectable
food log, and a meds view. No frameworks, no build step — one Python file serves
everything, using the standard library plus Chart.js from a CDN.

This is the **sanitized, personal-data-free copy** of a dashboard running in
production: no names, no medication names, no dates. See *Personalization* below.

## What it shows

- **Overview** — KPI cards and four charts, each with a stat bar underneath:
  - Fasting glucose (line + 130 mg/dL reference line): max / min / median / trend (first → last)
  - Weight, Tue+Sat points: max / min / median / trend
  - Blood pressure: separate SYS and DIA stat lines with trend
  - Daily calories & carbs (21-day bars + carb line): max / min / median / 7-day avg vs prior 7
- **Food** — pick any date (prev/next buttons included); totals strip plus rolling
  context: 7-day avg calories, 14-day median, 7-day avg protein and carbs, and how
  the selected day compares to the 7-day average.
- **Meds** — standing daily medications (Drug / Dose / Schedule / optional "For") and
  the dose history from the `medications` table.
- **Workouts** — sessions/total-minutes/longest-streak/current-streak cards, an
  active-minutes bar chart, and the workout history table.

## Files

```
health-dashboard/
├── dashboard.py               # the whole app (server + UI + stats)
├── health-dashboard.service   # systemd --user unit template
└── README.md
```

## Install

1. Copy `dashboard.py` to the host and edit the config block at the top:
   - `DB` — path to your SQLite ledger
   - `PORT` — default 8080
   - `MED_START` — `date(...)` of a first weekly injection to enable an
     "on-regimen day N" counter, or `None` (default) to hide it
2. Adjust `health-dashboard.service` if you moved the script, then install:

   ```
   install -m 644 health-dashboard.service ~/.config/systemd/user/
   systemctl --user daemon-reload
   systemctl --user enable --now health-dashboard
   ```

   Linger must be on for user units to survive logout/reboot (`loginctl
   show-user $USER | grep -i linger`); if it's off: `sudo loginctl enable-linger $USER`.
3. Verify:

   ```
   curl http://<tailscale-ip>:8080/_health        # -> {"ok":true}
   curl http://<tailscale-ip>:8080/api/meals?date=$(date +%F) | head -c 200
   ```

   Then from any other device on the tailnet: `http://<tailscale-ip>:8080` or
   `http://<hostname>:8080` (MagicDNS).

## Security model

- The server binds **only** the tailscale interface IP (resolved at startup via
  `tailscale ip -4`, fallback 127.0.0.1) — the public interface never listens, so
  no port-forwarding, no inbound cloud firewall changes, no auth burden. Privacy
  = tailnet membership + WireGuard encryption.
- Browsers may show an "Not secure / HTTP" warning on iOS/Android. Expected:
  the page rides inside the encrypted tunnel in plain HTTP.
- All database access is read-only (`sqlite3.connect("file:...?mode=ro", uri=True)`).
  Data entry happens through whatever logging pipeline writes the ledger, not this app.

## Endpoints

| Path | Purpose |
|---|---|
| `/` | the single-page UI |
| `/api/data` | readings, per-day meal totals, daily meds, dose history, workouts |
| `/api/meals?date=YYYY-MM-DD` | one day's meal rows + totals + rolling stats |
| `/_health` | reachability probe (`{"ok":true}`) |

## Ledger schema expected by the dashboard

- `daily_readings(reading_date, glucose_mg_dl, systolic, diastolic, weight_kg, …)`
- `meals(meal_date, meal_type, eat_time, description, calories, carbs_g, protein_g, fat_g, fiber_g, sugar_g, notes)`
- `medications(dose_date, dose_time, drug, dose_amount, notes)` — dose history
- `daily_meds(med_date, drug, dose_amount, schedule, notes)` — standing regimen;
  a note containing `NEW` renders as "recently started", otherwise "long-standing"
- `workouts(workout_date, done_time, activity, duration_min, intensity, notes)` —
  workout log powering the Workouts tab

## Personalization (deliberately omitted here)

The production copy personalizes three things, none of which belong in a public repo:

1. the HTML title/h1,
2. `MED_START` (a first-injection date) — `None` here by default,
3. the `PURPOSE` map on the Meds tab (drug keyword → what it's for). Empty dict
   here; the commented example in `dashboard.py` shows the shape.
