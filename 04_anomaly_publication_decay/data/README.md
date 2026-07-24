# Data sources — Project 04: Do Anomalies Die When They Are Published?

This folder is **not published** with the paper; this README documents every input so the
analysis is reproducible from the public source. **No number in the paper is hand-entered or
simulated** — every table/figure value is produced by `code/` from the files below and written
to `output/tables/*.csv`, then rendered to `paper/tables/*.tex`.

## Raw inputs (`data/raw/`, downloaded by `code/00_download.py`)

All data are from the **Open Source Asset Pricing (OSAP)** project
(Chen and Zimmermann, 2022, *Critical Finance Review* 11, 207–264), a public, freely
downloadable cross-sectional equity-anomaly library.

| File | Source | Contents |
|------|--------|----------|
| `PredictorLSretWide.csv` | OSAP public release | Monthly long-short (decile or sorted) portfolio returns, in percent, one column per predictor. Wide: `date` × 212 predictors. Signed so the in-sample mean is positive. |
| `SignalDoc.csv` | OSAP public release | Predictor metadata: `Acronym`, `Authors`, `Journal`, `Year` (publication), `SampleStartYear`, `SampleEndYear`, `Cat.Economic` (mechanism category), `Cat.Signal` (Predictor vs. placebo), reported in-sample `Return` and `T-Stat`. |

Both are public and contain **no proprietary or licensed data** (no CRSP/Compustat/WRDS
extract is redistributed here). Downloaded date-stamped; never hand-edited.

## Derived files

- `data/interim/anomaly_meta.csv` — one row per predictor (212 rows): publication year,
  sample-end/start year, journal, economic category, reported in-sample return and t-stat, and
  the transparent **risk-vs-mispricing category proxy** (`risk_framed`, `risk_framed_narrow`).
  Built by `code/10_build_panel.py`.
- `data/processed/anomaly_panel.csv` — the analytical **anomaly-month panel** (173,302 rows):
  long-short return, publication regime (in-sample / post-sample / post-publication), the nested
  McLean–Pontiff `oos`/`pub` dummies, event-time, and integer ids for clustering. Built by
  `code/10_build_panel.py`.

## Pipeline

```
code/00_download.py    → data/raw/            (OSAP pull)
code/10_build_panel.py → data/interim, processed
code/20_regressions.py → output/tables/t1–t6  (regime means, panel, hetero, robustness)
code/30_figures.py     → output/figures/fig1,fig2
code/35_tables_tex.py  → paper/tables/*.tex    (base tables)
code/40_extensions.py  → output/tables/t7–t10 + fig3 + paper/tables/*.tex  (extensions)
```

## Reserved for the student (do NOT construct from these files)

Per `STUDENT_TASKS.md`, two hand-collected variables are deliberately **not** built by the
code and are reserved for the student's manual work:
1. **Exact monthly publication / sample-end timing** (`data/interim/hand_timing.csv`) — the code
   uses only the *annual* `Year` and `SampleEndYear`.
2. **Hand-read risk-vs-mispricing framing** (`data/interim/hand_framing.csv`) — the authors'
   *stated economic interpretation*, which replaces the coarse category proxy.

All extension analyses (`code/40_extensions.py`) use **observable OSAP metadata only**
(in-sample strength, journal, publication era, sample-end/publication year) and never these
reserved variables.
