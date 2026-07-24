# Data for Project 10 — What Cracked a Bank in March 2023 (SVB)

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription.

## Sources (all via WRDS unless noted)
| File (local, not shipped) | WRDS library / source | Key fields |
|---|---|---|
| `raw/bank_universe.csv` | CRSP `crsp.dsenames`/`msenames` (bank SIC 6020–6079, 6712; sharecodes 10/11) | permno, permco, ticker, comnam |
| `raw/crsp_daily.csv` | CRSP `crsp.dsf` (daily returns) | permno, date, ret |
| `raw/crsp_market.csv` | CRSP `crsp.dsi` (market index) | date, vwretd (value-weighted return) |
| `raw/bank_crsp_link_active.csv` / `_all.csv` | CRSP–FFIEC/NIC permco ↔ RSSD crosswalk | permco, rssd9001, name, inst_type |
| `raw/call_2022q4.csv` | Call Report `bank.wrds_call_rcon_1/_2` (2022-12-31) | RCON5597 (uninsured deposits), RCON1754/1771 (HTM), RCON1772/1773 (AFS), RCON2170 (assets), RCON3210 (equity) |
| — (pulled inline in `05_regpanel.py`) | FR Y-9C `bank.wrds_holding_bhck_1/_2` (consolidated, 2022-12-31) | BHCK2170, BHCK3210, BHCK1754/1771/1772/1773 |
| — (pulled inline in `05_regpanel.py`) | `bank.wrds_struct_relationships` (parent–offspring chain) | id_rssd_parent, id_rssd_offspring, date_start/end |

Public inputs (redistributable): none for this project. All inputs are WRDS-licensed.

## Aggregation design (documented in `code/05_regpanel.py`)
- **Assets, equity, securities** come from the **consolidated FR Y-9C**, keyed by the
  holding-company RSSD. Summing subsidiary Call Reports double-counts multi-tier holding
  companies (e.g., NYCB sums to \$270B vs. its true consolidated \$90.1B), so we do **not** sum.
- **Uninsured deposits (RCON5597)** exist only in bank-level Call Reports, so the baseline
  uses the **lead** (largest-asset) subsidiary bank. Correctly hand-aggregating multi-bank
  holding companies is a reserved **student task** (see `STUDENT_TASKS.md`, Task 2) and is
  **not** performed by the automated pipeline.

## Reproduce
```bash
python code/00_pull.py         # pulls the raw CRSP + Call Report files above (needs WRDS credentials)
python code/05_regpanel.py     # builds data/interim/bank_reg_panel.csv (needs WRDS: Y-9C + struct chain)
python code/10_event_study.py  # market-model CARs → data/interim/cars.csv
python code/20_regressions.py  # summary/corr/CAR-window/horse-race/robustness → output/tables/t1..t5
python code/30_figures.py      # fig1 binscatter, fig2 quartiles
python code/35_tables_tex.py   # renders tab_sumstats/tab_cars/tab_main from the CSVs
python code/40_extensions.py   # heterogeneity, matching, randomization inference, placebo, power → t6..t9 (+ fig3)
cd paper && tectonic main.tex  # compiles the paper
```
Steps `00` and `05` require live WRDS access (raw pull + consolidated Y-9C / structure chain).
**Everything downstream of the committed interim files is fully reproducible offline:**
`10`, `20`, `30`, `35`, and `40` run from the shipped `data/raw/*.csv` and
`data/interim/*.csv`. The `output/tables/*.csv` in the repo are the exact numbers behind every
table and figure in the paper; the paper cannot drift because each `paper/tables/*.tex` is
rendered directly from a CSV.
