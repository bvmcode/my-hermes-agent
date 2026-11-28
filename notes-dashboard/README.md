# Notes & Checklists dashboard

Tailnet-only web UI (stdlib HTTP, no frameworks) for the personal notes +
checklists data stored in `health.db` (tables `notes` and `checklists`).

- **Port:** 8081 (binds the Tailscale IP only — never 0.0.0.0)
- **Tabs:** Notes (ledger list) / Kanban (notes by status: staged / in progress / done / closed) / Checklist
- **Read-only by design:** all writes happen through the chat/Hermes path —
  the SQLite ledger stays the single writer
- **Endpoints:** `/_health`, `/api/notes`, `/api/kanban`, `/api/checklist`,
  `/api/checklist-stats`

## Deploy

1. Copy `dashboard.py` to the box (e.g. `/home/ubuntu/notes_dashboard/dashboard.py`)
2. Install the unit file (see `health-dashboard` for the pattern): user-level
   systemd unit `notes-dashboard.service` → `ExecStart=/usr/bin/python3 .../dashboard.py`
3. `systemctl --user daemon-reload && systemctl --user enable --now notes-dashboard`

Note: `checklists` table added to `health.db` (id, created_date, created_time,
title, note, done, done_at).
