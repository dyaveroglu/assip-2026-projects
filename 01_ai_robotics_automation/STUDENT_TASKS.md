# Student manual tasks — Michael Philipov (Project 01, AI vs Robotics patents)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the full patent-to-firm panel (AIPD AI flags, CPC B25J robotics, KPSS
firm link, Compustat outcomes), the fixed-effects regressions, the event study, and a complete
paper. Headline: AI-patent stock goes with employment growth; robotics with firm value.

**Your work turns a correlation into a mechanism.** The paper currently treats "AI" and
"robotics" as machine-assigned labels and cannot tell a labor-*replacing* robot from a
labor-*augmenting* one. Only a human who reads the patent can. That distinction is the crux of
the automation debate — and it's yours.

## Task 1 — Validate the AI/robotics classifier (Weeks 1–2)
Pull a stratified sample of 150 patents the pipeline labeled (50 AI, 50 robotics B25J, 50
neither — the AI will give you `data/interim/patent_sample.csv` with links to Google Patents).
For each, read the abstract/claims and confirm: is it really AI? really robotics? Record
`is_ai_confirmed`, `is_robotics_confirmed`, notes. Report the classifier's precision.

## Task 2 (CRUX) — Hand-code robotics patents: replacing vs augmenting (Weeks 3–5)
For every firm-linked robotics (B25J) patent in a focused sample (~150), read it and code:
- `labor_role`: **replacing** (removes a human task — e.g., a pick-and-place arm doing what a
  worker did) vs **augmenting** (assists/extends a human — e.g., a surgical or collaborative
  robot) vs unclear.
- `application`: manufacturing / logistics / surgical / agricultural / service / other.
Save `data/interim/robotics_labor_coded.csv`. The AI will re-run the firm-outcome regressions
splitting robotics into replacing vs augmenting — this is the paper's sharpest test.

## Task 3 — Spot-check the firm links (Week 5)
For the 20 largest AI patenters and 20 largest robotics patenters, confirm the KPSS `permno`
maps to the right company (patent assignee name vs CRSP company name). Flag mismatches.

## Task 4 — Anecdote pairs (Week 6)
Find 5 clear "AI-hiring" firms and 5 "robot-replacing" firms in the data and write a paragraph
each from their 10-Ks on what the technology actually did to their workforce. These ground the
statistics in real cases.

## Weeks 7–8 — Write & present
Write the **Data** section and interpret the replacing-vs-augmenting split.

## Ground rules
- **Never invent a label.** "Unclear" is a valid, valuable code.
- Log dated entries in `logs/student_log.md`.
- The judgment calls (replacing vs augmenting) are the skill — flag hard cases for discussion.
