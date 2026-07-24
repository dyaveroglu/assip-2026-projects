# Project 04: Do Anomalies Die When They Are Published?

**Student:** Christopher Abhi Dadoo
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 14-page PDF). Awaiting student hand-collection.

## Research question
Do anomaly long-short returns fall after their academic publication, and is the decay larger
for mispricing- than risk-framed anomalies (McLean–Pontiff 2016)?

## Headline result (H1 confirmed; H2 fragile; H3 honest null)
**Anomaly returns fall by ~half from in-sample to post-publication.** Equal-weighted across
212 predictors, the average anomaly earns **0.61%/mo in-sample → 0.42% post-sample → 0.30%
post-publication** (paired within-anomaly decline −51%, t = −7.6), replicating McLean–Pontiff
on a larger, more recent (through-2024) sample. The panel post-publication coefficient is
−0.24 to −0.27 %/mo and survives anomaly + calendar-month fixed effects (t = −3.2).
*But:* the **incremental** publication effect (beyond general out-of-sample decay) is
significant with anomaly FE (−0.13, t = −2.2) yet **collapses to zero with time FE** — the
decline is an out-of-sample phenomenon hard to pin to the publication date itself. And a
category-based **risk-vs-mispricing split is a null** (interaction −0.03, t = −0.4 broad;
+0.10, t = 1.0 narrow — sign not even stable). Sharpening H2 (exact sample months) and
testing H3 (authors' stated framing) requires the student's hand-reading of ~60 articles.
See `paper/main.pdf`.

## Data
- Open Source Asset Pricing (Chen & Zimmermann 2022), release v2.0.0: `PredictorLSretWide.csv`
  (monthly long-short returns, 212 predictors) + `SignalDoc.csv` (publication year, sample
  window, economic category). Public, downloaded in `code/00_download.py`. 173,302
  anomaly-months, 1926–2024.

## Method / identification
- Regime panel (in-sample / post-sample / post-publication) around each anomaly's own sample-end
  and publication year; pooled panel regressions with anomaly and calendar-month FE, SE
  clustered by anomaly (two-way by anomaly & month); nested McLean–Pontiff out-of-sample vs
  publication decomposition; risk-vs-mispricing interaction.

## Pipeline
- `code/00_download.py` → OP data pull · `code/10_build_panel.py` → regime panel
- `code/20_regressions.py` → tables t1–t6 · `code/30_figures.py` → figures
- `code/35_tables_tex.py` → LaTeX · `paper/` → PDF
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
