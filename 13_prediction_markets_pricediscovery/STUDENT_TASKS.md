# Student manual tasks — Dildora Jo'rabekova (Project 13, Kalshi vs Polymarket)

> **Revised timeline (updated 2026-07-25): we start at Week 5.** The program is now in Week 5, so that is your starting line. **Every earlier-week task below (anything labeled Weeks 1–4) is folded into Week 5 — start those now, this week, in the order listed.** The Week 5–8 items keep their timing, and everything still lands by the symposium (Aug 12). Read any "Week 1" or "Weeks 3–4" label below as "begin now, in Week 5."
>
> **On authorship:** you are listed as a coauthor on the working paper, but that credit is *provisional and tentative for the ASSIP program at this stage* — it is confirmed when you complete your contribution below (verify the code and data, do your hand-coding, and help push the paper forward). Note too that in finance and economics, published author order is conventionally alphabetical; the student-first order on the draft is a program convention, not a ranking.


**The AI has built:** the full data pull from both public APIs, the aligned hourly panel,
the Hasbrouck / Gonzalo–Granger information-share pipeline, the lead–lag and Granger tests,
a resolving-news event study, four figures, and a complete paper draft. The current honest
finding is a **reversal of the "regulation breeds quality" prior**: on matched FOMC
contracts, **Polymarket leads price discovery** (information share ≈ 0.68, and 0.82 when
weighted by trading activity); the CFTC-regulated Kalshi is the follower.

**Your work is the hinge of this paper, not a footnote.** Every information-share number
above is only as trustworthy as the claim that the two contracts settle *identically*. The
AI matched contracts *mechanically* (same FOMC meeting, same outcome label). It cannot read
the fine print, it cannot tell a truly identical settlement rule from a subtly different
one, and it could only find four Fed meetings because Kalshi's API prunes old markets. Those
three gaps are exactly the jobs a careful human must do — and if you do them well, you
either put this reversal on solid ground or find the categories where it breaks.

## Task 1 (PIVOTAL) — Verify identical settlement, rule by rule (Weeks 1–3)
For each matched contract, open BOTH venues' resolution text and compare line by line:
- **Reference source & timestamp.** Kalshi resolves the FOMC decision to the published
  statement; confirm Polymarket resolves to the *same* statement and not to, e.g., a
  target-range midpoint, a different rounding, or a UMA oracle vote that could diverge.
- **Outcome bucketing.** Confirm "25 bps cut" means the same range on both venues, and that
  "50+ bps" / "hold" boundaries coincide. Flag any asymmetric bucket.
- **Edge cases.** Inter-meeting/emergency moves, no-decision, or a split statement.
- Save `data/interim/settlement_audit.csv` (meeting, outcome, kalshi_rule, poly_rule,
  identical? [Y/N/ambiguous], source_url, notes). **Keep only truly identical pairs;** the
  AI will re-run the information shares on your verified subset.

## Task 2 (PIVOTAL) — Hand-match a second event family (Weeks 3–5)
The Fed-only sample is small because Kalshi prunes history. Extend the design by
hand-matching contracts in **one more category** where both venues are liquid — candidates:
a government-shutdown deadline, a CPI/jobs print, a crypto price threshold (e.g., "BTC above
$X on date D"), or a specific election outcome.
- The hard part is settlement: crypto thresholds differ in *snapshot time* (Polymarket noon
  ET vs Kalshi's hourly index) and *price source* — those are **not** identical and must be
  excluded or flagged. Read every rule.
- Save `data/interim/matched_pairs_v2.csv` (venue tickers, resolution text, identical? Y/N).
  The AI will pull the series and re-estimate; you interpret whether Polymarket still leads.

## Task 3 — Liquidity vs information (Week 5)
Kalshi's lower information share partly reflects a **thinner tape** (stale hourly closes).
For 3–4 matched contracts, hand-tabulate each venue's trade frequency and typical bid–ask
from the order book, and judge how much of Kalshi's "following" is genuine informational
lag versus simply fewer trades. Write a one-page memo.

## Task 4 — Re-test with your verified data (Weeks 6–7)
With your identical-settlement subset (Task 1) and your second family (Task 2), the AI
re-runs the Hasbrouck / lead–lag / event-study pipeline. You decide: does the
Polymarket-leads result survive rule-verified matching and a new event category?

## Weeks 7–8 — Write & present
Write the **Data and Institutional Background** section (the settlement-rule comparison is
yours) and a memo on whether hand-verification changes the conclusion.

## Assigned reading (Weeks 1–2)
Hasbrouck (1995, JF) — information shares; Wolfers & Zitzewitz (2004, JEP) — prediction
markets; Putniņš (2013, JEF) — what price-discovery metrics actually measure.

## Ground rules
- **Never call two contracts "identical" unless the rules truly match.** "Ambiguous / not
  identical" is a valid and valuable answer — it *shrinks* the sample honestly.
- Log dated entries in `logs/student_log.md`. Save source URLs for every rule you read.
- The judgment calls (is this settlement *really* the same?) are the skill — flag hard cases.
