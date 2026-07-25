# Student manual tasks — Michael Yucheng Zhou (Project 02, AI in Medicine)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the medical-AI patent panel (AIPD × CPC A61, KPSS firm link, Compustat),
the sector breakdown, and the value regressions, plus a complete paper. Headline: medical-AI
patenting doubled; incumbents dominate; the market rewards it.

**Your work replaces a coarse label with real clinical meaning.** The paper calls a patent
"medical-AI" if it is AI-flagged *and* in the broad A61 class — but A61 covers everything from
bandages to MRI algorithms. Only a human who reads the patent can say what it actually does in
medicine. Your coding is what makes the "diffusion of AI into medicine" claim specific and real.

## Task 1 — Validate the medical-AI flag (Weeks 1–2)
Take a sample of 150 patents the pipeline labeled medical-AI (the AI will give you
`data/interim/medai_sample.csv` with Google Patents links). Read each and confirm it is
genuinely (a) AI/ML-based and (b) medical. Report the precision (what fraction are real
medical-AI vs. false positives like a generic sensor in A61).

## Task 2 (CRUX) — Hand-code clinical application (Weeks 3–5)
For ~200 confirmed medical-AI patents, code the clinical application:
- `application`: **diagnostic imaging** / **drug discovery** / **clinical prediction & monitoring**
  / **surgical robotics** / **genomics** / **other**.
- `modality`: which AI technique (computer vision, NLP, deep learning, other).
Save `data/interim/medai_application.csv`. The AI will re-run the analysis by application area —
does the market value diagnostic-imaging AI differently from drug-discovery AI?

## Task 3 — Verify incumbent vs entrant assignees (Week 5–6)
The paper splits firms by SIC into "health incumbent" vs "tech entrant." For the top 30 holders,
confirm the classification from the company's actual business (read their 10-K business
description). Some "tech" firms are really medical; some "health" firms are really diversified.
Save corrections.

## Task 4 — Case studies (Week 6)
Pick 3 incumbents and 3 entrants with big medical-AI portfolios; write a paragraph each on what
they're building (from patents + 10-K), grounding the statistics.

## Weeks 7–8 — Write & present
Write the **Data** section and interpret the by-application results.

## Ground rules
- **Never invent a label.** "Other/unclear" is valid.
- Log dated entries in `logs/student_log.md`; flag hard cases (a patent that is arguably both
  imaging and prediction) for discussion — those judgment calls are the skill.
