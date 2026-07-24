# Data for Project 06 — Disaster Housing & Beliefs

**The `data/` folder is intentionally not published.** All inputs are public and free, but the
raw files (especially the full-panel Zillow ZHVI download) are large and are re-pulled rather
than shipped. This README documents every source so the pipeline can be reproduced by anyone.

## Sources (all public, no subscription or API key required)
| File (local, not shipped) | Source | Key fields |
|---|---|---|
| `raw/zhvi_county.csv` | Zillow Research, ZHVI all-homes county, smoothed & seasonally adjusted (`County_zhvi_uc_sfrcondo_tier_0.33_0.67_sm_sa_month.csv`) | monthly county home-value index, 2000–2026 |
| `raw/fema_declarations.csv` | OpenFEMA `DisasterDeclarationsSummaries` (v2 API) for DR-4673/4677 (Ian) and DR-4827/4828/4829/4830/4831/4832 (Helene) | `fipsStateCode`, `fipsCountyCode`, `ihProgramDeclared`, `designatedArea` |
| `raw/ycom_county.csv` | Yale Program on Climate Change Communication, Climate Opinion Maps (YCOM 5.0), county level | `worried`, `happening`, `personal`, `harmUS` (estimated % of adults) |
| `raw/county_vote2020.csv` | County-level 2020 U.S. presidential returns (MIT Election Data and Science Lab) | `per_gop` (Republican two-party vote share) |
| `raw/nri_county.csv` | FEMA National Risk Index (NRI), county table (ArcGIS/CSV release) | `HRCN_RISKS` (hurricane risk), `RISK_SCORE` (overall), `CFLD_RISKS` (coastal flood) |

Public inputs are redistributable; they are omitted only for size and to keep the repo lean.

## Reproduce
```bash
python code/00_pull.py         # downloads the 5 raw sources above to data/raw/
python code/10_build.py        # stacked balanced [-24,+20] panel -> data/processed/panel.csv
python code/20_did.py          # DiD, belief moderation, event study, pre-trends -> output/tables/t1..t6
python code/40_extensions.py   # heterogeneity, matching, randomization inference, power -> t7..t10
python code/30_figures.py      # fig1..fig3 (event study, belief split, raw index)
python code/35_tables_tex.py   # renders paper/tables/*.tex from the baseline CSVs
cd paper && tectonic main.tex  # compiles the paper
```
`40_extensions.py` renders its own four `paper/tables/tab_{hetero,matched,ri,power}.tex` and
`output/figures/fig4_randinf.pdf`. Everything downstream of `00_pull.py` is fully determined by
the committed `code/`; the `output/tables/*.csv` in the repo are the exact numbers behind every
table and figure in the paper.

## What is NOT in here (reserved for the student)
The graded landfall geography — exact NOAA landfall track, hurricane-force wind swath, and
storm-surge footprint, and the county-by-county validation/correction of the coarse FEMA IHP
treatment flag — is the student's hand-collected contribution (`STUDENT_TASKS.md`, Tasks 1–2).
It is deliberately **not** constructed here. Every extension in `40_extensions.py` uses only
observable, pre-existing county data (pre-storm home-value level and momentum, FEMA National
Risk Index scores, the existing IHP flag) and design-based inference.
