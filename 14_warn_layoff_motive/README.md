# Project 14: What Kind of Layoff Does the Market Punish? A WARN-Notice Study

**Student:** Andy Pham
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 15-page PDF). Awaiting student hand-matching + motive coding.

## Research question
Do abnormal stock returns around mass-layoff (WARN Act) announcements differ by
the **size** of the layoff and by its **motive** (cost-cutting vs strategic
reallocation)?

## Headline result
The market gives WARN mass-layoff notices a **modest but significant negative**
verdict: CAR[0,+5] = **−1.6% (t=−2.41)**, post-event, with a clean near-zero
placebo (−0.18%, t=−0.32). But the average hides everything. It is **not** about
how many workers are cut — absolute headcount is irrelevant (t=0.46). It is about
**materiality**: a 1-SD larger layoff *relative to the firm* moves CAR by **−3.3pp
(t=−2.77)**; small firms lose **−3.9% (t=−2.86)** while large firms are unaffected
(**+0.4%, ns**); the bite is a small-firm phenomenon (size×relative-layoff
interaction −0.065, t=−2.86). Crucially, the one machine-readable **motive** proxy —
plant *closure* (reallocation/exit) vs ongoing-operation *layoff* (cost-cutting) —
shows **no CAR difference (t=−0.07)**. Distinguishing motive requires reading the
announcements and hand-coding it — the pivotal student task. (See `paper/main.pdf`;
all numbers trace to `output/tables/*.csv`.)

## Data
- **State WARN databases (free, official):** California EDD (PDF/XLSX, parsed),
  Texas Workforce Commission (`data.texas.gov`), Oregon (`data.oregon.gov`) —
  6,560 notices, 2022–2025, 3,450 filers.
- **WRDS:** CRSP daily returns + value-weighted index; Compustat fundamentals;
  CRSP/Compustat link. 615 matched firm-events at 328 listed firms (2022–2024,
  limited by CRSP index coverage).

## Method / identification
- Market-model event study (estimation window [-252,-46], shared
  `lib/event_study.py`) around each WARN notice date; firm-level events built by
  clustering site notices. Cross-sectional CAR regressions with firm-clustered SE;
  fuzzy name→ticker matching (leading-anchor token-set, high precision).

## Pipeline (run in order)
- `code/00_pull_warn.py` → raw WARN + combined panel
- `code/05_match_tickers.py` → fuzzy match filer names to CRSP/Compustat
- `code/08_build_events.py` → firm-event panel + Compustat fundamentals
- `code/10_event_study.py` → market-model CARs + event-time AR path
- `code/20_regressions.py` → tables t1–t6 (CSV)
- `code/30_figures.py` → figures · `code/35_tables_tex.py` → LaTeX tables
- `paper/` → `tectonic main.tex` → `main.pdf`
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
