# Project 06: Does Housing Re-Price Disaster Risk Only Where People Believe?

**Student:** Mateo Eduardo Stine
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 13-page PDF). Awaiting student hand-collection.

## Research question
After a major hurricane makes latent risk salient, do home values in hard-hit counties adjust,
and does the adjustment depend on local climate beliefs (the "re-price only if you believe it"
hypothesis of Baldauf-Garlappi-Yannelis 2020)?

## Headline result (honest null / reversal)
**No robust belief-conditional re-pricing.** Across 600 counties and 32,085 county-months
around Hurricanes Ian (2022) and Helene (2024), the average effect of being FEMA-designated
hard-hit is a **precise null** (Treat x Post = +0.001, t=0.34). This masks a differential
pre-trend concentrated in high-belief Florida coastal (Ian) markets; net of a treated linear
trend the effect is a small **-0.5%** (t=-3.0). The belief-conditioning hypothesis fails every
robustness cut: a high/low "worried" split gives +0.020 (t=2.5, **wrong sign**), which
reverses to -0.011 (t=-2.5) within Helene, is a null with a 2020 GOP-vote proxy (+0.002,
t=0.5), and **vanishes once pre-trends are removed** (+0.003, t=0.8). The cleanest-identified
subsample (low-belief, parallel pre-trends) shows the **largest** decline (-1.5% by 20 months)
-- the opposite of the belief mechanism. Storm-level: Ian's hard-hit coast **rose** +7.3%
(t=7.7), Helene's inland hard-hit counties **fell** -1.1% (t=-2.4). See `paper/main.pdf`.
Identification caveat: exposure is a coarse FEMA binary; the sharp test needs the student's
hand-collected landfall geography.

## Data (all free, no key)
- **Zillow ZHVI** county monthly home values (2000-2026).
- **OpenFEMA** DisasterDeclarationsSummaries (Ian: DR-4673/4677; Helene: DR-4827/28/29/30/31/32);
  treated = Individuals & Households Program county.
- **Yale Climate Opinion Maps** county "worried"/"happening" (belief); **2020 county vote share**
  (inverse-belief robustness).
- **FEMA National Risk Index** county hurricane-risk score.

## Method / identification
- Stacked exposure difference-in-differences (unit = county x event), balanced [-24,+20]-month
  window, ln(ZHVI), county x event FE + event x calendar-month FE, SE clustered by county.
  Belief moderation via Treat x Post x Moderator; dynamic event study + pre-trend diagnostics.

## Pipeline
- `code/00_pull.py` -> download all 5 sources to `data/raw/`
- `code/10_build.py` -> stacked balanced panel -> `data/processed/panel.csv`
- `code/20_did.py` -> DiD, belief moderation, event study, pre-trends -> `output/tables/*.csv`
- `code/30_figures.py` -> 3 figures -> `output/figures/*.pdf`
- `code/35_tables_tex.py` -> `paper/tables/*.tex`; `paper/main.tex` -> `paper/main.pdf`
- **Student work (pivotal):** see `STUDENT_TASKS.md`

## Folder layout (do not deviate -- the audit depends on it)
- `data/raw/`        downloaded data, date-stamped, never hand-edited
- `data/interim/`    cleaned / filtered, not yet merged
- `data/processed/`  final analytical panel
- `code/`            numbered scripts (00_pull, 10_build, 20_did, 30_figures, 35_tables_tex)
- `output/tables/`   regression output as CSV -> LaTeX
- `output/figures/`  PDF figures
- `logs/`            row-count + timestamp log for every data step
- `paper/`           LaTeX source (main.tex) + compiled PDF

**Rule:** every number in the paper must trace to a CSV in `output/tables/`.
No fabricated numbers, ever.
