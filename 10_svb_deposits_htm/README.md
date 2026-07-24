# Project 10: What Cracked a Bank in March 2023

**Student:** Aaron Lu Zhang
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 9-page PDF). Awaiting student manual tasks.

## Research question
In the SVB collapse window (Mar 8–13, 2023), was the bank-equity crash driven more by
**uninsured-deposit exposure** or by **hidden HTM/securities losses**, controlling for size?

## Headline result
Uninsured-deposit exposure wins the horse race: a 1-SD higher uninsured/assets ratio →
**−4.1 to −5.0pp** CAR (t up to −3.1), robust to size and excluding G-SIBs; securities
losses are insignificant conditional on funding. The market priced *run risk*, not
*mark-to-market risk*. (See `paper/main.pdf`, tables in `output/tables/`.)

## Data
- WRDS CRSP daily (returns, market index); FR Y-9C consolidated + Call Report (bank-reg
  library); 165 publicly-traded U.S. banks, 2022Q4 exposures.

## Method / identification
- Market-model event study (est. window [-252,-46]) + cross-sectional CAR regressions,
  HC1-robust SE. Subsidiary Call Reports aggregated to holding companies via
  `wrds_struct_relationships`.

## Pipeline (run in order)
- `code/00_pull.py` → raw WRDS data · `code/05_regpanel.py` → 2022Q4 reg panel
- `code/10_event_study.py` → CARs · `code/20_regressions.py` → tables
- `code/30_figures.py` → figures · `code/35_tables_tex.py` → LaTeX tables
- `paper/` → `tectonic main.tex` → `main.pdf`
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
