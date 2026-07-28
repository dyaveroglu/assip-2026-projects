> **Why this folder has no data files:** every input for this project is licensed from WRDS
> (Compustat / CRSP / Execucomp / CCM), which may not be redistributed — so nothing is committed
> here. As a registered GMU student you can pull it yourself: see `WRDS_ACCESS.md` at the repo
> root and run this project's `code/00_*.py`. Sources are documented below.

# Data for Project 03 — Clawbacks & CEO Risk-Taking

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription.

## Sources (all via WRDS unless noted)
| File (local, not shipped) | WRDS library / source | Key fields |
|---|---|---|
| `raw/funda.csv` | Compustat `comp.funda` (annual fundamentals) | at, capx, xrd, aqc, dltt, dlc, che, … |
| `raw/crsp_annual_vol.csv` | CRSP `crsp.dsf`/`dsf_v2` (daily returns → firm-year vol) | total & idiosyncratic volatility |
| `raw/execucomp_ceo.csv` | Execucomp `comp.anncomp` | CEO total pay, equity share |
| `raw/ccm_link.csv` | CRSP/Compustat Merged link table | gvkey ↔ permno |
| `raw/sp_index_members.csv` | Compustat `comp.idxcst_his` | S&P 500/400/600 membership history |

Public inputs (redistributable, whitelisted back into the repo if needed): none for this project.

## Reproduce
```bash
python code/00_pull.py        # pulls the raw files above from WRDS (needs credentials)
python code/05_regpanel.py    # builds data/processed/analytical_panel.csv
python code/10_did.py         # main DiD → output/tables/t1..t5
python code/15_extensions.py  # heterogeneity, matching, randomization inference, power
python code/30_figures.py     # figures
python code/35_tables_tex.py  # renders paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex # compiles the paper
```
Everything downstream of the WRDS pull (the panel, all tables, all figures, the paper) is fully
determined by the committed `code/`. The `output/tables/*.csv` in the repo are the exact numbers
behind every figure in the paper.
