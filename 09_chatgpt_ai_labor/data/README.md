# Data for Project 09 — Did ChatGPT Reprice AI-Exposed Labor?

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription
and the two public inputs noted below.

## Sources
| File (local, not shipped) | Library / source | Key fields |
|---|---|---|
| `raw/crsp_daily.csv` | CRSP `crsp.dsf` (daily stock file, via WRDS) | permno, date, ret, prc, shrout |
| `raw/crsp_market.csv` | CRSP value-weighted market index (via WRDS) | date, vwretd |
| `raw/crsp_universe.csv` | CRSP `crsp.msenames`/header (via WRDS) | permno, permco, ticker, comnam, siccd, naics4 |
| `raw/compustat_funda.csv` | Compustat `comp.funda` (annual fundamentals, via WRDS) | ceq, emp, at, sale, cik |
| `raw/ccm_link.csv` | CRSP/Compustat Merged link table (via WRDS) | gvkey ↔ permno |
| `raw/AIOE_DataAppendix.xlsx` | Felten, Raj & Seamans (2021), **public data appendix** | AIOE by occupation; AIIE by industry |
| SEC EDGAR (crawled at run time) | `data.sec.gov` submissions API + `www.sec.gov` Archives | most-recent pre-ChatGPT 10-K text |

**Public inputs (redistributable):** the Felten–Raj–Seamans AI-exposure appendix
(`raw/AIOE_DataAppendix.xlsx`) and the SEC EDGAR 10-K filings. The AI Industry Exposure (AIIE)
index and the AI Occupational Exposure (AIOE) index are from the authors' public data appendix
to *Strategic Management Journal* 42(12), 2195–2217.

## Interim / processed artifacts (rebuilt by `code/`, not hand-edited)
- `interim/aioe_by_occupation.csv`, `interim/aiie_by_naics4.csv` — AIOE/AIIE parsed from the
  public appendix; industry AI exposure by 4-digit NAICS.
- `interim/naics_buckets.csv` — the machine `supplier` / `substitution` / `user` sign buckets
  (a coarse NAICS rule; the student's hand-coded task exposure replaces it — see `STUDENT_TASKS.md`).
- `interim/cars.csv` — market-model cumulative abnormal returns for both events.
- `interim/firm_ai_intensity.csv` — SEC EDGAR 10-K AI-mention intensity (650 firms).
- `processed/analytical_panel.csv` — the final firm-level cross-section (3,056 firms) merging
  CARs, AIIE, buckets, and predetermined controls; every table is computed from this file.

## Reproduce
```bash
python code/00_pull_aioe.py         # parse the Felten-Raj-Seamans public appendix -> AIIE + buckets
python code/05_pull_crsp.py         # CRSP/Compustat raw pull (needs WRDS credentials)
python code/10_event_study.py       # market-model CARs for both events -> interim/cars.csv
python code/20_regressions.py       # build analytical_panel.csv; t1..t5 (long-short, cross-section, sign, robustness)
python code/25_edgar_ai_intensity.py# SEC EDGAR 10-K AI-intensity + firm-level validation (network; not re-run if CSVs present)
python code/40_extensions.py        # heterogeneity, characteristic matching, randomization inference, power/MDE
python code/30_figures.py           # figures (binscatter, sign buckets, CAAR path, RI histogram)
python code/35_tables_tex.py        # render paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex       # compile the paper
```
Everything downstream of the WRDS pull and the EDGAR crawl (the panel, all tables, all figures,
the paper) is fully determined by the committed `code/`. The `output/tables/*.csv` in the repo are
the exact numbers behind every table and figure in the paper.

**Note:** `25_edgar_ai_intensity.py` crawls SEC EDGAR live and is network-nondeterministic; its
outputs (`interim/firm_ai_intensity.csv`, `output/tables/t6_edgar*.csv`) are already present and
are not re-crawled on a routine rebuild. This is not missing data — it is a fixed snapshot.

**Rule:** every number in the paper must trace to a CSV in `output/tables/`. No fabricated
numbers, ever.
