# Project 01: Cognitive vs Physical Automation

**Student:** Michael Philipov
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 7-page PDF). Awaiting student hand-coding.

## Research question
Do cognitive (AI) and physical (robotics) automation leave different footprints inside the
firms that create them — jobs vs. value?

## Headline result
AI-patent stock → **employment growth** (+0.055, t=7.5); robotics stock → **higher Tobin's Q**
(+0.40, t=5.0) but no employment effect. Event study: employment +~11% and productivity +~6%
over 5 years after a firm's first AI patent, flat pre-trends. At the firm level, AI is
labor-*complementary*. (See `paper/main.pdf`.)

## Data
- USPTO AIPD (AI flags) + PatentsView CPC B25J (robotics) + KPSS patent→permno/value +
  WRDS Compustat. 7,087 firms, 83,976 firm-years, 1995–2024. Raw on Hopper
  `/scratch/lgao9/assip26_patents/`; shared panel `assip26/data/patent_*`.

## Method / identification
- Two-way (firm+year) FE panels + first-AI-patent adoption event study; SE clustered by firm.

## Pipeline
- `code/process_patents.py` (on Hopper) → `code/01_pull_compustat.py` → `code/05_panel.py`
  → `code/10_analysis.py` → `20_figures.py` / `25_tables_tex.py` → `paper/` PDF
- **Student work (crux = replacing vs augmenting):** see `STUDENT_TASKS.md`

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
