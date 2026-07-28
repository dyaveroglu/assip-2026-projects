# ASSIP 2026 — Empirical Finance Research Group

Fifteen student–faculty working papers from the 2026 [Aspiring Scientists Summer Internship
Program](https://www.gmu.edu/) empirical-finance group at the Costello College of Business,
George Mason University. Each project pairs a high-school research intern with a real,
reproducible empirical-finance study; the mentor (Lei Gao) is a coauthor on every paper.

Course site: https://edwardlg.github.io/assip-2026-empirical-finance/

## Projects
| # | Folder | Paper |
|---|--------|-------|
| 01 | `01_ai_robotics_automation` | Cognitive vs Physical Automation: AI vs robotics patents and firm outcomes |
| 02 | `02_ai_in_medicine` | AI Moves into Medicine |
| 03 | `03_clawbacks_ceo_risk` | Did Mandatory Clawbacks Curb CEO Risk-Taking? (SEC Rule 10D-1) |
| 04 | `04_anomaly_publication_decay` | Do Anomalies Die When Published? |
| 05 | `05_tariff_import_exposure` | Import Exposure & the April-2025 Tariff Shock |
| 06 | `06_disaster_housing_beliefs` | Disaster, Housing & Climate Beliefs |
| 07 | `07_bnpl_credit_file` | BNPL Enters the Credit File |
| 08 | `08_llm_10k_lookahead` | Is the LLM Reading the 10-K or Remembering the Stock? |
| 09 | `09_chatgpt_ai_labor` | Did ChatGPT Reprice AI-Exposed Labor? |
| 10 | `10_svb_deposits_htm` | What Cracked a Bank (SVB): Uninsured Deposits vs HTM Losses |
| 11 | `11_chips_awards` | CHIPS Act Award Announcements |
| 12 | `12_halfcent_tick` | The 2025 Half-Cent Tick & Spreads |
| 13 | `13_prediction_markets_pricediscovery` | Kalshi vs Polymarket: Who Leads Price Discovery? |
| 14 | `14_warn_layoff_motive` | What Layoff Does the Market Punish? |
| 15 | `15_cohort_shock_atlas` | Cohort Shock Atlas (co-authored by the full cohort) |

## Repository layout (per project)
```
NN_project/
  code/            analysis pipeline (pull -> build panel -> estimate -> render tables/figures)
  paper/           main.tex, main.pdf, tables/*.tex (rendered from output/)
  output/          tables/*.csv (aggregated result tables) and figures/*.pdf
  README.md        project overview and headline result
  STUDENT_TASKS.md the intern's reserved hand-collection contribution
  data/README.md   data sources (the data itself is NOT in this repo — see below)
```

## Data policy (please read)
Two kinds of data feed these projects:

- **Public-source data is included** in each project's `data/` folder — e.g. PatentsView,
  FEMA/NRI, Zillow ZHVI, CFPB complaints, state WARN notices, Kalshi/Polymarket, BEA, EDGAR
  filings/10-Ks, Open-Source Asset Pricing, and FDIC call reports. These carry no redistribution
  restriction.
- **WRDS-licensed data is NOT included** — Compustat, CRSP, Execucomp, and CCM links (and any
  firm-level panel derived from them) are licensed from Wharton Research Data Services and **may
  not be redistributed**, so they are excluded from this repository. Reproduce them by pulling
  from WRDS with your **own institutional credentials** using each project's `code/00_*.py`
  pull script; `data/README.md` documents every source. Everything downstream of the pull (the
  analytical panels, all tables, all figures, each paper) is fully determined by the committed
  `code/`, and `output/tables/*.csv` are the exact aggregated numbers behind the papers.

## Reproducibility
Each project reproduces with:
```bash
python code/00_*.py         # pull (needs WRDS credentials for licensed projects)
python code/05_*.py ...     # build the analytical panel
python code/1*_*.py         # estimate; writes output/tables/*.csv
python code/*_tables_tex.py # render paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex
```

## Authorship & honesty
Papers are student-first, mentor-coauthored. Several report **honest nulls**; where they do, the
papers say so plainly and quantify what the design could and could not detect (power / minimum
detectable effects). Nothing here is a claim of a top-journal *finding* — these are
submission-*structured* working papers built to a high methodological standard.
