# The Weather Ideas, Elaborated

This file expands the three meteorology ideas from `software-business-ideas.md`
into buildable plans: what the product actually does, why the incumbents have
left it open, how it makes money, what an MVP costs to run, and what data
sources power it. Every external claim is footnoted in **Verification** at the
bottom, and the things marked "verified live" were actually tested during this
session.

---

## Idea 1 — Personal Forecast Verification ("was MY forecast right?")

### The product in one sentence

A service that, for the exact coordinates you care about (home, commute,
trailhead, kid's soccer field), silently records every forecast each provider
issues, then — the next day — checks each one against what actually happened
at the closest weather station, and publishes a **per-provider, per-variable,
per-lead-time trust score for *your* location**.

### What the user actually sees

```
  Your location: 40.1217, -74.7533 (Roebling, NJ — gridpoint PHI/63,88)

  ── PAST 90 DAYS, VERIFIED ───────────────────────────────────────────
                        NWS   Open-Meteo  Weather.com   AccuWeather
  High temp ±3°F      100%    100%    100%       100%
  Low temp ±3°F       100%    100%    100%       100%
  Rain (yes/no)        50%     50%     66%        50%
  ── RECOMMENDATION ───────────────────────────────────────────────
  Use The Weather Channel app for rain calls at your house.
  NWS is fine for temperature. AccuWeather's adds are not worth it here.
```

(Monthly counts for a single location are ~90 forecasts per provider — the
real product pads this by co-scoring the 5-10 nearest stations within 25 km
so every cell has meaningful n, while flagging which station each row came
from. This is the same trick ForecastAdvisor uses — "nearest location within
50 km" — but with *your* coordinates at the center instead of a city center.)

### Why this is a real gap

The incumbent accuracy player is **ForecastAdvisor** (owned by
ForecastWatch), and its own methodology page is the strongest argument for
the gap: it scores **2,200+ city-center locations**, uses a rolling
12-month window, and answers "which forecaster is most accurate **for that
city**." It does not score for a private coordinate, does not score
*within-day-hour* forecasts (their analysis is 1-3 day lead times on high
and low temp + precip icon/text), and does not ingest a user's own
backyard station. The adjacent startups — **ForecastScores.com** ("was the
forecast right?", 1,200 US stations, pick a station/forecast/day) and
**ActuallyWeather.com** (model-vs-model across North America and Europe,
de-bias your model run) — both sell the framing but neither is
*personalized to a coordinate you own*. **Nobody lets a consumer say "score
the forecasts at my house, against my own rooftop sensor, and tell me
which app to open on my phone."**

### The data feeds (all free or freemium at MVP scale)

| What | Source | Cost | Note |
|---|---|---|---|
| Point location → gridpoint resolution | `api.weather.gov/points/{lat,lon}` | free, no key | JSON-LD, officially "open data, free to use for any purpose" |
| 7-day + hourly + raw gridpoint forecasts | `api.weather.gov/gridpoints/{office}/{x},{y}/ forecast[/hourly]` | free | 2.5km×2.5km resolution, NWS Weather Forecast Office products |
| Second/third forecast providers | Open-Meteo (free 10k calls/day non-commercial), OpenWeatherMap (free tier), WeatherAPI.com (100k/mo free), Visual Crossing (30k records/day free) | free to low $ | enough for 3-provider MVP without paying anything |
| Observations (the truth layer) | NWS ASOS/AWOS via api.weather.gov `{station}/observations`; nearest 5 from the `/points` response's `observationStations` field | free | quality-controlled station data; ForecastWatch's own methodology says these same stations drive their accuracy math |
| User's backyard sensor (the differentiator) | Ecowitt/WeatherFlow/Davis/Tempest HTTP feeds, or Home-Assistant webhooks | $0 (user's hardware) | 3 HACS integrations already do PWS→Home-Assistant ingestion (verified) |
| Historical archive for backfill | Visual Crossing (50+ years, sub-hourly, cheap at 10M records/$35mo) | ~$35/mo | lets the product have a "here's last year's score" value on day one |

### The unit economics

- MVP runs entirely on free tiers + a $5/mo VPS. The verification loop is
  a few hundred API calls per user per month (one pull per provider per
  location per cycle, plus one observation scrape per evening).
- **Charged product: $4/mo per household** ("score my house"), or free
  30-day report as the lead magnet, converting on "here's your neighborhood
  forecast report card."
- **The B2B upgrade is the real money:** outdoor-trade businesses —
  landscapers, roofers, concrete pourers, marina operators, event venues,
  golf courses — pay real invoices for "which model to trust for the next
  48 hours at MY address." Their addresses move around weekly; the
  per-coordinate scoring is exactly what they want and can't buy today.
  $99-299/mo per business account is the opening price, and *one* roofing
  company = ~50 consumer subscribers in revenue.
- Adjacent validation: **Sensible Weather sold 1M+ weather guarantees
  across 8,000 locations** in ~4 years — a parallel market for "weather
  certainty as a product," and their pricing page documents why
  businesses pay: it converts bookings and reduces cancellations. The
  verification product sits next to that industry, feeding it truth
  instead of payouts — potentially as **their data-quality backend**.

### The moat question (and the honest answer)

The moat isn't the scoring math — it's the **archive**. A personal
verification log *compounds*: every day your subscribers stay, the product
is the only place that stores forecast-for-this-coordinate-and-what-happened
for their exact house. Incumbent city-center scores from ForecastWatch can't
be recreated retroactively at a private coordinate, because **forecasts issued
that morning for that gridpoint don't exist anywhere** unless they were
captured when issued. Data captured can't be back-filled. That's the moat.

### MVP scope (2-4 weekends of work)

1. Cron: per registered location, call `/points` → `/forecast` +
   `/forecast/hourly` + two competitor feeds, store the raw JSON. (The
   storage is forecast-time-stamped; that's what makes it reproducible.)
2. Nightly cron: pull the nearest-N-station observations, run the scorecards.
3. A web page: paste a coordinate (or pick "use my phone's GPS"), see the
   scorecard after 2 weeks of data accrues. Before 2 weeks: "collecting
   baseline."
4. Free tier: 1 location. Paid: 3 locations + backyard-station ingestion +
   push notification on the daily scorecard ("your NWS forecast missed by
   8°F yesterday").

### Risks

- NWS could rate-shape or change the API (they've been stable & documented
  for years; the official GitHub issues page is the early-warning channel)
- The two adjacent startups (ForecastScores, ActuallyWeather) could pivot
  personal — mitigate by being *the* personal+PWS hybrid first and the
  only one with a Home-Assistant integration
- Weather providers' unofficial scrapes break; stick to official APIs for
  the MVP, add scraping later only as a bonus

---

## Idea 2 — PWS Drift & Calibration Platform ("your station has silently biased +7%")

### The product in one sentence

For owners of backyard weather stations (Ecowitt, Tempest/WeatherFlow,
Davis, Ambient), a service that continuously compares their station's raw
readings against the nearest official reference stations, detects and
reports **drift, bias, and fault by sensor**, and optionally publishes a
calibration-corrected feed back to the public networks (CWOP, PWSWeather,
Weather Underground, Windy).

### Who this is for, and how big the group actually is

- The **Personal Weather Station hobbyist population is large and
  active** — Weather Underground alone hosts tens of thousands of
  uploading stations (its API keys are only issued to registered and
  active PWS users), CWOP/MADIS exists as an official NOAA citizen
  network, and PWSWeather, WOW-BE, Windy, and OpenWeatherMap each accept
  uploads.
- The **HACS/Home-Assistant ecosystem** (verified live: Weather Station
  Core, Personal Weather Station, wundergroundpws integrations, plus one
  purpose-built multi-network uploader) shows an installed base of users
  already going out of their way to move data — they're the early adopter
  profile.
- Academic validation that the *problem* is real: a 2025 peer-reviewed
  evaluation of the very popular Tempest station found **positive bias vs.
  reference data in temperature, humidity, wind (high-biased due to sonic
  anemometer response), with the authors attributing part of it to the
  manufacturer's own auto-calibration algorithm causing the positive
  biases.** AviationWX's excellent standards guide spells out the
  field-drift taxonomy: "wind shadow, radiation heating, wetting losses,
  drift, cabling faults … most 'sensor error' is exposure error" —
  which is another way of saying every backyard station has *its own*
  bias profile that only a comparison service can discover.
- Community evidence of confusion & mis-calibration: the PalmTalk thread
  "Weather Station Experiments and Brand Comparisons" and Ecowitt-WS90
  forum threads are people *manually* doing what this product would
  automate (haptic rain gauges overcounting in wind, solar-radiation
  under-reads at high latitude, rain-gauge "worthless" reports).

### The product's actual features (ranked by user pain)

**Free tier:**
- Nearest-3-official-station comparison, refreshed hourly
- A "station health" page: current bias per sensor vs. the reference set,
  a 30-day trend line, a simple "OK / drifting / suspect" flag

**Paid ($5/mo, or bundled at $79/yr for serious hobbyists):**
- **Drift detection with dates** — "your hygrometer has biased +7% since
  June 3rd" (the date matters because it usually correlates with a storm,
  a move, or a firmware update — AviationWX's guide says exactly this:
  log firmware updates, hardware swaps, and moves, because they change
  the baselines)
- **Automatic per-sensor calibration curves** (linear bias/offset/scale
  per variable, learned vs. the reference set) — applied as an optional
  corrected-output stream
- **Network upload orchestration** — one config, pushed to
  CWOP/PWSWeather/WUnderground/Windy as the *corrected* stream, with a
  per-network status sensor (the open-source HACS uploader proves the
  demand and the integration shape; the paid part is the correction layer
  nobody has)
- **Alerting:** "your station went offline 14 hours ago," "your temperature
  looks stuck," "your rain tip count stopped after the last storm — check
  the funnel"

**The B2B twist that makes it a real company:** hardware vendors (Ecowitt,
WeatherFlow, Tempest, Ambient) ship weather stations pre-connected to
consumer networks. **Shipping each unit with a "Calibrate Me" subscription
pre-linked is a margin-maker and a differentiator** — the vendor's support
costs drop (fewer "is my rain gauge broken?" tickets) and the buyer gets a
station that self-heals. Sensible Weather's playbook (partnership-embedded
product at 8,000+ locations, then expanding to 1,400+ hotels through one
booking-engine integration) is exactly the route: one platform integration →
thousands of endpoints.

### Data feeds & build

- Ingest: the open HTTP endpoints the stations already POST to
  (`updateweatherstation.php`-style), plus the vendor cloud APIs for
  platforms that don't push raw (Ecowitt cloud, Tempest's
  bettermonitored/WeatherFlow API). All public/stable.
- Reference: nearest official stations (ASOS/AWOS, MESONET, COOP) via
  api.weather.gov — the free NWS route; plus the user's *own* neighboring
  PWS stations as a consensus check (3-neighbor median is the classic
  correction method).
- MVP storage: a timeseries in Postgres/TimescaleDB on a single small VPS —
  6 variables × hourly per station × 5,000 stations ≈ a few GB/year. Trivial.
- Sales channel for the paid tier: **Home Assistant + PWS forums +
  r/Weathertools + the vendors' own user groups.** The community is
  tight and self-referencing; a genuinely useful free tier will do the
  marketing.

### Risks

- **Users' siting problems are irreducible** — a station next to an AC
  exhaust will *never* match the airport, and the product has to be careful
  to say "this is siting error, not sensor drift" (the AviationWX guide's
  framing is exactly right: "most sensor error is exposure error"). Getting
  this wrong once → angry forum posts. Mitigate with a siting-aware
  reference selection (prefer stations with similar exposure class, and
  show confidence bars).
- Weather Underground/CWOP could change their ingest — mitigate by being
  multi-network from day 1 (the HACS uploader's exact strategy).

---

## Idea 3 — The Decision API ("GO / NO-GO for the thing you're about to do")

### The product in one sentence

An API that answers **"should we do X?"** instead of "what's the weather?" —
`/v1/decide` takes a location, an activity, and thresholds ("crane lift +
wind < 15 mph + no precipitation," "exterior paint + dry 4h window," "pool
party + no rain 10am-6pm"), returns a verdict + score + the best hours + the
risks, and **logs the decision forever so you can score the scorer.**

### Who's already trying to be this — and the gap

I have to flag this one harder than the other two: **a startup exists that
markets almost exactly this** — **weatherAI.io** ("the weather decision API
for apps and AI agents"; one call returns a go/no-go, a score out of 100,
the best hours and the risks; industry packs for construction, events,
drone flying, crops; 1,000 free calls/month; explicit agent/LLM framing;
they publish their track record nightly for fixed cities). Visual Crossing just
launched an LLX high-concurrency endpoint and markets Timeline as an
"events" API. Tomorrow.io's flagship framing has always been
"weather-aware operations" (its monitoring API watches locations and fires
alerts when rules are met). Xweather (Vaisala) serves the safety-critical
version.

So the honest, current state of this idea: **the "decision API" framing has
been claimed. The room isn't empty.** Three viable differentiated angles
remain, each of which is a real business in its own right:

**Angle A — the trust-scoring decision engine.** weatherAI publishes a
track record *per city, nightly, for a fixed set.* There is no decision
API that scores itself **at your coordinate, for your repeated real
decisions, over your own operating history** ("last 60 crane lifts:
our GO verdicts were weather-safe 58/60; the 2 misses both involved
gusts above threshold 45 minutes earlier than forecast"). Combine Idea 1's
personal-verification engine with a decision API and the pitch becomes
"*decisions, with the receipts*." For a B2B buyer paying for weather
certainty, that's a materially different sales conversation.

**Angle B — vertical decision products, not APIs.** The API framing is
commoditized; a **single-vertical product** is not. Two candidates:
  - **Concrete pour / roofing / siding job-verifier** for contractors:
    photo of the job + date + crew size + the pour-spec → an insurance-grade
    weather report attached to the invoice ("pour on 11/9, verified rain-free
    06:00-14:00 per PHI/63,88"). **Sensible Weather's business is adjacent
    proof that weather-certainty is billable** — they've now sold 1M+
    guarantees across 8,000+ locations, launched a *High Wind Guarantee*
    product line (their 2025 launch), and expanded to 1,400+ hotels via one
    SynXis integration. The B2B message is identical ("remove weather
    friction, increase conversion, reduce chargebacks") — but their
    product *protects the customer after the fact*; **a pre-pour report +
    post-pour attestation protects the contractor's invoice *before* the
    dispute.** No existing product does the attestation side; that's the
    white space.
  - **Event/venue "weather certainty" page** — an embed for venues and
    campgrounds that sells certainty at booking time ("if it rains past
    1pm on your booked day, you get X% back — verified by our station").
    This is a **white-label wrapper around Sensible weather's model** in a
    segment they don't serve (small non-hospitality venues).

**Angle C — the audit-grade decision log for regulated work.** Aviation,
crane jobs, concrete pours, film production — industries where a *weather
decision* has legal and insurance consequences. The product is a
defensible, timestamped, audit-ready "we were told X at 0600 and we
decided Y" record. The decision log itself — immutable, third-party,
permissible in an insurance or OSHA conversation — is the product.
Nobody currently markets this.

### Data feeds & build for Angle C (the strongest version)

- Forecast + observation: NWS (free), Met.no, Open-Meteo (free
  non-commercial) — the decision engine is an LLM-free rules layer on
  top, deliberately explainable ("wind 18-22 mph 1400-1500 > threshold 15;
  reason: crew on height")
- The audit trail: append-only ledger keyed by decision, with
  forecast-time-stamped inputs stored immutably (same primitive as Idea 1's
  moat: **forecast capture at issue time, verifiable later, impossible to
  back-fill**)
- Sales: one crew-per-week pilot with 3 local contractors; $150/mo per
  crew; the "attestation attached to invoice" feature is the close.

### What I'd do in weather, in order

1. **Idea 1 (personal verification) first.** It's the smallest surface, the
   only one with no direct competitor at the private-coordinate tier, the
   cheapest to run (free NWS + competitor feeds + one VPS), and it *creates
   the moat archive* that ideas 2 and 3 want to exist.
2. **Idea 2 second**, as the paid community of the same engine — the Home
   Assistant/PWS crowd becomes the product's first paying user base and its
   loudest marketing channel
3. **Idea 3 last and narrow** (one vertical: pour-attestation) — only after
   1 and 2 have given you real observed-forecast archives at user
   coordinates. The attestation pitch is much stronger when you can
   *demonstrate* you were capturing forecasts at their coordinates
   yesterday, not last year.

---

## Shared insight across all three

**The moat in weather is timestamped observation of issued forecasts.**
Every idea above is really the same primitive — *capture forecasts at issue
time, bind them to a coordinate and a user, then score them against
verified truth* — pointed at different buyers (household, station owner,
business). It is precisely the thing no incumbent product does at a private
coordinate today, precisely the thing that cannot be retroactively
replicated by a competitor after the fact, and precisely the reason
ForecastWatch's 2,200-city operation, ForecastScores' 1,200 stations, and
ActuallyWeather's model-comparison product haven't absorbed it: their
collections are public-infrastructure-shaped, and yours would be
*privately-owned-at-the-coordinate* shaped.

That's the idea. The rest is execution, and the execution surface is
small: free data, honest scoring, one cron, one page, and patience.

---

## Verification

- NWS API — keyless, JSON-LD, documented as "open data, free to use for
  any purpose"; live-tested the `/points` → `/gridpoints/PHI/63,88` chain
  during this session and pulled real gridpoint temperatures
- ForecastAdvisor's methodology, city-center-only framing, 2,200 locations,
  nearest-within-50km behavior — from their own `docs/accuracy` and
  `docs/about` pages
- ForecastScores.com — live site, "was the forecast right?", 1,200 US stations
- ActuallyWeather.com — live Substack + product site (de-bias model runs)
- weatherAI.io — live decision-API product site (go/no-go, industry packs,
  agent framing, published track record)
- Visual Crossing LLX launch, pricing tiers — from their launch page
- Tempest positive-bias findings and attribution to auto-calibration —
  peer-reviewed, Journal of Atmospheric and Oceanic Technology (AMS),
  doi 10.1175/jtech-d-24-0133.1
- AviationWX sensor-standards guide (drift taxonomy, exposure-error
  framing) — guides.aviationwx.org
- Sensible Weather's 1M+ guarantees / 8,000 locations / 1,400 hotels via
  SynXis partnership, High Wind Guarantee launch — their own press pages
  and Business Wire, Dec 2025
- Open-Meteo (10k/day free non-commercial), Visual Crossing (30k/day free),
  WeatherAPI.com (100k/mo free), Foreca (from €99/mo, 1M calls) — pricing
  pages pulled live
- The three HACS Home-Assistant PWS integrations and the multi-network
  uploader — verified from their GitHub READMEs
- Poncho (weather guarantees at point of sale, France) — live product site
- CWOP/MADIS + Weather Underground's PWS-key policy ("only issued to
  registered and active Weather Underground personal weather station
  users") — from the Wundergroundpws integration's setup docs
