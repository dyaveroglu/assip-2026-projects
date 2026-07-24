# Data for Project 07 — BNPL Enters the Credit File

**The `data/` folder is intentionally not published.** The analysis is built from the public
CFPB Consumer Complaint Database, which is freely available but voluminous; we do not ship the
raw pull. This README documents every source so the pipeline can be reproduced by anyone.

## Sources
| File (local, not shipped) | Source | Key fields |
|---|---|---|
| `raw/cfpb_bnpl.csv` | CFPB Consumer Complaint Database, public API (no key) | complaint_id, date_received, product, sub_product, issue, sub_issue, company, state, company_response, timely, submitted_via |
| `processed/bnpl_clean.csv` | Cleaned pull: 5 pure-play BNPL firms, false positives dropped | firm, month, cr flag |
| `interim/panelA_affirm.csv` | Within-Affirm CR×month count panel | month, cr, n, post |
| `interim/panelB_crossfirm.csv` | Cross-firm firm×month panel (CR share) | firm, month, cr_share, treat, post |
| `interim/panel_crossfirm_crcount.csv` | Cross-firm firm×month CR count panel | firm, month, n |
| `interim/eventstudy_series.csv` | Affirm vs peer-average CR series (Figure 1) | month, Affirm, PeerAvg |

The public CFPB API endpoint is
`https://www.consumerfinance.gov/data-research/consumer-complaints/search/api/v1/`.
Complaints are pulled for the five pure-play BNPL lenders (Affirm, Klarna, Sezzle, Zip, Perpay)
over 2022-01 through 2026-06. The public pull carries **no consumer narratives**, which is why
the genuine-furnishing-error labeling is reserved for the student's hand-collection task.

## Not present locally (reserved for the student — see STUDENT_TASKS.md)
| File | What it is | Why not built here |
|---|---|---|
| `interim/furnishing_dates.csv` | Exact per-lender × per-bureau furnishing dates | Hand-collected (Task 1); enables a staggered DiD |
| `interim/cr_gold.csv` | Hand-labeled genuine-furnishing-error gold set | Requires reading narratives that the public API does not return (Task 2) |

Every extension in `code/20_extensions.py` uses **observable CFPB structure only** (firm,
product, CFPB-provided issue label, month) plus the single public Affirm~Apr-2025 reference
date. No fabricated dates or labels are used anywhere.

## Reproduce
```bash
python code/00_pull.py        # pulls raw/cfpb_bnpl.csv from the public CFPB API
python code/10_did.py         # cleaning + within/cross-firm DiD → output/tables/t1..t2
python code/15_analysis.py    # honest composition + per-firm + DiD → output/tables/t1..t3
python code/20_extensions.py  # sumstats, per-firm het, triple-diff, robustness, RI, power
python code/30_figures.py     # figures fig1, fig2
python code/35_tables_tex.py  # renders existing paper/tables/*.tex from the CSVs
cd paper && tectonic main.tex # compiles the paper
```
Everything downstream of the CFPB pull (all tables, all figures, the paper) is fully determined
by the committed `code/`. The `output/tables/*.csv` are the exact numbers behind every table and
figure in the paper.
