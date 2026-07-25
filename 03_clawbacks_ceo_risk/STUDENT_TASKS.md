# Student manual tasks — Aiden Shanyu Chen (Project 03, Clawbacks)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the WRDS data pipeline (Compustat, CRSP, Execucomp, S&P index
membership), the difference-in-differences, the event-study/placebo diagnostics, the figures,
and a complete 14-page paper draft. The current honest finding is a **null**: the mandatory
clawback rule (SEC 10D-1) did **not** measurably change CEO investment/M&A risk-taking, and the
one "significant" result (return volatility) is a **size × COVID artifact** — it fails
parallel-trends and shows up identically in placebo splits that contain no clawback content.

**Your work is not a footnote here — it is the only path to a real test of the mechanism.**
The AI could not detect a clawback effect for one specific, fixable reason: it does not know
which firms *actually* had a voluntary clawback before 2023, and it does not know *how strong*
each firm's mandated 10D-1 policy is. It had to **proxy** treatment with firm size (small =
"forced adopter"). That proxy is blind to the exact dimension theory says should drive
behavior — **provision strength**. Hand-coding that strength is your job, and it is what turns a
proxy-based null into a sharp dose-response test.

## Why the proxy is not enough (read this first)
Rule 10D-1 sets a floor, not a uniform policy. Firms wrote materially different clawback
policies: some recover pay **only** after a formal restatement; others extend to broader
**misconduct**. Some use the statutory **three-year look-back**; others go longer. Some interact
the clawback with **severance / change-in-control multiples**; others do not. Two firms both
"treated" by the mandate can face very different incentives. A size proxy assigns them the same
treatment. If stronger policies changed behavior and weaker ones did not, the pooled test
averages the effect toward zero — exactly the null we report. Only hand-reading the actual
exhibits can separate strong from weak clawbacks.

## Task 1 (PIVOTAL) — Hand-code 10D-1 provision strength from EDGAR (Weeks 2–5)
For a defined sample of firms (the AI will hand you `data/interim/claw_sample.csv` with CIK,
ticker, and EDGAR links to each firm's clawback policy exhibit — usually **Exhibit 97** to the
10-K, or the policy filed on Form 8-K), read the actual policy text and code:
- `trigger` — restatement-only (0) vs. also covers misconduct/detrimental conduct (1).
- `lookback_months` — the recovery look-back window (statutory floor is 36).
- `discretion` — board has discretion not to claw back (1) vs. mandatory (0).
- `covers_former` — applies to former executive officers (0/1).
- `severance_link` — does the policy reach severance / change-in-control payments? (0/1) and, if
  disclosed, the severance multiple.
- `adopted_date` — the date the compliant policy was adopted.
Save `data/interim/claw_strength.csv` (one row per firm) with a `source_url` and a
`confidence` (high/medium/low) for every field. Build a simple **strength index** (sum of the
0/1 "stronger" indicators). This is the treatment variable the AI cannot construct.

## Task 2 (PIVOTAL) — Hand-verify ex-ante voluntary clawback status (Weeks 3–6)
The paper's control group assumes large (S&P 500) firms already had voluntary clawbacks and
small (S&P 600) firms did not. **Test that assumption directly** for a random sample of ~150
firms (75 large, 75 small): read the **2021 or 2022 proxy statement (DEF 14A)** and record
whether the firm disclosed a voluntary clawback policy *before* 10D-1 (`had_voluntary` 0/1) and
its scope. Save `data/interim/exante_clawback.csv`. This tells us how good the size proxy is —
if many small firms already had voluntary policies (or many large firms did not), the treatment
is mismeasured and the AI will re-run with your corrected assignment.

## Task 3 — Re-run the test with real treatment (Weeks 6–7)
With your strength index (Task 1) and corrected ex-ante status (Task 2), the AI re-estimates:
(i) DiD using **true** ex-ante-no-clawback firms as treated (not the size proxy); (ii) a
**dose-response** DiD interacting Post with your strength index — the key test of whether
*stronger* mandated clawbacks reduced risk-taking. You interpret whether the null survives.

## Task 4 — Read the assigned papers and write the background (Weeks 1, 7–8)
Read: Babenko, Bennett, Bizjak, Coles & Sandvik (2023, RCFS); Liu, Gan & Karim (2020, RQFA);
Chen, Greene & Owers (2015, RCFS); the SEC's 10D-1 adopting release (33-11126). Write the
**Institutional Background and Hypotheses** section (the 10D-1 timeline and provision-strength
taxonomy are yours), and a memo on whether your hand-coding overturns or confirms the null.

## Week-by-week
- **Weeks 1–2:** orientation; read the 4 papers; learn EDGAR full-text search; pilot-code 10 firms.
- **Weeks 3–4:** core hand-coding of provision strength (Task 1) + ex-ante status (Task 2).
- **Weeks 5–6:** finish coding; validation, second-pass on low-confidence cases.
- **Weeks 6–7:** AI re-runs the dose-response DiD with your data; you interpret.
- **Weeks 7–8:** write Background section; present.

## Ground rules
- **Never invent a value or a label.** "Ambiguous / not found" is a valid, valuable answer —
  flag it, don't guess.
- Log dated entries in `logs/student_log.md` (what you did, how many firms, judgment calls).
- The judgment calls (is this trigger "misconduct" or just "restatement"? does this reach
  severance?) are the skill — collect hard cases for the group to adjudicate.
- Every hand-coded value keeps a `source_url` so the coding is auditable and replicable.
