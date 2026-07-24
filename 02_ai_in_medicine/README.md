# Project 02: The Diffusion of AI into Medicine

**Student:** Michael Yucheng Zhou
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 6-page PDF). Awaiting student clinical coding.

## Research question
Who is capturing AI's move into medicine (incumbents vs tech entrants), and does the market
value it?

## Headline result
Medical-AI patents (AI ∩ CPC A61) **~doubled 2013→2020**. **Incumbent health firms hold 47%**
(482 firms) vs tech entrants 19% (135 firms). Medical-AI patent stock → higher Tobin's Q
(+0.48, t=5.0) and market cap (+0.13, t=5.3), premium concentrated in incumbents. (See
`paper/main.pdf`.)

## Data
- USPTO AIPD (AI flags, ends 2023) + PatentsView CPC A61 (medical) + KPSS patent→permno/value
  + WRDS Compustat. Shared panel `assip26/data/patent_analytical_panel.csv`.

## Method / identification
- Two-way (firm+year) FE value regressions; SE clustered by firm. Reuses the shared patent
  panel built for #01.

## Pipeline
- `code/10_analysis.py` → `20_figures.py` / `25_tables_tex.py` → `paper/` PDF
- **Student work (crux = clinical application coding):** see `STUDENT_TASKS.md`

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
