# Student manual tasks — Lasya Yellamagari (Project 08)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**Project:** *Is the LLM Reading the 10-K or Remembering the Stock?*
**Mentor:** Lei Gao (George Mason University) · ASSIP 2026

---

## What the AI has already built (the machine part)

The AI built the full, real pipeline end to end:

- pulled **220 real 10-K Item-1A (Risk Factors) sections** from the SEC EDGAR archive,
  split into a **pre-cutoff** window (filed 2019–2021) and a **post-cutoff** window
  (filed 2024), chosen so their 12-month return windows fall cleanly on either side of
  gpt-4o's **October-2023 knowledge cutoff**;
- linked each filing to CRSP and computed real **12-month buy-and-hold abnormal returns
  (BHAR)**;
- scored every filing **twice with gpt-4o** — once on the RAW text, once on an
  **automatically anonymized** version (firm name, ticker, years, and states redacted);
- ran the placebo regressions: does the LLM score keep its return-predictive power once
  identity is masked, and is any predictive power concentrated in the pre-cutoff window
  (the only place look-ahead is possible)?

**The result is real and is reported honestly in the paper** — including if it is a null.

## Why your job is the pivot of the whole paper

The entire contribution hinges on one thing being trustworthy: **that the "anonymized"
text is actually anonymous.** The AI's redactor is a *floor* — it removes the obvious
identifiers (name, ticker, dates, states). But a large language model can still recognize
a company from things the AI cannot reliably catch automatically:

- **brand and product names** ("the App Store", "F-150", "Model 3", "the Galaxy line"),
- **flagship facilities, subsidiaries, and executives** named in the risk factors,
- **paraphrased self-identifiers** ("the world's largest ride-hailing network"),
- **industry-plus-geography fingerprints** that uniquely pin down one firm.

If any of these leak through, the "anonymized" score is *not* really anonymized, and the
placebo is contaminated. **Closing that gap is a genuine research contribution, and it is
your job.** You are building the anonymization **gold standard** the paper's headline
depends on.

---

## Task 1 — Read the machine's redactions and learn the failure modes (Week 1)
- Open 15 filings side by side: `data/raw/rf/{id}.txt` (raw) vs
  `data/interim/anon/{id}.txt` (machine-anonymized). The map from `id` to company is in
  `data/interim/sample_final.csv`.
- For each, ask: *could I still tell which company this is?* Write down every clue the
  machine missed. Start `logs/student_log.md` with dated entries.

## Task 2 — Hand-build the anonymization gold standard for ~100 excerpts (Weeks 2–5)
This is the core deliverable. Your **100 filings are listed in `data/interim/gold_sample_100.csv`**
— a balanced draw of 50 pre-cutoff + 50 post-cutoff, selected from the full 220-filing pool in
`data/interim/anon/` (that folder holds the *entire* sample, 110 + 110 — not your 100; work only
from the `id`s in `gold_sample_100.csv`). Each row gives the `id`, `window`, company, and the paths
to the machine-anonymized text (`anon_path`) and the original (`raw_path`). For each of the 100:
- Start from the machine-anonymized text (`data/interim/anon/{id}.txt`) and **redact every remaining identity leak**:
  brand/product names, subsidiaries, named people, headquarters cities, unique
  self-descriptions. Replace with the same bracketed tokens the machine uses
  (`[COMPANY]`, `[PRODUCT]`, `[LOCATION]`, `[PERSON]`).
- **Re-verify**: after redacting, re-read and confirm you could *not* identify the firm.
  If you still can, keep redacting. Save `data/interim/gold_anon/{id}.txt` + a tally in
  `data/interim/gold_redactions.csv` (columns: id, machine_redactions, extra_by_hand,
  still_identifiable_yesno, note).
- **Never delete a risk itself** — only mask identity. If masking a product would delete a
  real risk ("dependence on [PRODUCT] for 60% of revenue" is a real risk; keep the
  sentence, mask only the name).

## Task 3 — Blind identification test (Week 5) — this quantifies the leakage
- Take 40 of your gold-standard excerpts. Give the *machine-anonymized* version and the
  *hand-anonymized* version to **two classmates** (blind). Ask each to name the company or
  say "cannot tell," for both versions.
- Record the identification rate for machine vs hand anonymization in
  `data/interim/blind_test.csv`. If humans can still ID the machine version but not yours,
  you have *measured* exactly how leaky the automated floor is — that number goes in the
  paper.

## Task 4 — Re-run and report the delta (Weeks 6–7)
- The AI re-scores your 100 gold-standard excerpts with gpt-4o and re-runs the placebo.
  You compare three columns side by side: **raw**, **machine-anon**, **hand-anon**.
- Write the one-paragraph verdict: *did tighter anonymization move the result?* Did the
  pre-cutoff return-predictability shrink further once brands/products were masked? That
  before/after is your finding.

## Weeks 7–8 — Write and present
- Write the paper's **Data & Anonymization** subsection (you know it best now) and a
  one-page memo: *what fraction of "anonymized" filings were still identifiable, and what
  did fixing it do to the result?*
- Present the raw → machine-anon → hand-anon ladder.

## Ground rules
- **Never invent a number.** If you cannot decide whether a filing is identifiable, mark
  it "uncertain," don't guess.
- Log dated entries in `logs/student_log.md`: how many excerpts, how many extra
  redactions, judgment calls.
- Ask when a firm is ambiguous — those judgment calls are the real skill of this project.
