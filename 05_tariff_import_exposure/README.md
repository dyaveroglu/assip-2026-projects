# Project 05: Import Exposure and the April 2025 Reciprocal-Tariff Shock

**Student:** Deniz Yaveroglu
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 14-page PDF). Awaiting student 10-K sourcing work.

## Research question
Did high imported-input-exposure U.S. firms underperform after the April 2, 2025 reciprocal-
tariff announcement, and did the April 9 pause reverse it? Identification is a **paired,
opposite-signed event study**: the same industry exposure measure should load *negatively*
on the April 2–4 shock and *positively* on the April 9 pause.

## Headline result (real, conditional, honestly caveated)
**Yes — conditionally, and symmetrically.** In the *raw* cross-section imported-input
intensity has no clean relationship with returns (it is dominated by size and beta). But
**conditional on size and market beta**, a 1-SD increase in industry imported-input
intensity is associated with a **−0.73pp** abnormal return on the shock (t = −2.35) and
**+0.60pp** on the pause (t = 1.78); over the full Apr 3–8 sell-off the shock effect is
−1.34pp (t = −2.48). Excluding microcaps the pattern is opposite-signed and nearly
symmetric (**−0.77pp / +0.77pp, both t ≈ 2.1**) and the shock-plus-pause **round-trip is a
precise zero** (t = −0.46): the pause reversed the shock. Honest caveats: the effect is
*conditional* (not visible unconditionally), and there is a **pre-announcement pre-trend**
(exposure loads −0.53pp, t = −2.22, in the Mar 27–Apr 2 window, because auto tariffs hit
Mar 26 and the package was pre-trailed). See `paper/main.pdf`; every number traces to
`output/tables/`.

## Data
- **WRDS CRSP** `dsf_v2` daily returns (5,072 U.S. common stocks, 2024–2025); **Fama–French**
  daily market factor (crsp.dsi has no 2025 rows); **Compustat** fundamentals via CCM link.
- **BEA** 2023 Summary Import Matrix + Gross-Output-by-industry (public bea.gov files) →
  industry imported-input intensity = imported intermediate inputs ÷ gross output, mapped to
  firms by NAICS. Analytical panel: **4,275 firms, 73 NAICS-3 industries.**

## Method / identification
- Market-model CARs (shared `lib/event_study.market_model_cars`, est. window [−252,−46]) on
  two paired events (shock day-0 = Apr 3; pause day-0 = Apr 9); cross-sectional regressions
  of CAR on standardized imported-input intensity + controls (size, beta, COGS/sales,
  leverage, book/market), SE **clustered by NAICS-3** (HC1 as robustness).

## Pipeline (run in order)
- `code/00_pull.py` → raw CRSP/FF/Compustat/BEA · `code/05_exposure.py` → industry intensity
- `code/10_event_study.py` → paired CARs · `code/20_regressions.py` → tables t1–t6
- `code/30_figures.py` → figures · `code/35_tables_tex.py` → LaTeX · `paper/` → `main.pdf`
- **Student work (pivotal):** see `STUDENT_TASKS.md` (`data/interim/firms_to_verify.csv` ready)

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
