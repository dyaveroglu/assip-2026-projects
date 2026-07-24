# Project 07: BNPL Enters the Credit File

**Student:** Rakshana Damodaran
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 8-page PDF). Awaiting student hand-collection.

## Research question
When BNPL lenders began **furnishing** loans to credit bureaus (2025), did credit-reporting
complaints against the furnisher spike — as widely feared?

## Headline result (honest null / reversal)
**No furnishing-specific effect.** Credit-reporting complaints rose sector-wide, not
specifically at Affirm (the furnisher): within-Affirm the credit-reporting *share* fell
(DiD −0.30, t=−3.6, as other complaints grew faster), and the cross-firm DiD is insignificant
(t=−0.76). Non-furnishing peers grew as much or more (Klarna ×11 vs Affirm ×2.7). See
`paper/main.pdf`. Identification caveat: near-simultaneous industry adoption ⇒ the clean test
needs the student's hand-collected furnishing dates.

## Data
- CFPB Consumer Complaint Database (free API); 19,354 complaints, 5 pure-play BNPL firms,
  2022–2026.

## Method / identification
- Within-firm and cross-firm difference-in-differences around Affirm's ~Apr-2025 furnishing;
  ln(1+count) and share DVs; firm + month FE; SE clustered by firm.

## Pipeline
- `code/00_pull.py` → CFPB pull · `code/10_did.py` + `code/15_analysis.py` → DiD + tables
- `code/30_figures.py` → figures · `code/35_tables_tex.py` → LaTeX · `paper/` → PDF
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
