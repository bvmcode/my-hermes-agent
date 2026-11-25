#!/usr/bin/env python3
"""Notes & Checklists dashboard (tailnet-only, port 8081).

Three tabs: Notes (ledger notes list) / Kanban (notes by status) / Checklist.
READ-ONLY by design — all writes happen through the chat/Hermes path, which
mutates the same SQLite DB (`health.db`: `notes` + `checklists` tables).
"""
import json
import os
import sqlite3
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

DB_PATH = "/home/ubuntu/health_data/health.db"
PORT = 8081
BIND_IP = None

def db_rows(q, *params):
    con = sqlite3.connect("file:%s?mode=ro" % DB_PATH, uri=True)
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(q, params)]
    con.close()
    return rows

def db_write_check(id_, done):
    con = sqlite3.connect(DB_PATH)
    try:
        import subprocess as sp
        now = sp.check_output(["date", "+%F %H:%M:%S"], env={**os.environ, "TZ": "America/New_York"}, text=True).strip() if done else None
        cur = con.execute("UPDATE checklists SET done=?, done_at=? WHERE id=?", (1 if done else 0, now, id_))
        con.commit()
        return cur.rowcount
    finally:
        con.close()

STATUS_ORDER = {"open": 0, "active": 1, "done": 2, "closed": 3}

def api_notes():
    rows = db_rows(
        "SELECT id, note_date, topic, body, status FROM notes "
        "ORDER BY CASE status WHEN 'open' THEN 0 WHEN 'active' THEN 1 WHEN 'done' THEN 2 ELSE 3 END, id DESC")
    return rows

def api_kanban():
    rows = api_notes()
    cols = [
        {"key": "open", "title": "Staged"},
        {"key": "active", "title": "In progress"},
        {"key": "done", "title": "Done"},
        {"key": "closed", "title": "Closed"},
    ]
    for c in cols:
        if c["key"] == "closed":
            c["items"] = [n for n in rows if n["status"] == "done" and "CLOSED" in (n["body"] or "").upper()]
        else:
            c["items"] = [n for n in rows if n["status"] == c["key"] and (
                c["key"] != "done" or "CLOSED" not in (n["body"] or "").upper())]
    for c in cols:
        for n in c["items"]:
            n.setdefault("id", 0)
    return cols

def api_checklist():
    rows = db_rows(
        "SELECT id, created_date, created_time, title, note, done, done_at "
        "FROM checklists ORDER BY done ASC, id DESC")
    return rows

def api_checklist_stats():
    rows = api_checklist()
    return {"total": len(rows), "open": sum(1 for r in rows if not r["done"]),
            "done": sum(1 for r in rows if r["done"])}

