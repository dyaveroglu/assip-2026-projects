# Student manual tasks — Christopher Abhi Dadoo (Project 04, Anomaly Publication Decay)

**The AI has built:** the full data pipeline (download of the 212-predictor Open Source Asset
Pricing library + SignalDoc metadata), the in-sample / post-sample / post-publication regime
panel, the decay regressions with clustered standard errors, two figures, and a complete paper
draft.

**The current honest findings are:**
1. **H1 is confirmed and strong.** The average anomaly earns 0.61%/month in-sample, 0.42%
   post-sample, and 0.30% post-publication — a −51% within-anomaly decline (t = −7.6),
   replicating McLean–Pontiff (2016) on a larger, more recent sample.
2. **H2 is fragile.** Whether there is an *extra* drop *at publication* (beyond general
   out-of-sample decay) is significant with anomaly fixed effects (−0.13, t = −2.2) but
   vanishes once calendar-time fixed effects are added. The metadata cannot cleanly separate
   the publication event from the secular decline in anomaly profits.
3. **H3 is a NULL with the machine proxy.** The category-based risk-vs-mispricing split does
   NOT reliably separate the decay: the interaction is −0.03 (t = −0.4) under a broad risk
   definition and flips to +0.10 (t = 1.0) under a narrow one. The sign is not even stable.

**Your work is not a footnote — it is the only path to sharpening H2 and testing H3.** The AI
could not resolve them because (a) it only knows publication and sample-end at the *year* level,
and (b) a mechanism label ("valuation", "momentum") is NOT the same as the authors' *stated
economic interpretation* (risk vs mispricing). Both are jobs only a careful human reader can do.

---

## Task 1 (PIVOTAL) — Hand-record exact timing for ~60 flagship anomalies (Weeks 1–3)
The AI used SignalDoc's `Year` and `SampleEndYear` (annual). For the ~60 most-cited anomalies
(momentum, accruals, asset growth, B/M, profitability, net issuance, idiosyncratic vol,
short-term reversal, etc.), open the ORIGINAL journal article and record:
- `pub_year_exact` and, where available, the **online-first / working-paper circulation date**
  (an anomaly can be arbitraged from the SSRN date, not the print date).
- `last_sample_month` — the exact final month of the study's return sample (e.g. "1993m12"),
  not just the year. This sharpens the event date for the post-sample vs post-pub boundary.
- `journal`, `volume`, `page` for citation.
- Save `data/interim/hand_timing.csv` (signal, pub_year_exact, working_paper_year,
  last_sample_month, source_url, confidence). The AI will re-run the panel using your monthly
  boundaries instead of annual ones — this is what could rescue a clean publication "kink" (H2).

## Task 2 (PIVOTAL) — Hand-code the risk-vs-mispricing FRAMING (Weeks 3–5)
For each of the same ~60 anomalies, read the original paper's abstract, introduction, and
conclusion and code the **authors' own stated interpretation**:
- `framing` ∈ {risk, mispricing, agnostic/both}: does the paper argue the return is
  compensation for risk (a covariance/factor story) or a mispricing/behavioral effect
  (over/under-reaction, limits to arbitrage), or does it explicitly decline to say?
- `framing_quote`: paste the one sentence that justifies your code.
- Save `data/interim/hand_framing.csv` (signal, framing, framing_quote, source_url).
- **This is the ground truth H3 needs.** The machine proxy is coarse (it codes book-to-market
  as "valuation"→mispricing, though Fama–French frame it as risk). Your reading replaces it.

## Task 3 — Adjudicate the ambiguous cases (Week 5)
Some anomalies are argued BOTH ways in the literature (value, size, liquidity). For these,
write a 2–3 sentence note on which framing the *original* paper took vs how the field later
reinterpreted it. Flag every hard case — the judgment call is the skill.

## Task 4 — Re-test with your data (Weeks 6–7)
With your monthly timing (Task 1) and hand framing (Task 2), the AI re-runs: (i) the nested
McLean–Pontiff decomposition using exact months, and (ii) the H3 interaction using your
`framing` variable instead of the category proxy. You interpret whether H2's publication kink
sharpens and whether mispricing anomalies now decay significantly more than risk anomalies.

## Weeks 7–8 — Write & present
Write the **Data and Institutional Background** subsection (the anomaly timeline and framing
table are yours) and a memo on whether your hand-coding changes the H2/H3 conclusions.

## Ground rules
- **Never invent a date, a month, or a framing.** "Ambiguous / not stated" is a valid, valuable
  answer — H3 has an explicit "agnostic" bucket for exactly this reason.
- Every field needs a `source_url`. Log dated entries in `logs/student_log.md`.
- The judgment calls (is this *really* a risk story?) are the contribution — flag hard cases.
