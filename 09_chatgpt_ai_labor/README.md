# Project 09: Did ChatGPT Reprice AI-Exposed Labor?

**Student:** Nam Bao Ngo
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE (data + analysis + 16-page PDF). Awaiting student manual tasks.

## Research question
Around ChatGPT (Nov 30, 2022) and GPT-4 (Mar 14, 2023), did high-AI-exposure firms earn
abnormal returns, and does the sign depend on whether AI **substitutes** for the firm's
core output vs **complements** its labor?

## Headline result
**Yes — and the sign flips.** Around ChatGPT, an equal-weighted portfolio long the most
and short the least AI-exposed industries earned **+1.3% over [0,+1] (t=3.96)** and
**+2.7% over [0,+10] (t=3.46)**. In the cross-section, a 1-SD higher AI Industry Exposure
(AIIE) → **+0.71pp** ten-day CAR (t=2.49, industry-clustered), rising to **+0.97pp**
(t=3.39) excluding financials; the pre-event placebo is a clean null. **But the sign
reverses with economic role:** AI *suppliers* (software, semiconductors, cloud) earned
**+0.6%**, ordinary AI *users* **-1.3%**, and *substitution* industries whose product IS
cognitive labor (staffing, education, publishing, legal, consulting) earned **-2.8%
(t=-2.3)**. Firm-level 10-K AI-mention intensity (650 EDGAR filings) correlates with AIIE
(ρ=0.25) and predicts the tight-window CAR (t=2.04). The market priced AI as a net cost
saving for most firms but a competitive threat where AI can produce the firm's output.
(See `paper/main.pdf`; every number traces to `output/tables/`.)

## Data
- **WRDS CRSP** daily returns + value-weighted index; **Compustat** controls (book equity,
  employees, CIK); 3,056 U.S. common stocks across 182 industries, two 2022–23 event windows.
- **Felten–Raj–Seamans (2021) AI Industry Exposure (AIIE)** by 4-digit NAICS (public data
  appendix), merged to firms — the industry AI-exposure proxy.
- **SEC EDGAR** 10-K filings — firm-level AI-mention intensity (650 firms, real text counts).

## Method / identification
- Market-model event study (est. window [-252,-46], shared `lib/event_study.py`) around
  ChatGPT and GPT-4; AIIE-quintile long-short; cross-sectional CAR regressions with
  **industry-clustered** SE; substitution-vs-complement bucket heterogeneity; placebo,
  drop-financials, HC1, and firm-level 10-K robustness. GPT-4 window is SVB-contaminated
  (flagged; effect survives dropping financials).

## Pipeline (run in order)
- `code/00_pull_aioe.py`  → download AIOE/AIIE, build industry exposure + sign buckets
- `code/05_pull_crsp.py`  → WRDS CRSP/Compustat raw pull
- `code/10_event_study.py`→ market-model CARs (both events)
- `code/20_regressions.py`→ panel, long-short, cross-section, sign channel, robustness → CSVs
- `code/25_edgar_ai_intensity.py` → SEC EDGAR 10-K AI-intensity + firm-level validation
- `code/30_figures.py`    → figures (binscatter, sign buckets, CAAR path)
- `code/35_tables_tex.py` → LaTeX tables from the CSVs
- `paper/` → `/tmp/tectonic main.tex` → `main.pdf`
- **Student work:** see `STUDENT_TASKS.md` (hand-verify event calendar; hand-code exposure)

## Folder layout (do not deviate — the audit depends on it)
- `data/raw/`        downloaded data, date-stamped, never hand-edited
- `data/interim/`    cleaned / filtered, not yet merged
- `data/processed/`  final analytical panel
- `code/`            numbered scripts (00_download, 10_clean, 20_merge, 30_analyze ...)
- `output/tables/`   regression output as CSV -> LaTeX
- `output/figures/`  PDF figures
- `logs/`            row-count + timestamp log for every data step
- `paper/`           LaTeX source (main.tex) + compiled PDF

**Rule:** every number in the paper must trace to a CSV in `output/tables/`.
No fabricated numbers, ever.
