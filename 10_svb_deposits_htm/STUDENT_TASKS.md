# Student manual tasks — Aaron Lu Zhang (Project 10, SVB)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the full data pipeline (WRDS pull, holding-company aggregation,
event study, cross-sectional regressions), all tables, the figure, and a complete paper
draft. The **core result is real**: uninsured-deposit exposure — not hidden securities
losses — explains which banks' stocks collapsed in the SVB window.

**Your job is the part the AI can't do reliably: verifying the entity linkages and the
hand-collected ground truth that make the result trustworthy.** These are genuine research
contributions — a reviewer's first attack on this paper is "your bank identifiers are
wrong," and *you* are the defense.

## Why your work matters
The paper links stock tickers (holding companies) to bank regulatory filings
(subsidiaries) with an automated WRDS crosswalk + a "lead bank" rule for uninsured
deposits. That automation is *good enough for a first pass but known to be wrong in
specific, correctable ways*. Fixing them is your contribution.

## Task 1 — Hand-verify the ticker → holding-company crosswalk (Weeks 1–2)
`data/interim/crosswalk.csv` has one row per bank with `ticker`, `name` (regulatory),
and `holder`. (The full WRDS panel `bank_reg_panel.csv` is not in this repo — it is WRDS-derived; pull it with your own GMU WRDS access if you need the balance-sheet columns.) For the **40 largest banks**:
- Confirm the regulatory `name` actually matches the ticker's company (use the FFIEC
  National Information Center, https://www.ffiec.gov/npw, and the bank's investor page).
- Flag any mismatch (wrong holding company, merged/renamed entity, wrong RSSD).
- Record corrections in `data/interim/crosswalk_verified.csv` (columns: ticker, name,
  correct_rssd, note). **Log every check in `logs/student_log.md`.**

## Task 2 — Correctly aggregate multi-bank holding companies (Weeks 3–4)
The paper uses the *lead* (largest) subsidiary bank's uninsured deposits. Some holding
companies own **several** banks. For the ~30 holding companies that have >1 bank
subsidiary (the AI will give you the list):
- Read each subsidiary's 2022Q4 Call Report (FFIEC bulk data or the NIC) and **sum RCON5597
  (uninsured deposits) across all bank subsidiaries** by hand.
- Save `data/interim/uninsured_aggregated.csv`. The AI will re-run the regression with your
  corrected numbers; you'll report whether the result strengthens or weakens.

## Task 3 — Independently transcribe the 20 biggest banks (Weeks 4–5)
Trust nothing. For the 20 largest banks, open the actual **2022 10-K** and hand-transcribe
total assets, total equity, HTM fair value vs amortized cost, and uninsured deposits.
Compare to `analytical_panel.csv`. Any discrepancy >5% is a finding — document it.

## Task 4 — Hand-build the SVB news timeline & confound flags (Weeks 5–6)
For each of the 165 banks, was there *bank-specific* news during March 8–13, 2023 (a
capital raise, a downgrade, a deposit-flight report)? Build `data/interim/news_flags.csv`
(permno, date, headline, source). Banks with idiosyncratic news are potential confounds;
the AI will re-run excluding them.

## Task 5 — Classify actual deposit runs (Weeks 6–7)
From Q1-2023 10-Qs and press coverage, hand-code which banks *actually* lost deposits
(0/1, and % if disclosed). This becomes a second outcome: does uninsured exposure predict
real outflows, not just stock reactions?

## Weeks 7–8 — Write & present
Write the paper's **Data section** (you know it best now) and a one-page memo on what your
verification changed. Present the before/after.

## Ground rules
- **Never invent a number.** If you can't find it, write "not found."
- Log dated entries in `logs/student_log.md`: what you did, how many items, judgment calls.
- Ask when a bank's structure is ambiguous — these judgment calls are the real skill.
