# Project 11: Do CHIPS Act Award Announcements Move the Awardees Stock?

**Student:** Alexander Li Tang
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 13-page PDF). Awaiting student manual tasks.

## Research question
In the days around a CHIPS Act award's **first announcement** (the Commerce/NIST
Preliminary Memorandum of Terms), do the awardee's shares earn an abnormal return, and does
the reaction **scale with award size** (absolute, and relative to firm market cap)?

## Headline result (a clean, honest null)
**CHIPS award announcements did not move awardee stocks on average.** Across 15
publicly-traded U.S. awardees (2024), the mean market-model CAR[-1,+1] is **+2.6% (t = 0.99)**,
the median is **+0.5%**, only **8/15** reactions are positive, and a pre-event placebo window
is if anything negative — statistically indistinguishable from zero in every window.
A naive regression makes the reaction look like it scales steeply with award/market-cap
(**OLS t = 32, R² = 0.80**), but this is **entirely a single-leverage-point artifact**:
Wolfspeed's $750M award was **52% of its $1.4B market cap** and its stock rose 36%; drop it
and the slope collapses to **t = 1.0, R² = 0.04**. The outlier-robust Spearman correlation is
only **0.37 (p = 0.18)**. **No robust evidence that announcement returns scale with award
size** — consistent with the awards being anticipated and priced in, and with CHIPS grants
being cost-shares (tied to large mandatory private co-investment) rather than windfalls.
(See `paper/main.pdf`; every number traces to `output/tables/*.csv`.)

## Data
- **Awards:** 17 hand-collected CHIPS first-announcement dates + amounts for U.S.-listed
  recipients, from Commerce/NIST press releases (`data/raw/chips_awards_handcollected.csv`);
  2 (ADI, MTSI, Jan-2025) fall past the CRSP cutoff → 15 analyzed events.
- **Returns:** WRDS **CRSP** daily (returns, price, shares) + the CRSP value-weighted index,
  2022-06 .. 2024-12.

## Method / identification
- **Event study** — per-event market-model CARs (est. window [-252,-46]) via the shared
  `lib/event_study.py`; cross-sectional regressions of the CAR on award size with HC1-robust
  SE, plus outlier-robust Spearman rank tests and drop-one robustness (given N = 15).

## Pipeline (run in order)
- `code/00_pull.py` → raw CRSP data · `code/10_event_study.py` → per-event CARs
- `code/20_regressions.py` → tables (CSV) · `code/30_figures.py` → figures
- `code/35_tables_tex.py` → LaTeX tables · `paper/` → `tectonic main.tex` → `main.pdf`
- **Student work:** see `STUDENT_TASKS.md`

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
