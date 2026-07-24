# Data for Project 01 — Cognitive vs Physical Automation (AI & Robotics Patents)

**The `data/` folder is intentionally not published.** The analysis uses (i) large USPTO/
PatentsView bulk files that are processed on the GMU Hopper HPC cluster and (ii) data licensed
from Wharton Research Data Services (WRDS), which may not be redistributed. This README documents
every source so the pipeline can be reproduced by anyone with access to the public patent files
and an appropriate WRDS subscription.

## Sources

| File (local / shared, not shipped) | Source | Key fields |
|---|---|---|
| `KPSS_2024.csv` (on Hopper) | Kogan-Papanikolaou-Seru-Stoffman patent--firm crosswalk | patent_num, permno, issue_date, xi_real (market value of patent) |
| `ai_model_predictions.csv` (on Hopper) | USPTO Artificial Intelligence Patent Dataset (AIPD) | doc_id, flag_patent, predict50_any_ai (+ component AI-type flags) |
| `g_cpc_current.tsv` (on Hopper) | PatentsView CPC classifications | patent_id, cpc_subclass (B25J = robotics), cpc_group |
| `compustat_annual.csv` (shared) | WRDS Compustat `comp.funda` + CRSP/Compustat Merged link | at, sale, ni, emp, xrd, ceq, csho, prcc_f, dltt, dlc, che, capx, sich, naicsh |
| `patent_firm_year.csv` (shared) | Built by `code/process_patents.py` on Hopper | permno, year, ai, rob, robbroad, med, n_patents, xi_sum |
| `patent_firm_first.csv` (shared) | Built by `code/process_patents.py` on Hopper | permno, first_ai_year, first_rob_year, first_robbroad_year |
| `patent_analytical_panel.csv` (shared) | Built by `code/05_panel.py` | final firm-year analytical panel (patent stocks + Compustat outcomes) |

Raw patent bulk files live on Hopper at `/scratch/lgao9/assip26_patents/`; the shared firm-year
panels and the Compustat pull live in `assip26/data/` and are read directly by the analysis code.

## Variable construction (summary)
- **AI patent**: USPTO AIPD `predict50_any_ai == 1` on a granted patent.
- **Robotics patent (B25J)**: any CPC subclass equals B25J (industrial robots / manipulators).
- **Robotics-broad**: B25J or CPC group in {G05D1 (autonomous-vehicle control), B62D57 (legged
  machines), Y10S901 (robotics cross-reference)}.
- **Patent stocks**: running cumulative counts of a firm's flagged grants; used as `ln(1+stock)`.
- **Outcomes**: `ln(emp)`, `ln(sale/emp)` (labor productivity), ROA `= ni/at`,
  Tobin's Q `= (at - ceq + csho*prcc_f)/at`. Size `= ln(at)`.

## Reproduce
```bash
python code/process_patents.py   # ON HOPPER: builds patent_firm_year / patent_firm_first from raw
python code/01_pull_compustat.py # pulls WRDS Compustat annual + CCM link (needs WRDS credentials)
python code/05_panel.py          # builds data/../patent_analytical_panel.csv
python code/10_analysis.py       # main two-way FE panel + event study -> output/tables/t1..t4
python code/15_extensions.py     # heterogeneity, alt-FE, randomization inference, power/MDE (t5..t8)
python code/20_figures.py        # event-study figure
python code/25_tables_tex.py     # renders the baseline paper/tables/*.tex from CSVs
cd paper && tectonic main.tex    # compiles the paper
```
Everything downstream of the patent build and the WRDS pull (the panel, all tables, all figures,
the paper) is fully determined by the committed `code/`. The `output/tables/*.csv` in the repo are
the exact numbers behind every table and figure in the paper.

## Ground rule
Every number in the paper traces to a CSV in `output/tables/`. No fabricated numbers, ever. The
student's reserved hand-coding (labor-replacing vs labor-augmenting robotics; classifier
validation) is **not** constructed anywhere in this pipeline — see `STUDENT_TASKS.md`.
