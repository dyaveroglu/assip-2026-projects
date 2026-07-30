# Student manual tasks — Nam Bao Ngo (Project 09, ChatGPT / AI-exposed labor)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the full data pipeline (CRSP/Compustat pull, the
Felten--Raj--Seamans AI-exposure merge, the two-event market-model event study, the
cross-sectional regressions, the SEC-EDGAR 10-K AI-intensity crawl, all tables and
figures, and a complete paper draft). **The core result is real:** around ChatGPT,
higher-AI-exposure firms earned positive abnormal returns (a top-minus-bottom quintile
long--short of **+1.3% over [0,+1], t=3.96** and **+2.7% over [0,+10], t=3.46**), and
the **sign reverses** for firms whose product *is* cognitive labor (staffing, education,
publishing, legal, consulting: **-2.8%, t=-2.3**).

**Your job is the part the AI cannot do reliably — and it is what makes or breaks the
paper's identification.** Two things: (1) nail down *exactly when* each AI release hit
the market relative to the close, and (2) hand-code *true* firm-level AI task exposure so
the substitution-vs-complement split stops being a coarse NAICS proxy. A referee's first
two attacks on this paper are "your event date is contaminated" and "your industry buckets
are wrong." *You* are the defense.

## Why your work matters
The whole design rests on two assumptions the machine cannot verify: that day 0 is the
*trading day the news was actually priceable*, and that a firm's NAICS code tells us
whether AI is a threat or a tailwind. Both are shaky. ChatGPT launched the same afternoon
as the November 30, 2022 Powell pivot; GPT-4 launched into the SVB banking crisis. And
CRSP's NAICS tags put Visa and Moody's in "business support services." Fixing these is a
genuine research contribution, not busywork.

## Task 1 — Hand-verify the AI event calendar (Weeks 1--2) — PIVOTAL
Build `data/interim/event_calendar_verified.csv` (columns: `event`, `announce_datetime_ET`,
`source_url`, `before_or_after_close`, `confounding_news_same_day`, `notes`).
- For **ChatGPT (Nov 30 2022)**, **GPT-4 (Mar 14 2023)**, and add **the ChatGPT API/
  GPT-3.5 (Mar 1 2023), Bing Chat (Feb 7 2023), and Google Bard (Feb 6 / Mar 21 2023)**
  as extra events: find the *exact* announcement timestamp (OpenAI blog, press wire, first
  Bloomberg/Reuters tape) and whether it was before or after the 4:00pm ET close. If after
  the close, day 0 should be the *next* trading day — check whether our code's day-0 choice
  (`code/10_event_study.py`) matches.
- For each event, list *every* major market-moving story that day (Powell's Brookings
  speech on Nov 30; the SVB/Signature/Credit Suisse timeline around GPT-4). This is the
  confound table that justifies why we lean on ChatGPT and drop financials.
- **Deliverable memo:** for which events is a clean one-day CAR even identifiable? Your
  answer decides which windows the final paper trusts. Log every source in
  `logs/student_log.md`.

## Task 2 — Hand-code true AI task exposure for 40--50 firms (Weeks 3--5) — PIVOTAL
The paper's sign channel uses a crude NAICS rule (`supplier` / `substitution` / `user`).
Replace it with hand judgment for the 40--50 largest firms in the high-exposure buckets. The firm list is `data/interim/firm_ai_intensity.csv` (ticker, naics4, and the `aiie` exposure score); the bucket for each industry is in `data/interim/naics_buckets.csv` (`bucket` column). Pick the highest-`aiie` firms to hand-code.
- Open each firm's 10-K "Business" and "Risk Factors" sections. Decide, on a 0--2 scale,
  **(a) substitution**: can generative AI directly produce what this firm *sells*?
  **(b) complementarity**: does the firm deploy AI to cut its own costs or sell AI tools?
- Record `data/interim/firm_exposure_handcoded.csv` (columns: `ticker`,
  `sub_score`, `comp_score`, `one_line_rationale`, `evidence_quote`). Flag every case
  where your judgment disagrees with the NAICS bucket (e.g., is an IT-services firm like
  EPAM a supplier or a substitution victim?). **The AI will re-run the sign regression
  with your codes and report whether the substitution effect strengthens.**

## Task 3 — Validate the 10-K AI-intensity measure (Weeks 5--6)
The automated EDGAR crawl (650 firms; 34.8% mention AI; correlation with AIIE only 0.25)
counts AI terms with a regex. Spot-check 30 filings by hand:
- Confirm the parsed document is the real 10-K body (not an exhibit index), and that AI
  mentions are substantive (a strategy discussion) vs boilerplate risk-factor language.
- Record `data/interim/edgar_spotcheck.csv` (ticker, accession, human_ai_mentions,
  regex_ai_mentions, agree?). The modest 0.25 correlation may be measurement error you can
  reduce — any systematic gap is a finding.

## Task 4 — Build a "pure-play" loser/winner case file (Weeks 6--7)
For 8--10 named firms the press singled out (e.g., Chegg, Pearson, Fiverr, Upwork on the
loser side; Nvidia, Microsoft, C3.ai on the winner side), assemble a one-paragraph
narrative + the firm's ChatGPT-window CAR from `data/processed/analytical_panel.csv`.
This becomes the paper's motivating anecdotes and a sanity check that the cross-section
lines up with what actually happened.

## Weeks 7--8 — Write & present
Write the paper's **Data section** and a one-page memo on how your hand-verified event
calendar and hand-coded exposure changed the results. Present the before/after.

## Ground rules
- **Never invent a number.** If you cannot pin down a timestamp or a classification, write
  "not found / ambiguous" and explain. Honest nulls are results.
- Log dated entries in `logs/student_log.md`: what you did, how many items, judgment calls.
- When a firm's AI exposure is genuinely two-sided (both threatened and benefiting), say so
  — that ambiguity is itself the paper's most interesting point.
