# Data for Project 05 — Import Exposure and the April 2025 Reciprocal-Tariff Shock

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS
subscription plus the public BEA input-output files.

## Sources
| File (local, not shipped) | Library / source | Key fields |
|---|---|---|
| `raw/crsp_daily.csv` | CRSP `crsp.dsf_v2` (WRDS) | permno, date, ret (daily returns, 2024-01–2025-05) |
| `raw/market_ff.csv` | Fama–French daily factors (`ff.factors_daily`, WRDS) | date, mktret = mktrf+rf |
| `raw/universe.csv` | CRSP `crsp.stocknames_v2` (WRDS) | permno, ticker, comnam, siccd (US common shares) |
| `raw/compustat_funda.csv` | Compustat `comp.funda` (WRDS) | at, cogs, sale, dltt, dlc, ceq, csho, prcc_f, naicsh |
| `raw/ccm_link.csv` | CRSP/Compustat Merged link (`crsp.ccmxpf_lnkhist`, WRDS) | gvkey ↔ permno, linkdt, linkenddt, linkprim |
| `raw/bea_import_matrix.xlsx` | **BEA** Summary Import Matrix, 2023, Before Redefinitions (public, bea.gov) | imported intermediate inputs by using industry |
| `raw/bea_gross_output.xlsx` | **BEA** Gross Output by Industry, table TGO105-A (public, bea.gov) | 2023 gross output by industry |

**Public inputs (redistributable):** the two BEA Excel files are public downloads from
bea.gov and may be shipped with the repo; the WRDS extracts may not.

## Derived files (built by the pipeline, not hand-edited)
- `interim/bea_industry_intensity.csv` — imported-input intensity by BEA summary industry.
- `interim/industry_import_intensity.csv` — the BEA→NAICS-3 crosswalk with intensity per NAICS-3.
- `interim/cars.csv` — market-model CARs for the shock and pause events.
- `interim/firms_to_verify.csv` — **stratified sample of firms for the student's 10-K sourcing
  task** (see `STUDENT_TASKS.md`). Reserved input for the manual, hand-collected contribution.
- `processed/analytical_panel.csv` — final firm-level panel (CARs + exposure + controls).

## Reproduce
```bash
python code/00_pull.py         # pulls the WRDS raw files above (needs credentials)
python code/05_exposure.py     # builds BEA imported-input intensity → NAICS-3 crosswalk
python code/10_event_study.py  # market-model CARs for the paired Apr-2025 events
python code/20_regressions.py  # analytical panel + tables t1–t6
python code/30_figures.py      # figures fig1–fig2
python code/40_extensions.py   # heterogeneity, placebo, randomization inference, power (t7–t10, fig3)
python code/35_tables_tex.py   # renders paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex  # compiles the paper
```
Everything downstream of the WRDS pull (the panel, all tables, all figures, the paper) is fully
determined by the committed `code/`. The `output/tables/*.csv` in the repo are the exact numbers
behind every table and figure in the paper.

## Reserved for the student (do not construct from observable data)
Per `STUDENT_TASKS.md`, the hand-collected firm-level 10-K input-sourcing measure
(`import_reliance`, `source_countries`, `finished_vs_input`, `tariff_language`) and the
April-2025 country-tariff map (`country_tariff_apr2025.csv`) are the student's manual
contribution. The extension analyses in `code/40_extensions.py` use only observable industry-
and firm-level characteristics and are deliberately orthogonal to that reserved test.
