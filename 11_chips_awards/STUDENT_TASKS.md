# Student manual tasks — Alexander Li Tang (Project 11, CHIPS awards)

**The AI has built:** the full pipeline — a first-pass hand-collected award list, the
WRDS/CRSP pull, the per-event market-model event study (shared `lib/event_study.py`), the
cross-sectional "scaling with size" regressions, all tables, both figures, and a complete
paper draft. **The core result is real and honest:** CHIPS award announcements did *not*
move awardee stocks on average (mean CAR[-1,+1] = +2.6%, t = 0.99; median +0.5%; 8/15
positive), and the apparent "reaction scales with award size" is an artifact of a single
distressed micro-cap (Wolfspeed).

**Your job is the part the AI cannot do reliably, and it is genuinely pivotal:** the entire
event study stands or falls on *the exact announcement date and the correct ticker for each
award*. A one-day error in an event date, or a wrong parent ticker, silently corrupts a CAR.
You are the defense against a reviewer's first attack: "your event dates and identifiers are
wrong."

## Why your manual work matters
An event study is only as good as its event dates. The AI populated
`data/raw/chips_awards_handcollected.csv` from the Manufacturing Dive CHIPS tracker plus a
handful of primary press releases, but it did **not** open every Commerce/NIST release to
confirm the exact day, and it used a "latest CRSP name" rule to map tickers. Both are
*good enough for a first pass but known to be wrong in specific, correctable ways.* Fixing
them is your contribution — and may change the result.

## Week-by-week (8 weeks)

### Weeks 1–2 — Verify every announcement date against the PRIMARY press release
Read the three assigned papers (MacKinlay 1997; Brown & Warner 1985; Corrado 1989), then:
for all 17 awards in `data/raw/chips_awards_handcollected.csv`, open the actual U.S.\
Department of Commerce (`commerce.gov/news/press-releases`) **or** NIST CHIPS
(`nist.gov/chips`) release announcing the *Preliminary Memorandum of Terms* (the FIRST
announcement, not the later finalized "funding agreement"). Record the exact publication
date (YYYY-MM-DD), the proposed direct-funding amount, and the *time of day* if given (a
release after the market close means day 0 is the **next** trading day — this matters for
the CAR). Save to `data/interim/dates_verified.csv` (ticker, announce_date, award_usd_m,
press_release_url, after_close_flag, note). The AI re-runs `10_event_study.py` with your
dates.

### Weeks 3–4 — Resolve each awarded ENTITY to the correct listed parent, and build the confound timeline
- Confirm each ticker corresponds to the awarded entity: SolAero → **Rocket Lab (RKLB)**;
  TSMC Arizona → the **TSM** ADR (a partial claim on the Taiwan parent — flag it); Absolics →
  SKC (Korea, *not* U.S.-listed); Polar Semiconductor, Bosch, Hemlock, Edwards Vacuum →
  privately held (exclude). Verify each on SEC EDGAR and the company IR page. Record in
  `data/interim/tickers_verified.csv`.
- Build the news/confound timeline: for each event's [-1,+5] window, check for *other*
  material news (earnings, guidance, M&A, capital raises, downgrades). **Amkor is a known
  confound** — its Q2 earnings (2024-07-29) fell inside its window and drove the −17%, not
  the award. Find the others. Save `data/interim/news_flags.csv` (ticker, date, headline,
  source, confound_flag). The AI re-runs excluding confounded events.

### Weeks 5–6 — Independently transcribe the 6 biggest awards, and stage the extensions
- Trust nothing. For Intel, TSMC, Micron, GlobalFoundries, Texas Instruments, and Wolfspeed,
  open the company's own 8-K / press release reacting to the award and confirm (a) the dollar
  amount, (b) the *required private co-investment* (the cost-share — this is the key reason a
  grant may not be a windfall), and (c) grant-only vs grant+loan. Any discrepancy vs. the
  raw file >5% is a finding — document it.
- Stage the two held-out **Jan-2025** awards (Analog Devices ADI, MACOM MTSI) — record exact
  dates now so they drop into the sample when the next CRSP annual file lands.
- Hand-collect the *second* event for each firm: the finalized "CHIPS Incentives Award"
  (funding agreement, late 2024) — `data/interim/finalization_dates.csv`. A second,
  less-anticipated event is a natural extension the AI can run.

### Weeks 7–8 — Write & present
Write the paper's **Data section** (you will know it best) and a one-page memo on what your
verification changed: did any event date move? did dropping confounds change the null? do the
co-investment numbers explain why the reactions were muted? Present the before/after.

## Deliverables you produce by hand
1. `data/interim/dates_verified.csv` — primary-source-verified announcement dates + amounts.
2. `data/interim/tickers_verified.csv` — entity → listed-parent resolution.
3. `data/interim/news_flags.csv` — window-level confound timeline.
4. `data/interim/finalization_dates.csv` — the second (funding-agreement) event dates.

## Ground rules
- **Never invent a number or a date.** If you cannot find it, write "not found."
- The FIRST announcement (Preliminary Memorandum of Terms) is the event — not the later
  finalized funding agreement, and not the company's own earlier fab-siting press release.
- Log dated entries in `logs/student_log.md`: what you did, how many items, judgment calls.
  This becomes part of the paper's replication trail.
- Ask when an entity's structure is ambiguous (subsidiary vs. parent) — those judgment calls
  are the real skill, and they are what make this paper trustworthy.
