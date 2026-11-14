#!/usr/bin/python3
"""Health dashboard - tailnet-only web UI over a SQLite health ledger.

Tabs: Overview (charts + stat bars) / Food (date-selectable log) / Meds.
No frameworks, no build step: stdlib HTTP + Chart.js CDN.
"""
import json
import sqlite3
import subprocess
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from zoneinfo import ZoneInfo

PORT = 8080
DB = "/home/ubuntu/health_data/health.db"
ET = ZoneInfo("America/New_York")

# Set to the date of your first weekly injection (e.g. date(2026, 11, 7)) to show an
# "on regimen day N" counter; leave as None to hide it entirely.
MED_START = None


def tailscale_ip():
    try:
        out = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True, timeout=5)
        lines = [s for s in out.stdout.strip().splitlines() if s.strip()]
        return lines[0] if lines else "127.0.0.1"
    except Exception:
        return "127.0.0.1"


HOST = tailscale_ip()


def db_rows(query, args=()):
    con = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(query, args).fetchall()]
    finally:
        con.close()


def lbs(kg):
    return round(kg * 2.2046226218, 1) if kg is not None else None


def api_data():
    readings = db_rows(
        "SELECT reading_date, glucose_mg_dl, systolic, diastolic, weight_kg "
        "FROM daily_readings ORDER BY reading_date"
    )
    readings = [
        {"date": r["reading_date"], "glucose": r["glucose_mg_dl"], "sys": r["systolic"],
         "dia": r["diastolic"], "weight_lbs": lbs(r["weight_kg"])}
        for r in readings
    ]
    by_day = db_rows(
        "SELECT meal_date, SUM(calories) cal, SUM(carbs_g) carbs, "
        "SUM(protein_g) protein, SUM(sugar_g) sugar FROM meals GROUP BY meal_date ORDER BY meal_date"
    )
    last7 = [d for d in by_day if d["cal"] is not None][-7:]
    meds = db_rows(
        "SELECT dose_date, dose_time, drug, dose_amount, notes FROM medications "
        "ORDER BY dose_date DESC, dose_time DESC"
    )
    daily_meds = db_rows(
        "SELECT med_date, drug, dose_amount, schedule, notes FROM daily_meds ORDER BY drug"
    )
    today = datetime.now(ET).date()
    regimen_day = (today - MED_START).days + 1 if MED_START else None
    return {
        "generated": datetime.now(ET).isoformat(timespec="seconds"),
        "et_date": today.isoformat(),
        "regimen_day": regimen_day,
        "avg7_cal": round(sum(d["cal"] for d in last7) / len(last7)) if last7 else None,
        "readings": readings,
        "by_day": [
            {**d, "cal": d["cal"] or 0, "carbs": d["carbs"] or 0,
             "protein": d["protein"] or 0, "sugar": d["sugar"] or 0}
            for d in by_day
        ],
        "meds": meds,
        "daily_meds": daily_meds,
    }


