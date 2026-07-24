# Project 03: Clawbacks and CEO Risk-Taking after the 2023 SEC Rule

**Student:** Aiden Shanyu Chen
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (WRDS data + DiD + diagnostics + 14-page PDF). Awaiting student
hand-collection of 10D-1 provision strength.

## Research question
Did the **mandatory** clawback regime created by SEC Rule 10D-1 (adopted Oct 2022; listing
standards effective Oct 2023) change CEO investment/M&A risk-taking — as **voluntary** clawback
adoption did (Liu, Gan & Karim 2020; Babenko et al. 2023)?

## Headline result (honest null + a debunked false positive)
**No robust evidence that the mandate changed CEO risk-taking.** In a firm+year fixed-effects
DiD comparing forced adopters (S&P SmallCap 600, ex-ante mostly *without* a voluntary clawback)
to already-covered controls (S&P 500), the post×treated effect is insignificant for
investment/assets (+0.003, t=0.81), capex (−0.001, t=−1.30), R&D (+0.002, t=1.33), acquisitions
(+0.002, t=0.81), leverage, and cash. Return volatility *does* fall (idiosyncratic vol −0.027,
t=−5.01), **but this is not a clawback effect**: parallel trends are rejected (pre-trend Wald
p<0.001), the event study shows no break at 2023, dropping COVID halves it, and size-only
placebos reproduce it (S&P 400 vs 500: −0.018, t=−3.59; below-median size: −0.018, t=−4.02). It
is a size×COVID artifact. CEO pay actually *rose* for forced adopters (+0.139, t=5.22). See
`paper/main.pdf`.

**Identification caveat / why the student matters:** treatment is an intent-to-treat *proxy*
(firm size for ex-ante clawback status). It is blind to **provision strength** — the dimension
theory says should drive behavior. Hand-coding 10D-1 strength (Task 1) enables a dose-response
test that the size proxy cannot run. See `STUDENT_TASKS.md`.

## Data
- WRDS: Compustat `funda` (capx, xrd, aqc, at, ...), CRSP `dsf`/`dsf_v2` daily returns →
  firm-year total & idiosyncratic volatility, `comp_execucomp.anncomp` (CEO pay), CCM link,
  and S&P 500 / 400 / 600 index-constituent history (`comp.idxcst_his`).
- Main DiD sample: **753 firms, 8,222 firm-years, fiscal 2015–2025** (431 control + 322 treated).

## Method / identification
- Difference-in-differences around Rule 10D-1 (Post = fyear ≥ 2023); treated = S&P 600 (forced
  adopter proxy) vs control = S&P 500 (already-covered). Firm + year FE; SE clustered by firm.
- Dynamic event-study for parallel-trends; size-based placebos; POST=2024, drop-COVID,
  two-way-cluster robustness.

## Pipeline
- `code/00_pull.py`      → WRDS pull (index, funda, CCM, Execucomp, CRSP→annual vol) to `data/raw/`
- `code/05_regpanel.py`  → build `data/processed/analytical_panel.csv`
- `code/10_did.py`       → DiD, progressive specs, event study, placebos → `output/tables/*.csv`
- `code/30_figures.py`   → `output/figures/fig1_eventstudy.pdf`, `fig2_groupmeans.pdf`
- `code/35_tables_tex.py`→ LaTeX tables from CSVs → `paper/tables/*.tex`
- `paper/main.tex`       → `paper/main.pdf` (compile with `/tmp/tectonic main.tex`)
- **Student work (pivotal):** see `STUDENT_TASKS.md`

## Folder layout (do not deviate — the audit depends on it)
- `data/raw/`        downloaded data, date-stamped, never hand-edited
- `data/interim/`    cleaned / filtered, not yet merged
- `data/processed/`  final analytical panel
- `code/`            numbered scripts (00_pull, 05_regpanel, 10_did, 30_figures, 35_tables_tex)
- `output/tables/`   regression output as CSV -> LaTeX
- `output/figures/`  PDF figures
- `logs/`            row-count + timestamp log for every data step
- `paper/`           LaTeX source (main.tex) + compiled PDF

**Rule:** every number in the paper must trace to a CSV in `output/tables/`.
No fabricated numbers, ever.
