# Data for Project 11 — CHIPS Act Award Announcements & Awardee Stock Returns

**The `data/` folder is intentionally not published.** The analysis uses data licensed from
Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with the appropriate WRDS subscription.

## Sources
| File (local, not shipped) | Library / source | Key fields |
|---|---|---|
| `raw/chips_awards_handcollected.csv` | **Hand-collected** from U.S.\ Dept.\ of Commerce (`commerce.gov/news/press-releases`) and NIST CHIPS Program Office (`nist.gov/chips`) press releases | company, ticker, exchange, announce\_date (PMT), award\_usd\_m, award\_type (grant / grant+loan), us\_listed, adr, source |
| `raw/awards_with_permno.csv` | Above + CRSP `crsp.stocknames` | adds permno, shrcd, siccd |
| `raw/crsp_daily.csv` | CRSP `crsp.dsf` (daily stock file) | permno, date, ret, prc, shrout, vol |
| `raw/crsp_market.csv` | CRSP `crsp.dsi` (daily market index) | date, vwretd (value-weighted market return) |

Public input (redistributable): `raw/chips_awards_handcollected.csv` is compiled from public
government press releases and carries a `source` column pointing to the originating release for
every award. The CRSP files are WRDS-licensed and are **not** shipped.

## Coverage
- **Awards:** 17 hand-collected CHIPS first-announcement (Preliminary Memorandum of Terms) dates
  and proposed direct-funding amounts for U.S.-listed recipients, Jan-2024 .. Jan-2025. Two
  (Analog Devices ADI, MACOM MTSI, announced Jan-2025) fall past the CRSP daily cutoff and are
  held out → **15 events analyzed**.
- **Returns:** CRSP daily returns, price, and shares outstanding for the 15 awardee permnos, plus
  the CRSP value-weighted index, 2022-06-01 .. 2024-12-31 (covers the earliest event's
  `[-252,-46]` estimation window and the latest 2024 event window).

## Student hand-validation (reserved; not used in the current analysis)
Per `STUDENT_TASKS.md`, the following are the student's manual contributions and are **not**
constructed or used by the code in this repo: primary-source verification of each announcement
date, entity→listed-parent ticker resolution, a firm-level news/confound timeline beyond the
single pre-existing Amkor earnings flag, the second (finalized "funding agreement") event dates,
and the required private co-investment (cost-share) dollars behind each award.

## Reproduce
```bash
python code/00_pull.py         # pulls CRSP raw files from WRDS (needs credentials); writes raw/
python code/10_event_study.py  # per-event market-model CARs → data/interim/cars.csv
python code/20_regressions.py  # event-time + cross-sectional tables → output/tables/t1..t5
python code/30_figures.py      # fig1 (scatter), fig2 (CAR by window)
python code/35_tables_tex.py   # renders base paper/tables/*.tex from the CSVs
python code/40_extensions.py   # heterogeneity, alt models/tests, randomization inference, power
cd paper && tectonic main.tex  # compiles the paper
```
Everything downstream of the WRDS pull (CARs, all tables, all figures, the paper) is fully
determined by the committed `code/`. The `output/tables/*.csv` in the repo are the exact numbers
behind every figure and table in the paper. No numbers are fabricated; where the result is a
null, it is reported as such.
