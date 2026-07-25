# Student manual tasks — Andy Pham (Project 14, WARN mass layoffs)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the full data pipeline — a 6,560-notice multi-state WARN
panel (CA + TX + OR, 2022–2025), an automated fuzzy match of filer names to
public-firm tickers, the firm-event clustering, the market-model event study
(615 firm-events at 328 listed firms), the cross-sectional regressions, all six
tables, two figures, and a complete paper draft. **The core result is real:**
the market's average reaction to a WARN mass-layoff notice is a modest negative
CAR[0,+5] of **−1.6% (t=−2.41)**, and that punishment is almost entirely about
**materiality** — big layoffs at small firms (−3.9%), not the raw number of jobs.

**Your two jobs are the parts the AI cannot do reliably, and they are what turns
this from a suggestive result into a publishable one.** The paper currently
*cannot answer its own title question* — "does the market punish cost-cutting
layoffs differently from strategic-restructuring layoffs?" — because motive is
not in the machine-readable data. **You are going to put it there.** You will
also verify and extend the name-to-ticker match that the entire event study
rests on.

## Why your work is pivotal
1. A reviewer's first attack is: *"your WARN filers are matched to the wrong
   tickers."* The AI's matcher is high-precision but only catches filers whose
   name leads with the listed parent's name. It **misses every brand/subsidiary**
   ("Pixar"→Disney, "Optum"→UnitedHealth, "Instagram"→Meta) and can collide on
   look-alike names ("Snap Inc." vs "Snap One Holdings"). *You* are the defense.
2. The paper's headline finding is a **null on motive** — the crude
   closure-vs-layoff flag shows no CAR difference (t=−0.07). That null is only
   interesting if the *real* motive (cost-cutting vs reallocation), hand-coded
   from the announcements, *does* move CARs — or convincingly does not. **Only a
   human reading the announcements can code this.** This is the heart of the paper.

## Week-by-week

### Weeks 1–2 — Orientation + verify the name→ticker match
- Read three assigned papers: Worrell, Davidson & Sharma (1991, AMJ); Chen,
  Mehrotra, Sivakumar & Yu (2001, J. Emp. Fin.); Farber & Hallock (2009, Labour
  Econ.). One-paragraph memo on each: what reaction did they find, and to *what
  kind* of layoff?
- `data/interim/name_matches.csv` has 738 auto-matched filer names → permno/ticker.
  For the **150 largest matched events** (`data/interim/warn_events.csv`, sort by
  `headcount`), confirm the ticker is the true listed parent. Use SEC EDGAR
  full-text search, the firm's investor-relations page, and Google.
- Flag every wrong match. Record corrections in `data/interim/matches_verified.csv`
  (`company_raw, correct_permno, correct_ticker, note`). **Log every check in
  `logs/student_log.md`.**

### Weeks 2–3 — Rescue the missed brand/subsidiary layoffs
The automated pass deliberately skips filers that don't lead with the parent's
name. Go through the **unmatched high-headcount notices** (the AI will hand you
the sorted list of `warn_all.csv` rows with no confident match) and hand-map the
recognizable public-firm brands to their listed parent + ticker: Pixar/Lucasfilm
(Disney), Optum (UnitedHealth), Twitch/AWS/Whole Foods (Amazon), Instagram/WhatsApp
(Meta), Genentech (Roche), YouTube/Waymo (Alphabet), and so on. Save to
`data/interim/matches_manual.csv`. Each rescued big layoff becomes a new event.

### Weeks 3–6 — Hand-code the layoff MOTIVE (the core contribution)
This is the task the whole paper is built around. For **every matched event**
(start with the ~300 largest), read the actual layoff announcement and code motive:
- Pull the primary source: the WARN letter (many states post the PDF), the firm's
  press release / 8-K, and news coverage around the notice date.
- Code `motive ∈ {cost_cutting, reallocation, demand_collapse, merger_integration,
  automation, plant_economics, unclear}` and a binary `strategic` (1 =
  reallocation/restructuring toward a new strategy; 0 = defensive cost-cutting).
- Also record: was the layoff framed as **proactive** (management choice) or
  **reactive** (forced by losses/demand)? Was guidance raised or cut alongside it?
- Save `data/interim/motive_coded.csv` (`permno, event_date, motive, strategic,
  proactive, source_url, quote, coder_note`). **Never guess — code `unclear` and
  move on if the source is silent.**
- The AI will then re-run Table 4 and Table 5 replacing the crude `is_closure`
  proxy with your `strategic` code and report whether motive moves CARs. **This is
  the result the paper is waiting for.**

### Weeks 6–7 — Independently transcribe 20 events + confound flags
- Trust nothing. For the 20 largest events, hand-transcribe from primary sources:
  the exact affected headcount (WARN letter), total firm employees (10-K), and the
  announcement date. Compare to `warn_events.csv`; any discrepancy >10% is a
  finding.
- For each large event, was there *other* firm-specific news in the [−1,+5] window
  (earnings, an acquisition, guidance change, CEO exit)? Build
  `data/interim/confounds.csv` (`permno, event_date, headline, source`). The AI
  re-runs excluding contaminated events.

### Weeks 7–8 — Write & present
Write the paper's **Data and matching section** (you will know it best) and a
one-page memo: *did hand-coded motive change the answer?* Present the before/after
— crude proxy (null) vs your hand-coded motive.

## Deliverables you produce by hand
1. `data/interim/matches_verified.csv` — verified/repaired ticker matches.
2. `data/interim/matches_manual.csv` — rescued brand/subsidiary layoffs.
3. `data/interim/motive_coded.csv` — the hand-coded motive (the core input).
4. `data/interim/confounds.csv` — firm-specific confound flags.

## Ground rules
- **Never invent a number or a motive.** If a source is silent, write
  "unclear"/"not found."
- Log dated entries in `logs/student_log.md`: what you did, how many items,
  judgment calls.
- The judgment calls — "is closing this plant *reallocation* or *cost-cutting*?" —
  are the real skill. When ambiguous, record both the quote and your reasoning.
