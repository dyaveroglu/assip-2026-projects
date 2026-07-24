# Project 08: Is the LLM Reading the 10-K or Remembering the Stock?

**Student:** Lasya Yellamagari
**Mentor:** Lei Gao (George Mason University)
**Program:** ASSIP 2026
**Status:** DRAFT COMPLETE — scaled to N=209 on Hopper Ollama (llama4:scout). Diagnosed null.

**Scaled result (2026-07-08):** The look-ahead placebo now runs on the full **209-filing**
sample (llama4:scout, run locally on a Hopper A100 — no rate limit). Result is a **diagnosed
null**: neither the raw nor the anonymized risk score reliably predicts 12-month returns, and
the raw-vs-anon gap does not differ across the training cutoff. The N=10 gpt-4o pilot's hint
does not survive scaling. Caveat: llama4:scout's cutoff (~mid-2024) only approximately post-dates
the 2024 filings, so the post-window is a weaker control than gpt-4o's clean Oct-2023 cutoff —
read as a memorization test. Pipeline: `code/score_ollama.py` (Hopper) → `20_panel`→`45_fill_paper`.

## Research question
Does an LLM risk-factor score lose its return-predictive power once firm
identity (name/ticker/dates) is masked, and is any predictive power concentrated
in filings the model could have *memorized* (pre-training-cutoff) — i.e. is the
apparent forecast really **look-ahead contamination**?

## Headline result
On the real (but small, rate-limited) scored sample of **N=10 filings (5 pre-, 5
post-cutoff)**, gpt-4o's raw and anonymized risk scores are nearly identical
(ρ=0.98, mean absolute gap 3.0 pts on 0–100). The **directional** look-ahead
signature appears but is **not statistically significant**: the raw-text score
predicts pre-cutoff 12-month BHAR with slope **−0.75 (t=−0.74)** vs the
anonymized score's **+0.15 (t=0.28)**, while both post-cutoff slopes are ≈0
(−0.03, −0.06); the stacked triple interaction score×raw×post is **+0.92
(t=1.73)**, marginally consistent with contamination. **Honest reading:**
directionally suggestive of "remembering the stock," but underpowered — the
scored sample is tiny because the shared GMU LLM gateway was saturated. The
pipeline is complete and every number is real; scaling the sample (and the
hand-built anonymization gold standard) is the intended next step.
See `paper/main.pdf`; all numbers trace to `output/tables/` via `code/45_fill_paper.py`.

## Design (placebo)
- **Model:** gpt-4o (gpt-4o-2024-11-20), knowledge cutoff **October 2023**, via the
  GMU PatriotAI gateway. Each filing scored **twice** with an identical prompt:
  once on **raw** Item-1A text, once on an **anonymized** copy (name, ticker,
  years, states redacted).
- **Two windows around the cutoff:** **pre-cutoff** = filed 2019–2021 (12-month
  outcome realized before Oct-2023 → look-ahead *possible*); **post-cutoff** =
  filed 2024 (text and outcome after cutoff → look-ahead *impossible*).
- **Outcome:** 12-month market-adjusted buy-and-hold abnormal return (BHAR),
  built from CRSP monthly returns and the Fama–French market factor.
- **Contamination signature:** raw beats anonymized at predicting returns *only*
  pre-cutoff, and the raw-vs-anon gap vanishes post-cutoff
  (triple interaction `score × raw × post`).

## Data
- **10-K risk factors:** SEC EDGAR archive on Hopper
  (`/groups/LGAO/edgar_archive`, 96k 10-Ks with pre-extracted Item 1A);
  220 filings sampled (110 pre, 110 post), all with a valid 12-month BHAR.
- **Returns / links:** WRDS `crsp.msf_v2` (monthly, through 2025-12),
  `ff.factors_monthly`, `comp.company` + `crsp.ccmxpf_lnkhist` (CIK→permno).
- **LLM scores:** gpt-4o via PatriotAI (`SKILL 4`).

## Pipeline (`code/`)
- `00_link_sample.py`  — filter EDGAR INDEX, define pre/post windows, CIK→permno link, sample.
- `05_returns.py`      — CRSP monthly + FF market → forward BHAR (3/6/12m); finalize sample.
- `07_fetch_anon.py`   — fetch Item-1A text from Hopper; automated anonymizer + redaction stats.
- `10_llm_score.py`    — gpt-4o raw & anon scoring (resumable, backoff under the shared TPM cap).
- `20_panel.py`        — merge scores + returns → `data/processed/panel.csv`.
- `30_regressions.py`  — placebo regressions → `output/tables/t1..t6*.csv`.
- `35_tables_tex.py`   — booktabs LaTeX tables from the CSVs.
- `40_figures.py`      — figures (score agreement, predictive-slope bars, pre-cutoff scatter).
- `45_fill_paper.py`   — writes abstract/results/robustness/conclusion prose FROM the CSVs.

## Student's pivotal manual task
Hand-build the **anonymization gold standard** — redact and re-verify every firm
name/ticker/brand/date in ~100 excerpts, then measure how much the automated
redactor leaked and whether tighter anonymization moves the result. See
`STUDENT_TASKS.md`.

## Caveats
- The scored LLM sample is **small**: the shared GMU LLM gateway is rate-limited
  ("token limit already exceeded"), so scoring is throttled. The **full pipeline**
  is built and every number is real; the design (not the power) is the
  contribution, and the hand-built gold standard is the intended scale-up.
- The automated anonymizer removes explicit identifiers only; firms may remain
  identifiable from business text — which biases the placebo *toward* a null.

**Rule:** every number in the paper traces to a CSV in `output/tables/`. No
fabricated numbers, ever.
