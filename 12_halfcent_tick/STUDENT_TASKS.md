# Student manual tasks — Kushal Borra (Project 12, Half-Cent Tick)

**The AI has built:** the full data pipeline (WRDS CRSP daily pull, sample construction,
DiD estimation, event-study, placebo, figures), all tables, and a complete 18-page paper
draft. The **core result is real and honest**: using the best *daily* proxy we could obtain,
we cannot detect the half-cent tick's effect, and we show *why* — the daily closing quote is
censored to the penny grid for exactly the stocks the reform targets, and the naive control
group fails parallel-trends.

**Your job is the part the AI cannot do reliably and that turns this honest null into a
credible test:** (1) hand-verify the regulatory facts and per-stock eligibility, and
(2) drive the acquisition of the intraday data the question actually needs. These are
genuine research contributions — a referee's first two attacks on this paper are "your
compliance dates are wrong" and "your treatment stocks aren't really the eligible ones," and
*you* are the defense.

## Why your work matters
The paper approximates the SEC's real eligibility rule (time-weighted average quoted spread
≤ \$0.015) with an automated screen on the *daily closing* dollar spread. That is good
enough for a first pass but is known to be wrong in specific, correctable ways. The reform
also phased in over a sequence of exchange notices, not a single instant. Nailing the exact
dates and the true eligible-symbol list is what makes any estimate trustworthy.

## Week-by-week (8 weeks)

### Weeks 1–2 — Read the rule; log the exact phase-in dates (PIVOTAL)
- Read the **SEC adopting release** "Regulation NMS: Minimum Pricing Increments, Access
  Fees, and Transparency of Better Priced Orders" (Sept 18, 2024) and the follow-on
  **exchange notices** (NYSE, Nasdaq, Cboe) implementing it.
- Build `data/interim/phasein_dates.csv` (columns: `provision`, `tranche`, `effective_date`,
  `source_url`, `quote`). Provisions: the \$0.005 minimum increment (Rule 612), the
  \$0.0010 access-fee cap (Rule 610), and any odd-lot/round-lot changes with *different*
  dates. **The paper currently uses Nov 3, 2025 as the single event date — confirm or
  correct it, and flag every provision that took effect on a different day.**
- Read the 3 assigned background papers: Harris (1994, RFS), O'Hara–Saar–Zhong (2019, RAPS),
  Chung–Zhang (2014, JFM). One-paragraph memo each in `logs/reading_notes.md`.

### Weeks 3–4 — Hand-verify tick-constrained eligibility per stock (PIVOTAL)
- The exchanges publish the **official list of symbols assigned the \$0.005 increment** for
  each evaluation period. Obtain it (exchange websites / SEC filings).
- For the **75 treated and 75 control** stocks in `data/raw/sample_stocks.csv`, mark each
  `permno`/`ticker` as `eligible_half_cent` = yes/no per the official list on the effective
  date. Save `data/interim/eligibility_verified.csv` (columns: `permno`, `ticker`,
  `screen_says_treated`, `official_says_eligible`, `note`).
- **Every mismatch between our \$0.015 screen and the official list is a finding.** The AI
  will re-run the DiD keeping only stocks where the two agree ("clean treatment").

### Weeks 5–6 — Validation and the intraday upgrade
- **Effective spread reality check:** for ~10 treated names, pull a few post-event days of
  intraday quotes (any free source: exchange TAQ samples, a broker API, or the WRDS TAQ
  *full* product if your institution subscribes) and confirm whether half-cent quotes
  actually appear intraday. Record findings in `logs/intraday_check.md`. This directly tests
  the paper's central claim (that the effect is intraday and invisible in daily data).
- **Matched control:** propose a control group matched to treated on **price and
  volatility** (not just "wide-spread"), so the two groups share a counterfactual. List your
  matched pairs in `data/interim/matched_controls.csv`; the AI will re-estimate.

### Weeks 7–8 — Write and present
- Write the paper's **Institutional Background and Data sections** (you now know the rule and
  the eligibility better than anyone) and a one-page memo on what your verification changed:
  did the clean-treatment / matched-control DiD move the estimate or the pre-trends?
- Present the before/after and state plainly what daily data can and cannot show.

## Ground rules
- **Never invent a number or a date.** If a date or symbol list is not found, write "not
  found" and cite where you looked.
- Log dated entries in `logs/student_log.md`: what you did, how many items, judgment calls.
- Ask when eligibility is ambiguous (dual-listed, recently split, sub-\$1) — these calls are
  the real skill.
