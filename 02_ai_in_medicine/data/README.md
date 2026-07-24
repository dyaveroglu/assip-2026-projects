# Data for Project 02 — The Diffusion of AI into Medicine

**The `data/` folder is intentionally not published.** The analysis combines public patent data
with data licensed from Wharton Research Data Services (WRDS), which may not be redistributed.
This README documents every source so the pipeline can be reproduced by anyone with the
appropriate access. The analytical panel is the shared innovation panel built for the ASSIP 2026
patent projects and lives at `assip26/data/patent_analytical_panel.csv` (read-only).

## Sources
| File (shared / not shipped) | Source | Key fields |
|---|---|---|
| `patent_analytical_panel.csv` | Firm-year panel (built from the sources below) | permno, year, sich, at, tobinq, mktcap, size, rd_at, ai/med/aimed stocks & logs |
| `patent_firm_year.csv` | AIPD × PatentsView aggregated to firm-year | ai, rob, med, aimed, visai patent counts |
| `patent_firm_first.csv` | First-adoption years per firm | first_ai_year, first_med_year, first_aimed_year |
| USPTO AIPD | USPTO Artificial Intelligence Patent Dataset (public) | AI component-technology flags per patent (through grant year 2023) |
| PatentsView | patentsview.org (public) | CPC classifications; subclass A61 = medical/veterinary |
| KPSS crosswalk | Kogan, Papanikolaou, Seru, Stoffman (2017), public replication files | patent ↔ permno link + market-based patent value (xi) |
| Compustat annual | WRDS `comp.funda` (licensed) | at, sale, ni, xrd, capx, emp → size, Q, R&D/assets |

A patent is **medical-AI** (`aimed`) if AIPD flags it AI **and** it carries a CPC A61 subclass.
Stocks are cumulative firm-matched patent counts; `ln_*` variables are `ln(1 + stock)`.

Public inputs (redistributable): USPTO AIPD, PatentsView, and the KPSS replication crosswalk.
Licensed inputs (not shipped): Compustat fundamentals via WRDS.

## Reproduce
```bash
python code/10_analysis.py     # trend, sector ownership, value regressions -> output/tables/t1..t3
python code/20_figures.py      # fig1 medical-AI trend
python code/25_tables_tex.py   # renders tab_sector.tex, tab_value.tex from the CSVs
python code/30_extensions.py   # sumstats, heterogeneity, alt-ID/robustness, randomization
                               #   inference (+fig2), power -> t4..t8 and paper/tables/*.tex
cd paper && tectonic main.tex  # compiles the paper
```
Everything downstream of the shared panel is fully determined by the committed `code/`. The
`output/tables/*.csv` are the exact numbers behind every table and figure in the paper; no number
in the paper is entered by hand.

## Reserved for the student (not built here)
Per `STUDENT_TASKS.md`, the hand-coded **clinical-application** and **AI-modality** labels
(diagnostic imaging / drug discovery / clinical prediction / surgical robotics / genomics; and
computer vision / NLP / deep learning) are the student's contribution and are deliberately **not**
constructed or used in any script. All extensions here use observable firm characteristics only.
