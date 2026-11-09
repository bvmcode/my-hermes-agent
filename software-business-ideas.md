# Software Business Ideas

Ideas I'd actually consider building — grouped by the three spaces Barry named
(meteorology, education, utilities) plus a few categories I think deserve a
look because of how the market moved in 2025-2026. Each idea lists **what's
wrong with the current solution**, **the novel angle**, and **why it could
make money**.

*By Hermes, researched live on 2026-11-09. Verification notes at the bottom.*

---

## 1. Meteorology

### 1.1 "Was the forecast right?" — a personal forecast-verification service

**What's wrong today:** every weather app shows you a forecast; *none* shows
you how often that provider was right *for your specific location*. Forecast
skill is local (mountains, coastlines, urban heat islands), and your app's
forecast for your block is a gridpoint guess that's never scored. Forecast
verification is an active science — but the consumer experience is still
"trust the icon."

**The novel build:** a service that, for the coordinates of your
house/commute/trailhead, records every forecast issued by each provider
(NWS, Open-Meteo, Tomorrow.io, Weather.com, Foreca...), waits the real day
out, then scores each against the official station record. Publishes a
"trust score" per provider per variable per lead-time (e.g. "Open-Meteo's
3-day precipitation probability for *your* station has been right 71% of
the time; NWS is at 79%").

- **Why now:** NWS's api.weather.gov is free, keyless, JSON-LD, and
  machine-readable (verified live while researching this — the
  `/points/{lat,lon}` → `/gridpoints/{office}/{x},{y}/forecast` flow is
  stable and officially documented as "open data, free to use for any
  purpose"). The observational record (NWS/COOP/MADIS, Ecowitt,
  PWSWeather, Weather Underground) is already public. The pieces never
  existed at consumer-friendliness until recently.
- **Adjacent moves:** ForecastScores.com already does this
  "was the forecast right?" framing for 1,200 US stations;
  ActuallyWeather.com sells this as a de-biasing tool across North
  America and Europe. **The gap:** neither one is personal — neither
  lets a consumer say "here is my house, my roof, my commute path, score
  the forecasts *there*, and tell me which one to open on my phone."
- **Money:** subscription at $3-6/mo per household ("your rain forecast,
  scored, guaranteed-to-be-the-best-available"). B2B angle: outdoor
  industries (landscapers, contractors, event venues, golf courses,
  marinas) pay real money to know *which* model to trust for the next
  48 hours.
- **Barry-specific hook:** this doubles as a weather-station companion
  product idea. Home Assistant already has a thriving ecosystem of
  personal weather station integrations (Ecowitt, Davis, WeatherFlow —
  verified: at least three HACS projects built exactly this in 2025),
  and *every one of them has no scoring layer*.

### 1.2 PWS-to-NOAA citizen-observation "score + submit" platform

**What's wrong today:** hobbyists run excellent backyard Ecowitt/Davis
stations; many upload to Weather Underground or CWOP; almost none get
feedback about whether *their* sensors drift, whether their humidity is
biased after a season outside, or whether their rain gauge is undercounting
in heavy wind.

**The novel build:** a tool that, for each uploading personal station,
automatically calibrates against the nearest official ASOS/AWOS/COOP
record and reports drift ("your hygrometer has biased +7% since June"),
then optionally feeds a corrected stream back to the public networks. It's
a paid pro tier for serious hobbyists and a citizen-science pipeline
NOAA's own volunteer networks (CWOP/MADIS) would happily link.

- **Money:** freemium with drift scoring as the paid feature; bulk
  dashboard for hardware vendors (Ecowitt, WeatherFlow) to ship with
  their stations as a differentiator.

### 1.3 Weather-decision API for "should I do this" questions

**What's wrong today:** current apps answer "what will the weather be?"
Businesses need answers to "*should I send the crew?*", "*should we book
the tent?*", "*cancel or reschedule?*" — a decision, not a reading.

**The novel build:** a small API/chat service where developers query with
natural-language thresholds ("wind under 12 mph after 2pm, rain risk
under 30%") and either `GO`/`NO-GO`/`CHECK` comes back with reasoning, plus
an auditable forecast trail. It's Decision-As-A-Service; every answer gets
logged, retrospectively scored, and improved.

- **Why it's novel:** current weather-API businesses sell *data*; nobody
  sells *decisions* with a scoring history attached.

---

## 2. Education

### 2.1 "Last-mile" lesson delivery for teachers

**What's wrong today:** teachers are drowning — Techpoint reported teachers
spending up to 20 hours preparing one hour of class and 250 papers to grade
in a week; the UK government funded a £1M AI marking program because
teacher feedback workload was halving classroom time; the *stated* gap
(from the Meet Every Learner Needs analysis) is **last-mile delivery**: AI
gives you text, and the teacher then has to copy-paste it into a slide
deck, a worksheet, and an exit ticket before it's usable. Tools like
paddy (€1M pre-seed, 12k users in 6 months) and Fast Feedback are doing
adjacent work.

**The novel build:** "one prompt → full classroom kit."
Teacher says *"Photosynthesis, 8th grade, 45 minutes, mix of learners."*
The product emits the **complete deliverable bundle** — warm-up, slide
deck (real .pptx), differentiated practice, exit ticket, answer key,
 reteach sheet — formatted and ready to project, no copy-paste assembly.
Differentiation is real (three reading levels, ELL support, extension for
advanced students) and teacher-editable inline.

- **Why it's novel:** the 2022 AGA-style gap isn't generation, it's
  *assembly + formatting*. Nobody ships the classroom-ready bundle.
- **Money:** per-teacher SaaS at $10-15/mo (teachers already buy
  classroom tools out of pocket); enterprise via districts; a
  state-standards-aligned variant is an instant differentiator.
- **Barry-specific hook:** the deliverable-emission mechanic is exactly
  what an agent does well — build it *on an agent framework* and it
  becomes a template, not a one-off product.

### 2.2 Gradebook-aware reteach generator

**What's wrong today:** Fast Feedback (UK, 2025) is already generating
reteach tasks from marked work — but nobody is doing it *connected to the
gradebook*, so the reteach is generic instead of " reteach this kid's
exact misconception" and "regroup tomorrow's lesson around the mistake
60% of the class made."

**The novel build:** a tool watching the gradebook (Google Classroom,
Canvas, PowerSchool integrations) that turns class-wide error patterns
into next-day reteach slides *before* the teacher walks in. It's the
difference between "AI graded it" and "AI made my next lesson better."

### 2.3 Special-education compliance assistant

**What's wrong today:** IEP paperwork is a national burnout driver; most
special-ed teachers burn 5-10 hours a writing cycle on compliance prose
that's identical in structure and unique per kid.

**The novel build:** an IEP/504 drafting assistant that produces the
compliance scaffolding (goals, accommodations, progress-monitoring text)
from teacher speech-dictation, with every claim traced back to the case
notes and a hard boundary — it drafts, humans approve, nothing auto-sends.
HIPAA/FERPA-first architecture from the start, not bolted on.

- **Money:** per-seat district contracts sell slow but stick.

---

## 3. Utilities

### 3.1 Personal-agents-as-a-product for a *vertical* (health, home, eldercare)

**What's wrong today:** ChatGPT/Claude/Codex are generic sandboxes. Barry
runs a Hermes instance with his health ledger, family messaging, and job
pipeline — this is the *product*, but the market has no packaged version
of it.

**The novel build:** a white-label "personal daily-log agent" box —
appliance + subscription — aimed at a *vertical*. Pick one, e.g.:

| Vertical | What it does | Why they'd pay |
|---|---|---|
| **GLP-1 / diabetes tracking** | agent logs meals/glucose/symptoms by voice dictation, mirrors CSVs to family, produces a doctor-appointment summary with the medication timeline built in (dose #1 → weekly → trending) | the 2025-2026 GLP-1 tracking market exploded (validated: GLPzy, PenPal, CalZen, GLP-1 Journal all shipped 2025-2026) but *none of them are conversational agents that log by dictation* — they're all forms-and-buttons apps. Voice-first logging is the open lane. |
| **Eldercare check-in** | voice agent calls mom at 9am, asks 3 questions, flags deviations to a human | adult-children pay for monitoring they can't do from far away |
| **Field-crew daily log** | construction/restaurants dictating the day's events into a searchable ledger | paperwork is why small contractors lose legal disputes |

- **Why it's novel:** every existing player is an *app with forms*; the
  dictation-first, memory-persistent, self-improving agent version doesn't
  exist commercially. The stack you need is exactly what Barry's box runs.
- **Money:** $199-399 one-time appliance + $20-40/mo subscription;
  margin comes from the same agent core being reskinned per vertical.

### 3.2 The "life-in-CSV" export bus

**What's wrong today:** your health data is in Apple Health; your food is
in an app; your meds are in another; your kid's is in a fridge magnet.
**Zero of them talk to each other, and every one of them exports in a
format designed for lawyers.**

**The novel build:** a privacy-first, locally-hosted service that
-normalizes- the export formats of 30 consumer health/lifestyle apps into
one clean, queryable, *you-owned* CSV/API schema — plus a "morning report"
and an "appointment summary" endpoint. It's plumbing, and plumbing is what
utility companies are made of. The GLP-1/health trackers above would plug
into it rather than compete with it.

- **Money:** $5-10/mo, cheap because it's pure aggregation; the real
  business is becoming the data layer other personal tools plug into.

### 3.3 "Agent-in-a-box" for small professional practices

**What's wrong today:** solo law/accounting/therapy/contractor offices
have no IT staff; generic Copilot/ChatGPT can't touch their files, learn
their client history, or remember anything.

**The novel build:** a hermes-style box pre-seeded with the practice's
document corpus and workflows — intake, letter-writing, appointment
reminders, client follow-ups — with an audit trail. Sell through
accountants to their business clients; one install per practice.

- **Money:** $2-4k per box + $99/mo; the appliance form factor is the moat
  because the trust story ("your data stays in your office") is what these
  buyers need.

---

## 4. Categories I'd add (beyond the three Barry named)

### 4.1 Family-logistics agents
The "who has what tonight" problem — schedules, carpools, permission
slips, food allergies, appointments — for a household. One agent, per
family, synced on everyone's device. Existing calendar/family apps (Cozi,
FamCal) are dumb storage. Nobody ships the *decision* version — the agent
that sees the conflict before you do.

### 4.2 Maintenance-memory SaaS
"Which filter, when did we change it, who's coming Tuesday?" — home
maintenance is guesswork. An agent that logs home service visits
(dictated), tracks model numbers and warranties from photos, and reminds
proactively. Small market per user, almost viral per neighborhood.

### 4.3 Religious/community organization tools
Churches, synagogues, mosques run on volunteers and spreadsheets. A
church-office agent: sermon notes → bulletins, schedules → reminders, member
care lists → outreach logs. A real market, barely digitized, and the buyers
trust values-aligned vendors.

### 4.4 Small-press / creator fulfillment
Writers, podcasters, Etsy-scale makers: an agent that handles the
administrative side — invoices, licenses, fan-mail triage, podcast-show-notes
— so the creator creates. (Adjacent: YouTube show-notes/summary agent on a
cron, which is exactly what the 7pm AI-news pipeline already proves out
technically.)

---

## Ranking for a solo builder

| # | Idea | Why build first |
|---|---|---|
| 1 | **2.1 — Last-mile lesson delivery** | smallest sellable artifact, urgent demand, clear "bundle assembly" gap; MVP in weeks |
| 2 | **1.1 — Personal forecast verification** | free data, zero marginal cost to run, strong daily-utility habit loop |
| 3 | **3.1 — Vertical personal-agent (GLP-1)** | Barry's own run = customer #0 + the demo; voice dictation is the unclaimed lane |
| 4 | **2.3 — Sped compliance assistant** | high pain, sticky; slower sell (district contracts) |
| 5 | **1.3 — Weather-decision API** | B2B long-tail; good after #1 earns trust |
| 6 | **3.4 — Practice-in-a-box** | highest ticket, longest validation cycle |

---

## Verification notes

- **api.weather.gov** is keyless, JSON-LD, explicitly "open data, free to
  use for any purpose" — I pulled a live point-forecast for South Jersey
  while writing this and the full docs page checks out.
- **ForecastScores.com** ("was the forecast right?", 1,200 US stations) and
  **ActuallyWeather.com** (model-vs-model across North America/Europe)
  exist and are adjacent; my personal-verification idea (#1.1) takes the
  *consumer-at-a-coordinate* framing they don't.
- **Home-Assistant PWS integrations** (Weather Station Core, Personal
  Weather Station, wundergroundpws — verified live on GitHub) confirm an
  installed base of weather-station hobbyists without any verification layer.
- **Teacher-workload claims** (20h prep per 1h class; 250 papers/week; UK
  £1M marking program; paddy €1M/12k users; Fast Feedback £20k SHINE
  award) — all verified from Techpoint, gov.uk, Tech.eu, and SHINE Trust
  sources dated 2025.
- **GLP-1 tracking tools** — verified live (GLPzy, PenPal, CalZen, GLP-1
  Journal, MyFitnessPal's GLP-1 mode, all 2025-2026 launches). None are
  dictation-first agents; every one is a forms app. This is the gap #3.1
  targets.
