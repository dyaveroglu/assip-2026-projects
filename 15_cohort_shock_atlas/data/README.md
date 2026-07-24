# Data for Project 15 — Cohort Policy-Shock Event-Study Atlas

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription.

## Sources (all via WRDS unless noted)
| File (local, not shipped) | WRDS library / source | Key fields |
|---|---|---|
| `raw/crsp_daily.csv` | CRSP `crsp.dsf` (≤2024) + `crsp.dsf_v2` (2025) | permno, date, ret |
| `raw/ff_market.csv` | Fama-French `ff.factors_daily` | date, mktrf, rf → mktret |
| `../../data/compustat_annual.csv` | Compustat `comp.funda` (shared cohort file) | permno, fyear, mktcap, sich (industry) |

The sample is the ~2,000 largest U.S. firms by 2022 market capitalization (from the shared
Compustat file), daily returns 2021-06 through 2025-12, benchmarked to the Fama-French market
return. Ten dated 2022–2025 policy/technology shocks are studied on common footing.

Public inputs (redistributable): none. Event **dates** are from public primary sources and are
listed in `code/10_atlas.py` / `code/30_extensions.py`.

## Reserved (student hand-collected, NOT in this repo)
Per `STUDENT_TASKS.md`, the cohort's reserved contribution is, for each shock, its **exact
intraday event time** (announcement vs.\ effective; pre- vs.\ post-close) and its **firm-level
exposure measure** (e.g., import-input intensity, AI-exposure, uninsured-deposit ratio),
assembled into `data/interim/exposure_by_shock.csv` keyed by permno × shock. This file is **not**
constructed by the analysis code and is left for the students; the extensions use only observable
firm characteristics (market cap, market beta, industry, idiosyncratic volatility).

## Reproduce
```bash
python code/00_pull.py         # pulls crsp_daily.csv + ff_market.csv from WRDS (needs credentials)
python code/10_atlas.py        # atlas + meta-tests  → output/tables/t1_*, t2_*
python code/30_extensions.py   # 10 meta/robustness tables → output/tables/t3..t12, figs 3–5
python code/20_figures.py      # atlas figures 1–2
python code/25_tables_tex.py   # renders tab_atlas.tex, tab_meta.tex from the CSVs
cd paper && tectonic main.tex  # compiles the paper
```
Everything downstream of the WRDS pull is fully determined by the committed `code/`. The
`output/tables/*.csv` files are the exact numbers behind every table and figure in the paper —
no number in the paper is entered by hand.
