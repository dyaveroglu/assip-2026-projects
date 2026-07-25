# Student manual tasks — Rakshana Damodaran (Project 07, BNPL)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the CFPB data pull, the difference-in-differences, the figures, and a
complete paper draft. The current honest finding is a **reversal**: there is *no
furnishing-specific* spike in credit-reporting complaints — the whole BNPL sector surged.

**Your work is not a footnote here — it is the only path to a clean test.** The AI could not
identify a furnishing effect because it does not know each lender's *exact* furnishing date,
and because it cannot tell a genuine furnishing error from a billing dispute miscategorized
as "credit reporting." Both are jobs only a careful human can do. If you do them well, you
either confirm the null with a proper staggered design or rescue a real effect the pooled
test missed.

## Task 1 (PIVOTAL) — Hand-collect exact furnishing dates (Weeks 1–3)
For each BNPL lender × each bureau, find the *exact date* it began furnishing:
- Affirm → Experian; Affirm → TransUnion; Klarna → (which bureaus, when); Sezzle;
  Zip; Perpay; Afterpay/Block.
- Sources: company press releases, Experian/TransUnion/Equifax announcements, bank/fintech
  news (American Banker, PYMNTS), 10-K/10-Q risk factors, earnings-call transcripts.
- Save `data/interim/furnishing_dates.csv` (lender, bureau, date, source_url, confidence).
- **This creates the staggered treatment the paper needs.** The AI will re-run a proper
  staggered DiD using your dates.

## Task 2 (PIVOTAL) — Hand-label the credit-reporting complaint gold set (Weeks 3–5)
Pull a random sample of 300 credit-reporting complaint narratives (the AI will give you the
file `data/interim/cr_sample.csv`). For each, code:
- `is_furnishing_error` (0/1): is this genuinely about a wrong/duplicate/inaccurate BNPL
  tradeline being *reported*? (vs. a billing, refund, or fraud issue mislabeled "credit
  reporting")
- `error_type`: duplicate account / wrong late payment / account not mine / not updated / other.
Save `data/interim/cr_gold.csv`. This is the ground truth that (a) tells us whether the
credit-reporting complaints are actually furnishing-related and (b) validates the machine
classifier the AI will build.

## Task 3 — Validate the product flag (Week 5)
Check whether CFPB's "Credit reporting" product label actually matches the narrative content
for your 300 cases. Report the false-positive rate.

## Task 4 — Re-test with your data (Weeks 6–7)
With your furnishing dates (Task 1) and gold labels (Task 2), the AI re-runs: (i) a staggered
DiD using true treatment timing, (ii) the DiD restricted to *genuine furnishing-error*
complaints. You interpret whether the null survives.

## Weeks 7–8 — Write & present
Write the **Data and Institutional Background** section (furnishing timeline is yours), and a
memo on whether your hand-coding changes the conclusion.

## Ground rules
- **Never invent a date or a label.** "Not found / ambiguous" is a valid, valuable answer.
- Log dated entries in `logs/student_log.md`.
- The judgment calls (is this *really* a furnishing error?) are the skill — flag hard cases.
