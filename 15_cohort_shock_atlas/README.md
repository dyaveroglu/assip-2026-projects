# Project 15: Anticipation, Speed, and Reversal: A Policy-Shock Event-Study Atlas

**Student:** ASSIP 2026 Cohort
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 7-page PDF). Cohort co-authored; awaiting per-shock exposure hand-off.

## Research question
Measured on common footing, how do the dense 2022–2025 U.S. policy/tech shocks differ — in how
much the market moves, differentiates firms, and propagates?

## Headline result
**Differentiation scales with shock size** (corr 0.69 between |market move| and cross-sectional
CAR SD); the **tariff shock differentiates most** (SD 5.8%); **SVB is the propagation outlier**
(drift −3.5%, reversal corr +0.42 = contagion). Reversal is otherwise mild/mixed. (See
`paper/main.pdf`.)

## Data
- WRDS CRSP daily (`dsf` + `dsf_v2` for 2025) for ~2,000 large firms + Fama-French market;
  10 dated shocks 2022–2025.

## Method / identification
- Uniform market-model event study (shared `lib/event_study.py`) across all shocks + cross-shock
  meta-analysis (differentiation, drift, reversal).

## Pipeline
- `code/00_pull.py` → `10_atlas.py` → `20_figures.py` / `25_tables_tex.py` → `paper/` PDF
- **Cohort work (each student owns a shock):** see `STUDENT_TASKS.md`

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