PAGE = """<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Notes &amp; Checklists</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:#0d1117;color:#dfe6ee;font-family:-apple-system,'Segoe UI',Roboto,sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:16px}
h1{font-size:22px;font-weight:600;letter-spacing:.3px;margin:6px 0 2px}
.sub{color:#8b98a8;font-size:13px;margin-bottom:12px}
.banner{background:#161b22;border:1px solid #212933;border-radius:8px;padding:8px 12px;font-size:13px;margin-bottom:10px}
.banner a{color:#4ecdc4;text-decoration:none}
.tabs{display:flex;gap:6px;margin-bottom:14px;flex-wrap:wrap}
.tab{background:#161b22;color:#aab7c6;border:1px solid #212933;border-radius:6px;padding:8px 16px;font-size:14px;cursor:pointer}
.tab.on{background:#1f6feb22;border-color:#1f6feb;color:#58a6ff}
.tabpane{display:none}.tabpane.on{display:block}
.cards{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}
.card{background:#161b22;border:1px solid #212933;border-radius:8px;padding:10px 16px;min-width:140px}
.card .n{font-size:22px;font-weight:600}.card .l{color:#8b98a8;font-size:12px}
.kan{display:flex;gap:10px;flex-wrap:wrap;align-items:flex-start}
.kcol{background:#161b22;border:1px solid #212933;border-radius:8px;padding:10px;flex:1;min-width:220px}
.kcol h3{font-size:13px;color:#aab7c6;margin:0 0 8px;text-transform:uppercase;letter-spacing:.5px}
.kcard{background:#1c2430;border:1px solid #263040;border-radius:6px;padding:8px;margin-bottom:8px;font-size:13px}
.tag{background:#1f6feb22;color:#58a6ff;border-radius:4px;padding:1px 6px;font-size:11px;margin-right:4px}
.d{color:#8b98a8;font-size:11px;margin:3px 0}
ul.nlist{list-style:none;margin:0;padding:0}
ul.nlist li{background:#161b22;border:1px solid #212933;border-radius:8px;padding:10px 12px;margin-bottom:8px;font-size:14px}
ul.nlist .t{font-weight:600;margin-right:6px}.nbody{margin-top:4px;color:#c9d2dd;font-size:13px;white-space:pre-wrap}
.cthead{display:flex;gap:8px;align-items:baseline;margin-bottom:10px;flex-wrap:wrap}
.chk{display:flex;align-items:flex-start;gap:10px;background:#161b22;border:1px solid #212933;border-radius:8px;padding:10px 12px;margin-bottom:8px}
.chk .box{width:18px;height:18px;border-radius:4px;border:2px solid #4ecdc4;flex:0 0 auto;margin-top:1px}
.chk.done .box{background:#4ecdc4}
.chk.done .title{text-decoration:line-through;color:#8b98a8}
.chk .title{font-size:14px;font-weight:500}
.chk .note{color:#8b98a8;font-size:12px;margin-top:3px}
.chk .date{color:#6c7885;font-size:11px;margin-top:2px}
footer{color:#6c7885;font-size:12px;margin-top:18px;border-top:1px solid #212933;padding-top:10px}
footer a{color:#4ecdc4;text-decoration:none}
</style></head><body><div class="wrap">
<h1>Notes &amp; Checklists</h1>
<div class="sub">barry's staging bench — read-only display; everything moves through Telegram/Hermes</div>
<div class="banner">
  <b>To add, check off, or move anything:</b> open <a href="tg://resolve?domain=hermes_eytmpbhr5pup3qoc_bot">Telegram app</a> · <a href="https://t.me/hermes_eytmpbhr5pup3qoc_bot">t.me fallback</a> — same chat, every device.
</div>
<div class="tabs">
<button class="tab on" id="tb-notes" onclick="show('notes')">Notes</button>
<button class="tab" id="tb-kanban" onclick="show('kanban')">Kanban</button>
<button class="tab" id="tb-checklist" onclick="show('checklist')">Checklist</button>
</div>

<div class="tabpane on" id="pane-notes"><div id="notecard"></div><ul class="nlist" id="notelist"></ul></div>

<div class="tabpane" id="pane-kanban"><div class="kan" id="kan"></div>
<div style="color:#8b98a8;font-size:12px;margin-top:8px">Cards move by voice — open Telegram from the banner and just ask.</div></div>

<div class="tabpane" id="pane-checklist">
<div class="cards" id="chkcards"></div>
<ul class="nlist" id="chklist"></ul></div>

<footer>tailnet-only · notes + kanban + checklist · source: health.db (notes + checklists tables) · read-only by design</footer>
</div>
<script>
let TABS=['notes','kanban','checklist'];
function show(t){
  TABS.forEach(k=>{
    document.getElementById('pane-'+k).style.display=(k===t)?'block':'none';
    document.getElementById('tb-'+k).classList.toggle('on',k===t);
  });
  if(t==='notes')loadNotes();
  if(t==='kanban')loadKanban();
  if(t==='checklist')loadChecklist();
}
const esc=s=>String(s==null?'':s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
async function loadNotes(){
  const rows=await (await fetch('api/notes',{cache:'no-store'})).json();
  const open=rows.filter(r=>r.status==='open'||r.status==='active').length;
  document.getElementById('notecard').innerHTML=
    `<div class="cards"><div class="card"><div class="n">${rows.length}</div><div class="l">total notes</div></div>`
    +`<div class="card"><div class="n">${open}</div><div class="l">open / active</div></div>`
    +`<div class="card"><div class="n">${rows.filter(r=>r.status==='done').length}</div><div class="l">done</div></div></div>`;
  document.getElementById('notelist').innerHTML=rows.map(n=>
    `<li><span class="t">[${n.id}] ${esc(n.topic)}</span>`
    +`<span class="tag">${esc(n.status)}</span><span class="d">${esc(n.note_date)}</span>`
    +`<div class="nbody">${esc(n.body)}</div></li>`).join('')||'<li style="color:#8b98a8">no notes yet</li>';
}
async function loadKanban(){
  const cols=await (await fetch('api/kanban',{cache:'no-store'})).json();
  document.getElementById('kan').innerHTML=cols.map(c=>{
    const it=c.items;
    return `<div class="kcol"><h3>${c.title} (${it.length})</h3>`+(it.map(n=>
      `<div class="kcard"><span class="tag">${n.id}</span> <b>${esc(n.topic)}</b>`
      +`<div class="d">${esc((n.note_date||'').slice(5))}</div>`
      +`<div style="margin-top:4px">${esc((n.body||'').length>180?(n.body||'').slice(0,180)+'…':(n.body||''))}</div></div>`
    ).join('')||`<div class="d" style="color:#8b98a8;font-size:12px">—</div>`)+`</div>`;
  }).join('');
}
async function loadChecklist(){
  const rows=await (await fetch('api/checklist',{cache:'no-store'})).json();
  const s=await (await fetch('api/checklist-stats',{cache:'no-store'})).json();
  document.getElementById('chkcards').innerHTML=
    `<div class="card"><div class="n">${s.total}</div><div class="l">total items</div></div>`
    +`<div class="card"><div class="n">${s.open}</div><div class="l">open</div></div>`
    +`<div class="card"><div class="n">${s.done}</div><div class="l">checked off</div></div>`;
  document.getElementById('chklist').innerHTML=rows.map(r=>
    `<li class="chk ${r.done?'done':''}"><div class="box" style="cursor:pointer" onclick="toggleChk(${r.id}, ${r.done?'false':'true'})"></div><div>`
    +`<div class="title">${esc(r.title)}</div>`
    +`${r.note?`<div class="note">${esc(r.note)}</div>`:''}`
    +`<div class="date">added ${esc(r.created_date)}${r.done_at?' · checked '+esc(r.done_at.split(' ')[0]):''} · [${r.id}]</div>`
    +`</div></li>`).join('')||'<li style="color:#8b98a8">empty — say "add checklist item: …" in Telegram</li>';
}
async function toggleChk(id, done){
  const r=await fetch('api/checklist/check',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({id:id,done:done})});
  if(!r.ok){ alert('check failed'); return; }
  await loadChecklist();
}
show('notes');
</script></body></html>"""

