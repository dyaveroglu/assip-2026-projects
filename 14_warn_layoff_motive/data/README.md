# Data for Project 14 — What Kind of Layoff Does the Market Punish? (WARN Notices)

**The `data/` folder is intentionally not published.** The analysis combines
free, official state WARN databases with data licensed from Wharton Research Data
Services (WRDS), which may not be redistributed. This README documents every
source so the pipeline can be reproduced by anyone with the appropriate WRDS
subscription. Every number in the paper traces to a CSV in `output/tables/` and is
reproduced by the code in `code/`.

## Public sources (state WARN databases — free, official)
| File (local) | Source | Key fields |
|---|---|---|
| `raw/ca_2022_23.pdf` … `raw/ca_2025_26.xlsx` | California EDD detailed WARN reports (fiscal-year PDF/XLSX) | filer, notice date, employees affected, location, layoff/closure type |
| `raw/warn_ca.csv` | California WARN, parsed from the EDD files above | normalized notice records |
| `raw/warn_tx.csv`, `raw/warn_tx.json` | Texas Workforce Commission WARN (`data.texas.gov`) | filer, notice date, employees, location |
| `raw/warn_or.csv`, `raw/warn_or.json` | Oregon WARN (`data.oregon.gov`) | filer, notice date, employees, location, type |

Pooled and restricted to 2022–2025: 6,560 notices from 3,450 distinct filer names
(CA 5,548; TX 815; OR 190).

## WRDS sources (licensed — not redistributable)
| File (local) | WRDS library / source | Key fields |
|---|---|---|
| `raw/crsp_daily.csv` | CRSP `crsp.dsf` (daily stock file) | permno, date, ret, prc, vol, shrout |
| `raw/crsp_market.csv` | CRSP `crsp.dsi` (daily market index) | date, vwretd (value-weighted), sprtrn (S&P 500) |
| `raw/crsp_stocknames.csv` | CRSP `crsp.stocknames` | permno, ticker, company name history |
| `raw/comp_company.csv` | Compustat `comp.company` | gvkey, legal name, SIC, country |
| `raw/comp_funda.csv` | Compustat `comp.funda` (annual fundamentals) | at, emp, sale, prcc_f, csho, sich |
| `raw/ccm_link.csv` | CRSP/Compustat Merged link table | gvkey ↔ permno |

## Interim / processed
- `interim/warn_all.csv` — pooled, cleaned multi-state WARN panel.
- `interim/name_matches.csv` — high-precision fuzzy filer→listed-firm matches.
- `interim/permno_gvkey.csv` — CRSP↔Compustat identifier crosswalk.
- `interim/warn_events.csv` — firm-level layoff events (site notices clustered) + Compustat fundamentals.
- `interim/cars.csv` — market-model CARs per firm-event; `interim/ar_path.csv` — event-time AR path.
- `processed/analytical_panel.csv` — the final firm-event cross-section (CARs + characteristics).

## Reproduce
```bash
python code/00_pull_warn.py      # pulls state WARN + WRDS raw files (needs credentials)
python code/05_match_tickers.py  # fuzzy match filer names to CRSP/Compustat
python code/08_build_events.py   # firm-event panel + Compustat fundamentals
python code/10_event_study.py    # market-model CARs + event-time AR path
python code/20_regressions.py    # tables t1–t6 (CSV)
python code/25_extensions.py     # heterogeneity, randomization inference, alt benchmarks, power
python code/30_figures.py        # figures (incl. randomization-inference histogram)
python code/35_tables_tex.py     # renders paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex    # compiles the paper
```
Everything downstream of the WRDS/WARN pull (the panel, all tables, all figures,
the paper) is fully determined by the committed `code/`. The `output/tables/*.csv`
are the exact numbers behind every table and figure in the paper.

## Reserved for the student (NOT in this pipeline — see `STUDENT_TASKS.md`)
The hand-collected inputs are deliberately **not** constructed by the automated
code: `interim/matches_verified.csv` (verified ticker matches),
`interim/matches_manual.csv` (rescued brand/subsidiary layoffs),
`interim/motive_coded.csv` (the hand-coded layoff **motive** — the core
contribution), and `interim/confounds.csv` (firm-specific confound flags). The
extension tables use only the machine `is_closure` proxy and observable firm
characteristics; the hand-coded motive is left entirely for the student.
