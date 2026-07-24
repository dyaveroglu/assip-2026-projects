# Project 12: Did the 2025 Half-Cent Tick and Access-Fee Cut Tighten Spreads?

**Student:** Kushal Borra
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 18-page PDF). Awaiting student manual tasks.

## Research question
For tick-constrained NMS stocks, did the SEC's \$0.005 minimum pricing increment and the
Rule 610 access-fee cut (compliance date **Nov 3, 2025**) reduce quoted/effective spreads
relative to wide-spread control stocks?

## Headline result (honest, measurement-limited null)
Using the **CRSP daily closing NBBO** proxy (WRDS TAQ intraday is not subscribed on this
account — only sample libraries exist) for **150 NMS stocks** (75 tick-constrained, 75 wide;
5,820 stock-days), the difference-in-differences estimate for the relative quoted spread is
**+0.73 bps (t = 4.2; +2.9 double-clustered)** — the *wrong sign* for a spread reduction,
driven entirely by wide-spread controls narrowing more than treated names. **We do not read
this as a treatment effect:** a placebo event inside the pre-period is large and significant
(**−0.77 bps, t = −5.5**) and pre-trends are non-parallel, so parallel-trends fails. The
deeper reason is **penny-grid censoring**: **0.0%** of treated stock-days show a sub-penny
closing spread either before or after the reform, and the share pinned at exactly \$0.01
*rose* from 81% to 89%. Both groups' dollar spreads fell Oct→Nov (treated −10.7%, control
−22.6%, both p<0.001) — a market-wide move the daily design cannot separate from the reform.
**Conclusion: the daily proxy cannot answer this question; a TAQ intraday test is required.**
(See `paper/main.pdf`; every number traces to `output/tables/*.csv`.)

## Data
- **WRDS CRSP daily** (`crsp.dsf_v2`, CIZ format): daily closing consolidated NBBO
  (`dlybid`, `dlyask`), 2025. TAQ intraday NBBO **not available** on this account
  (`taqsamp`/`taqmsamp` sample libraries only cover 2008/2009/2021) — fallback used per brief.
- Quoted spread proxy = `ask − bid` (dollars) and `(ask − bid)/mid` (relative), the
  Chung–Zhang (2014) daily proxy. Effective-spread proxy = `2|close − mid|/mid` (caveated).

## Method / identification
- Stock × day DiD around Nov 3, 2025: treated = tick-constrained (Sept mean dollar spread
  ≤ \$0.015, the SEC TWAQS cutoff) vs control = wide-spread (≥ \$0.02). Stock + day FE,
  price/volume controls, SE clustered by stock (and stock+day). Event-study, placebo, and
  within-group descriptives. Treatment assigned from a **separated** Sept screening window.

## Pipeline (run in order)
- `code/00_pull.py`   → WRDS pull: screening universe, sample selection, daily panel → `data/raw/`
- `code/10_build.py`  → build analytical panel (spreads, periods, winsorize) → `data/processed/`
- `code/20_did.py`    → DiD, event-study, placebo, mechanism tables → `output/tables/*.csv`
- `code/30_figures.py`→ event-time / event-study / censoring figures → `output/figures/*.pdf`
- `code/35_tables_tex.py` → booktabs LaTeX tables from the CSVs → `paper/tables/*.tex`
- `paper/` → `/tmp/tectonic main.tex` → `main.pdf` (18 pp.)
- **Student work:** see `STUDENT_TASKS.md`

## Folder layout (do not deviate — the audit depends on it)
- `data/raw/` downloaded data · `data/interim/` · `data/processed/` final panel
- `code/` numbered scripts · `output/tables/` CSV→LaTeX · `output/figures/` PDF · `logs/`
- `paper/` LaTeX + compiled PDF

**Rule:** every number in the paper traces to a CSV in `output/tables/`. No fabricated numbers, ever.
