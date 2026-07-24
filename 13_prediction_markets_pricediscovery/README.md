# Project 13: Where Does Price Discovery Happen: Kalshi vs Polymarket?

**Student:** Dildora Jo'rabekova
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 15-page PDF). Awaiting student hand-matching.

## Research question
For event contracts listed on BOTH Kalshi and Polymarket with identical settlement, which
venue leads price discovery?

## Headline result
**Polymarket leads.** Across 15 matched FOMC outcome contracts (4 meetings, 32,885
contract-hours), Polymarket's Hasbrouck information share averages **0.68** (median 0.79,
and **0.82** weighted by trading activity); Polymarket leads in 11 of 15 pairs, the four
exceptions being the thinnest far-dated contracts with no Granger causality in either
direction. The pooled lead–lag cross-correlation peaks at Polymarket leading Kalshi by one
hour, and in the resolved June-2026 meeting Polymarket's mean absolute pricing error is
~1/5 of Kalshi's in the final week. The two prices are cointegrated (spread stationary in
87% of pairs; mean gap 3.6¢). The CFTC-regulated retail venue is the *follower* on US-macro
events — the reverse of a "regulation breeds price quality" prior. See `paper/main.pdf`.
**Identification caveat:** contracts are matched mechanically (same FOMC meeting + outcome);
verifying *rule-by-rule identical settlement* is the student's pivotal task (`STUDENT_TASKS.md`).

## Data
- **Kalshi** trade API (`api.elections.kalshi.com`): hourly candlestick YES prices.
- **Polymarket** Gamma API + CLOB `prices-history`: hourly YES-token prices.
- 4 matched FOMC meetings (Jun/Jul/Sep/Oct 2026), 5 outcomes each; free public APIs, no auth.

## Method / identification
- Bivariate VECM with imposed cointegrating vector (1,−1) → Hasbrouck (1995) information
  shares (Cholesky bounds) + Gonzalo–Granger component weights; lead–lag cross-correlation;
  bidirectional Granger causality; resolving-news event study on the resolved June meeting.

## Pipeline
- `code/00_pull.py` → both APIs · `code/10_build.py` → aligned hourly panel + pair selection
- `code/20_analyze.py` → Hasbrouck/lead-lag/Granger · `code/25_event_study.py` → June event study
- `code/30_figures.py` → 4 figures · `code/35_tables_tex.py` → LaTeX tables · `paper/` → PDF
- **Student work (pivotal):** see `STUDENT_TASKS.md`

## Folder layout (do not deviate — the audit depends on it)
- `data/raw/`        downloaded data, date-stamped, never hand-edited
- `data/interim/`    cleaned / filtered, not yet merged
- `data/processed/`  final analytical panel
- `code/`            numbered scripts (00_download, 10_clean, 20_merge, 30_analyze ...)
- `output/tables/`   regression output as CSV -> LaTeX
- `output/figures/`  PDF figures
- `logs/`            row-count + timestamp log for every data step
- `paper/`           LaTeX source (main.tex) + compiled PDF

**Rule:** every number in the paper must trace to a CSV in `output/tables/`.
No fabricated numbers, ever.
