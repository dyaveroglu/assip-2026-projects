# Data for Project 12 — Half-Cent Tick & Access-Fee Cut

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription.

## Sources (all via WRDS unless noted)
| File (local, not shipped) | WRDS library / source | Key fields |
|---|---|---|
| `raw/screening_universe.csv` | CRSP `crsp.dsf_v2` (CIZ format), Sept 2025 | per-stock Sept mean `dlybid`/`dlyask` spread, price, `dlyprcvol` |
| `raw/sample_stocks.csv` | derived from the screening universe | 75 treated (tick-constrained) + 75 control (wide), `permno`, `ticker`, `treated` |
| `raw/panel_daily.csv` | CRSP `crsp.dsf_v2` (CIZ format), 2025-08-25..2025-12-19 | daily closing NBBO (`dlybid`,`dlyask`), `dlyclose`, `dlyvol`, `dlyprcvol`, `dlyret`, `dlynumtrd` |
| `processed/panel_full.csv` | built by `code/10_build.py` | dollar/relative/effective spreads, event-time index, winsorized outcomes |
| `processed/panel_did.csv`  | built by `code/10_build.py` | the 4wk-pre + 4wk-post DiD analysis window (5,820 stock-days) |

**Data-source note (stated plainly, per the project brief).** The ideal input is WRDS **TAQ**
intraday NBBO, from which one computes a time-weighted quoted spread and a trade-based effective
spread. TAQ intraday is **not subscribed** on this account: only the TAQ *sample* libraries
(`taqsamp`/`taqmsamp`) are available, and they cover only a handful of 2008/2009/2021 days — there
is no 2025 TAQ. We therefore use the brief's sanctioned fallback, the CRSP daily stock file
(`crsp.dsf_v2`), which records each security's daily **closing** consolidated NBBO. The quoted
spread proxy is `ask − bid` (dollar) and `(ask − bid)/midpoint` (relative), the Chung–Zhang (2014)
daily proxy. This is a daily closing-quote proxy, **not** a time-weighted intraday measure — the
central limitation the paper documents.

Public inputs (redistributable): none for this project.

**Reserved for the student (not built here; see `../STUDENT_TASKS.md`):**
`interim/phasein_dates.csv` (hand-verified per-tranche compliance dates),
`interim/eligibility_verified.csv` (per-stock official half-cent eligibility), and
`interim/matched_controls.csv` (a control group hand-matched to treated on price and volatility).
The extension code deliberately does **not** construct these.

## Reproduce
```bash
python code/00_pull.py        # WRDS pull: screening universe, sample, daily panel → data/raw/ (needs credentials)
python code/10_build.py       # builds data/processed/panel_full.csv and panel_did.csv
python code/20_did.py         # main DiD, event-study, placebo, mechanism → output/tables/t1..t8
python code/30_figures.py     # event-time / event-study / censoring figures → output/figures/
python code/35_tables_tex.py  # renders paper/tables/*.tex from the base CSVs
python code/40_extensions.py  # heterogeneity, overlap, alt-definitions, randomization inference, power → t9..t13 + fig4
cd paper && tectonic main.tex # compiles the paper (main.pdf)
```
Everything downstream of the WRDS pull (the panels, all tables, all figures, the paper) is fully
determined by the committed `code/`. The `output/tables/*.csv` in the repo are the exact numbers
behind every table and figure in the paper.