def api_meals(qdate):
    rows = db_rows(
        "SELECT id, meal_type, eat_time, description, calories, carbs_g, protein_g, "
        "fat_g, fiber_g, sugar_g, notes FROM meals WHERE meal_date=? ORDER BY eat_time",
        (qdate,)
    )
    tot = db_rows(
        "SELECT SUM(calories) cal, SUM(carbs_g) carbs, SUM(protein_g) protein, "
        "SUM(sugar_g) sugar, SUM(fat_g) fat, COUNT(*) n FROM meals WHERE meal_date=?",
        (qdate,)
    )
    days = db_rows(
        "SELECT meal_date, SUM(calories) cal, SUM(protein_g) protein, SUM(carbs_g) carbs "
        "FROM meals GROUP BY meal_date HAVING SUM(calories)>0 ORDER BY meal_date"
    )
    def median(v):
        s = sorted(v)
        if not s:
            return 0
        return s[len(s)//2] if len(s) % 2 else (s[len(s)//2 - 1] + s[len(s)//2]) / 2
    last7 = days[-7:]
    l14 = days[-14:]
    stats = {
        "cal7avg": round(sum(d["cal"] for d in last7) / len(last7)) if last7 else None,
        "cal14med": round(median([d["cal"] for d in l14])) if l14 else None,
        "prot7avg": round(sum((d["protein"] or 0) for d in last7) / len(last7)) if last7 else None,
        "carbs7avg": round(sum((d["carbs"] or 0) for d in last7) / len(last7)) if last7 else None,
    }
    t = tot[0] if tot else {}
    return {
        "date": qdate,
        "rows": rows,
        "totals": {
            "cal": t.get("cal") or 0, "carbs": t.get("carbs") or 0,
            "protein": t.get("protein") or 0, "sugar": t.get("sugar") or 0,
            "fat": t.get("fat") or 0, "rows": t.get("n") or 0,
        },
        "stats": stats,
    }


HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Health Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0e1116;--card:#161b22;--line:#232a33;--txt:#e6edf3;--mut:#8b98a8;--acc:#4ecdc4}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:15px/1.45 -apple-system,Segoe UI,Roboto,sans-serif}
.wrap{max-width:1100px;margin:0 auto;padding:20px 16px 60px}
h1{font-size:20px;margin:0 0 2px}.sub{color:var(--mut);font-size:13px;margin-bottom:14px}
.tabs{display:flex;gap:8px;margin-bottom:16px}
.tab{padding:8px 16px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--mut);cursor:pointer;font-size:14px;font-weight:600}
.tab.on{color:var(--txt);border-color:var(--acc);background:#1a2430}
.tabpane{display:none}.tabpane.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin-bottom:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .k{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.4px}
.card .v{font-size:26px;font-weight:700;margin-top:4px}.card .d{color:var(--mut);font-size:12px;margin-top:2px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}@media(max-width:760px){.grid{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.panel h2{font-size:14px;margin:0 0 10px;color:var(--mut);font-weight:600}
.statline{display:flex;flex-wrap:wrap;gap:14px;color:var(--mut);font-size:12px;margin-top:8px}
.statline b{color:var(--txt);font-weight:600}
.panel.wide{grid-column:1/-1;overflow:auto}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:var(--mut);text-align:left;font-weight:600;padding:6px 8px;border-bottom:1px solid var(--line)}
td{padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.tag{display:inline-block;padding:1px 7px;border-radius:20px;font-size:11px;background:#21262d;color:var(--mut)}
.datebar{display:flex;align-items:center;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.datebar button{background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:7px 12px;cursor:pointer;font-size:14px}
.datebar input{background:var(--card);border:1px solid var(--line);color:var(--txt);border-radius:8px;padding:7px 10px;font-size:14px;color-scheme:dark}
.datebar .tot{color:var(--mut);font-size:13px}
.totcard{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:14px}
.totcard .card{padding:10px 14px}.totcard .v{font-size:20px}
footer{color:var(--mut);font-size:11px;margin-top:22px;text-align:center}
</style>
</head>
<body>
<div class="wrap">
<h1>Health Dashboard</h1>
<div class="sub" id="sub">loading…</div>
<div class="tabs">
<button class="tab on" id="tb-ov" onclick="show('ov')">Overview</button>
<button class="tab" id="tb-food" onclick="show('food')">Food</button>
<button class="tab" id="tb-meds" onclick="show('meds')">Meds</button>
</div>

<div class="tabpane on" id="pane-ov">
<div class="cards" id="cards"></div>
<div class="grid">
<div class="panel"><h2>Fasting glucose (mg/dL)</h2><canvas id="glc"></canvas><div class="statline" id="st-glc"></div></div>
<div class="panel"><h2>Weight (lbs) — Tue + Sat</h2><canvas id="wt"></canvas><div class="statline" id="st-wt"></div></div>
<div class="panel"><h2>Blood pressure</h2><canvas id="bp"></canvas><div class="statline" id="st-bp"></div></div>
<div class="panel"><h2>Daily calories &amp; carbs</h2><canvas id="cal"></canvas><div class="statline" id="st-cal"></div></div>
</div>
</div>

<div class="tabpane" id="pane-food">
<div class="datebar">
<button onclick="shiftDay(-1)">‹ prev</button>
<input type="date" id="fooddate" onchange="loadFood()">
<button onclick="shiftDay(1)">next ›</button>
<span class="tot" id="foodnote"></span>
</div>
<div class="totcard" id="foodtot"></div>
<div class="statline" id="foodstats" style="margin:0 0 12px 2px"></div>
<div class="panel wide"><h2>Meal log</h2>
<table><thead><tr><th>Time</th><th>Type</th><th>What</th><th>Cal</th><th>Carb</th><th>Pro</th><th>Fat</th><th>Sug</th><th>Notes</th></tr></thead>
<tbody id="foodrows"></tbody></table></div>
</div>

<div class="tabpane" id="pane-meds">
<div class="grid">
<div class="panel"><h2>Daily medications</h2><div id="dailymeds"></div></div>
<div class="panel"><h2>Dose history</h2><ul id="meds" style="margin:0;padding-left:18px;font-size:14px"></ul></div>
</div>
</div>

<footer>tailnet-only · overview + food (any date) + meds · source: health.db</footer>
</div>
<script>
let charts={};
function show(t){
  ['ov','food','meds'].forEach(k=>{
    document.getElementById('pane-'+k).style.display=(k===t)?'block':'none';
    document.getElementById('tb-'+k).classList.toggle('on',k===t);
  });
  if(t==='ov'&&!charts.glc)loadOverview();
  if(t==='food')loadFood();
}
function line(id,labels,sets,extra={}){
  if(charts[id])charts[id].destroy();
  charts[id]=new Chart(document.getElementById(id),{type:'line',data:{labels,datasets:sets},
    options:{responsive:true,interaction:{mode:'index',intersect:false},
      scales:{y:{suggestedMin:extra.ymin,suggestedMax:extra.ymax}},
      plugins:{legend:{labels:{color:'#8b98a8',boxWidth:10}}},
      elements:{point:{radius:3},line:{tension:.25}}}});
}
function bar(id,labels,sets){
  if(charts[id])charts[id].destroy();
  charts[id]=new Chart(document.getElementById(id),{data:{labels,datasets:sets},
    options:{responsive:true,interaction:{mode:'index',intersect:false},scales:{y:{beginAtZero:true}},
      plugins:{legend:{labels:{color:'#8b98a8',boxWidth:10}}}}});
}
function stats(a){
  const s=a.filter(x=>x!=null).sort((p,q)=>p-q);
  if(!s.length)return null;
  const med=s.length%2?s[(s.length-1)/2]:(s[s.length/2-1]+s[s.length/2])/2;
  return {min:s[0],max:s[s.length-1],med:med};
}
function statline(id,items){
  document.getElementById(id).innerHTML=items.filter(Boolean).map(x=>`<span>${x}</span>`).join('');
}
async function loadOverview(){
  const d=await (await fetch('api/data',{cache:'no-store'})).json();
  document.getElementById('sub').textContent=
    `updated ${d.generated.replace('T',' ')} ET`+(d.regimen_day?` · on-regimen day ${d.regimen_day}`:' ');
  const r=d.readings,gl=r.filter(x=>x.glucose!=null),wt=r.filter(x=>x.weight_lbs!=null);
  const cards=
    [['Weight',wt.length?wt[wt.length-1].weight_lbs+' lbs':'—',wt.length?wt[wt.length-1].date:''],
     ['Fasting',gl.length?gl[gl.length-1].glucose:'—',gl.length?gl[gl.length-1].date:''],
     ['Cal avg (7d)',d.avg7_cal!=null?d.avg7_cal:'—','per day']];
  if(d.regimen_day)cards.push(['On regimen','day '+d.regimen_day,'weekly injections']);
  document.getElementById('cards').innerHTML=cards.map(c=>
    `<div class="card"><div class="k">${c[0]}</div><div class="v">${c[1]}</div><div class="d">${c[2]}</div></div>`).join('');
  const glL=gl.map(x=>x.date.slice(5));
  line('glc',glL,[{label:'fasting',data:gl.map(x=>x.glucose),borderColor:'#4ecdc4',backgroundColor:'#4ecdc433',fill:true},
    {label:'130 target',data:glL.map(()=>130),borderColor:'#d2992288',borderDash:[6,6],pointRadius:0,borderWidth:1}]);
  line('wt',wt.map(x=>x.date.slice(5)),[{label:'lbs',data:wt.map(x=>x.weight_lbs),borderColor:'#9b5de5',backgroundColor:'#9b5de533',fill:true}],
    {ymin:Math.min(...wt.map(x=>x.weight_lbs))-3,ymax:Math.max(...wt.map(x=>x.weight_lbs))+3});
  const bp=r.filter(x=>x.sys!=null);
  line('bp',bp.map(x=>x.date.slice(5)),[
    {label:'systolic',data:bp.map(x=>x.sys),borderColor:'#f4a261'},
    {label:'diastolic',data:bp.map(x=>x.dia),borderColor:'#e76f51'},
    {label:'120',data:bp.map(()=>120),borderColor:'#8b98a866',borderDash:[6,6],pointRadius:0,borderWidth:1},
    {label:'80',data:bp.map(()=>80),borderColor:'#8b98a866',borderDash:[6,6],pointRadius:0,borderWidth:1}],
    {ymin:60,ymax:185});
  const days=d.by_day.slice(-21);
  bar('cal',days.map(x=>x.meal_date.slice(5)),[
    {type:'bar',label:'calories',data:days.map(x=>x.cal),backgroundColor:'#4ecdc455'},
    {type:'line',label:'carbs g',data:days.map(x=>x.carbs),borderColor:'#f4a261',pointRadius:2}]);
  const gs=stats(gl.map(x=>x.glucose));
  if(gs)statline('st-glc',[
    `max <b>${Math.round(gs.max)}</b>`, `min <b>${Math.round(gs.min)}</b>`,
    `median <b>${Math.round(gs.med)}</b>`,
    `trend <b>${gl[0].glucose} → ${gl[gl.length-1].glucose} (${gl[gl.length-1].glucose-gl[0].glucose>0?'+':''}${Math.round(gl[gl.length-1].glucose-gl[0].glucose)})</b>`]);
  const ws=stats(wt.map(x=>x.weight_lbs));
  if(ws)statline('st-wt',[
    `max <b>${ws.max}</b> lbs`, `min <b>${ws.min}</b> lbs`, `median <b>${ws.med}</b> lbs`,
    `trend <b>${wt[0].weight_lbs} → ${wt[wt.length-1].weight_lbs} (${(wt[wt.length-1].weight_lbs-wt[0].weight_lbs).toFixed(1)})</b>`]);
  const sysA=bp.map(x=>x.sys),diaA=bp.map(x=>x.dia);
  const s1=stats(sysA),s2=stats(diaA);
  if(s1&&s2)statline('st-bp',[
    `SYS max <b>${s1.max}</b> · min <b>${s1.min}</b> · median <b>${Math.round(s1.med)}</b> · trend <b>${sysA[0]} → ${sysA[sysA.length-1]} (${sysA[sysA.length-1]-sysA[0]>0?'+':''}${sysA[sysA.length-1]-sysA[0]})</b>`,
    `DIA max <b>${s2.max}</b> · min <b>${s2.min}</b> · median <b>${Math.round(s2.med)}</b> · trend <b>${diaA[0]} → ${diaA[diaA.length-1]} (${diaA[diaA.length-1]-diaA[0]>0?'+':''}${diaA[diaA.length-1]-diaA[0]})</b>`]);
  const ca=days.map(x=>x.cal); const cs=stats(ca); let ctr='';
  if(ca.length>=8){
    const lt=ca.slice(-7),pt=ca.slice(-14,-7);
    const la=lt.reduce((a,b)=>a+b,0)/lt.length, pa=pt.reduce((a,b)=>a+b,0)/pt.length;
    ctr=`trend <b>7d avg ${Math.round(la)} vs prior ${Math.round(pa)} (${la-pa>0?'+':''}${Math.round(la-pa)})</b>`;
  }
  if(cs)statline('st-cal',[`max <b>${Math.round(cs.max)}</b>`, `min <b>${Math.round(cs.min)}</b>`,
    `median <b>${Math.round(cs.med)}</b>`, ctr]);
  // Optional: map drug-keywords to what they're for, shown on the Meds tab. Example:
  //   const PURPOSE={ibuprofen:'NSAID · pain, take with food'};
  const PURPOSE={};
  document.getElementById('dailymeds').innerHTML=d.daily_meds.length?
    ('<table style="font-size:14px"><thead><tr><th>Drug</th><th>Dose</th><th>Schedule</th><th>For</th></tr></thead><tbody>'
    +d.daily_meds.map(m=>{
      const key=Object.keys(PURPOSE).find(k=>m.drug&&m.drug.toLowerCase().includes(k))||'';
      const since=(m.notes&&m.notes.includes('NEW'))?'recently started':'long-standing';
      return `<tr><td><b>${m.drug}</b></td><td>${m.dose_amount||''}</td><td>${m.schedule||''}</td>
        <td>${PURPOSE[key]||''}<div style="color:#8b98a8;font-size:11px">${since}</div></td></tr>`;}).join('')
    +'</tbody></table><div style="color:#8b98a8;font-size:11px;margin-top:10px">Full notes &amp; Rx detail stay in the ledger — shown to nobody but you and your provider.</div>')
    :'<span style="color:#8b98a8">none recorded</span>';
  document.getElementById('meds').innerHTML=d.meds.map(m=>
    `<li><b>${m.drug}</b> — ${m.dose_date} ${(m.dose_time||'').slice(0,5)} ${m.notes?('· '+m.notes):''}</li>`).join('');
}
async function loadFood(){
  const q=document.getElementById('fooddate').value;
  if(!q)return;
  const d=await (await fetch('api/meals?date='+q,{cache:'no-store'})).json();
  const t=d.totals,s=d.stats||{};
  document.getElementById('foodnote').textContent=`${t.rows} item${t.rows===1?'':'s'}`;
  document.getElementById('foodstats').innerHTML=(
    s.cal7avg!=null?`7-day avg <b>${s.cal7avg} cal</b>`:'')+
    (s.cal14med!=null?` <span style="color:#4a5460">·</span> 14-day median <b>${s.cal14med} cal</b>`:'')+
    (s.prot7avg!=null?` <span style="color:#4a5460">·</span> 7-day avg protein <b>${s.prot7avg}g</b>`:'')+
    (s.carbs7avg!=null?` <span style="color:#4a5460">·</span> 7-day avg carbs <b>${s.carbs7avg}g</b>`:'')+
    (s.cal7avg!=null&&t.rows?` <span style="color:#4a5460">·</span> vs 7-day avg: <b>${t.cal-s.cal7avg>0?'+':''}${Math.round(t.cal-s.cal7avg)} cal</b>`:'');
  document.getElementById('foodtot').innerHTML=
    [['Cal',Math.round(t.cal)],['Carbs',Math.round(t.carbs)+'g'],['Protein',Math.round(t.protein)+'g'],
     ['Fat',Math.round(t.fat)+'g'],['Sugar',Math.round(t.sugar)+'g']].map(c=>
    `<div class="card"><div class="k">${c[0]}</div><div class="v">${c[1]}</div></div>`).join('');
  document.getElementById('foodrows').innerHTML=d.rows.map(m=>{
    const tm=(m.eat_time||'').slice(0,5);
    return `<tr><td>${tm}</td><td><span class="tag">${m.meal_type}</span></td><td>${m.description||''}</td>
      <td>${m.calories!=null?Math.round(m.calories):''}</td><td>${m.carbs_g!=null?Math.round(m.carbs_g):''}</td>
      <td>${m.protein_g!=null?Math.round(m.protein_g):''}</td><td>${m.fat_g!=null?Math.round(m.fat_g):''}</td>
      <td>${m.sugar_g!=null?Math.round(m.sugar_g):''}</td><td style="color:#8b98a8;font-size:12px">${m.notes||''}</td></tr>`;
  }).join('')||'<tr><td colspan="9" style="color:#8b98a8">no items logged for this date</td></tr>';
}
function shiftDay(n){
  const el=document.getElementById('fooddate');
  const v=el.value||new Date().toISOString().slice(0,10);
  const dt=new Date(v+'T12:00:00'); dt.setDate(dt.getDate()+n);
  el.value=dt.toISOString().slice(0,10);
  loadFood();
}
document.getElementById('fooddate').value=new Date().toISOString().slice(0,10);
show('ov');
loadOverview();
loadFood();
</script>
</body>
</html>
"""


class H(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path
        try:
            if path in ("/", "/index.html"):
                self._send(200, HTML.encode(), "text/html; charset=utf-8")
            elif path == "/api/data":
                self._send(200, json.dumps(api_data()).encode(), "application/json")
            elif path == "/api/meals":
                q = parse_qs(u.query).get("date", [datetime.now(ET).date().isoformat()])[0]
                self._send(200, json.dumps(api_meals(q)).encode(), "application/json")
            elif path == "/_health":
                self._send(200, b'{"ok":true}', "application/json")
            else:
                self._send(404, b'{"error":"not found"}', "application/json")
        except Exception as e:
            try:
                self._send(500, json.dumps({"error": str(e)}).encode(), "application/json")
            except Exception:
                pass


if __name__ == "__main__":
    print(f"health dashboard (tabs) on http://{HOST}:{PORT} tailnet-only", flush=True)
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