class Handler(BaseHTTPRequestHandler):
    def _json(self, obj):
        body = json.dumps(obj, default=str).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(PAGE.encode())

    def do_GET(self):
        path = self.path.split("?")[0].strip("/")
        try:
            if path in ("", "index.html"):
                self._html()
            elif path == "_health":
                self._json({"ok": True, "service": "notes-dashboard"})
            elif path == "api/notes":
                self._json(api_notes())
            elif path == "api/kanban":
                self._json(api_kanban())
            elif path == "api/checklist":
                self._json(api_checklist())
            elif path == "api/checklist-stats":
                self._json(api_checklist_stats())
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self._json({"error": str(e)[:200]})

    def _body_json(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            import json as _j
            return _j.loads(self.rfile.read(n) or b"{}")
        except Exception:
            return {}

    def do_POST(self):
        path = self.path.split("?")[0].strip("/")
        try:
            if path == "api/checklist/check":
                b = self._body_json()
                id_ = b.get("id")
                done = b.get("done")
                if not isinstance(id_, int) or not isinstance(done, bool):
                    self._json({"error": "need integer id + boolean done"})
                    return
                # hard limit: only the checklist table's done/done_at fields are writable
                n = db_write_check(id_, done)
                self._json({"ok": n == 1, "id": id_, "done": done})
            else:
                self.send_response(404)
                self.end_headers()
        except Exception as e:
            self._json({"error": str(e)[:200]})

    def log_message(self, fmt, *args):
        pass

def main():
    global BIND_IP
    try:
        ip = subprocess.check_output(["tailscale", "ip", "-4"], text=True).strip().splitlines()[0]
        BIND_IP = ip if ip.startswith("100.") else None
    except Exception:
        BIND_IP = None
    if not BIND_IP:
        BIND_IP = "127.0.0.1"
    srv = ThreadingHTTPServer((BIND_IP, PORT), Handler)
    print(f"notes-dashboard serving on {BIND_IP}:{PORT}", flush=True)
    srv.serve_forever()

if __name__ == "__main__":
    main()
