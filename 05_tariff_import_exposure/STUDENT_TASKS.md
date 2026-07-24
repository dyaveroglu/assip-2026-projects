# Student manual tasks — Deniz Yaveroglu (Project 05, Tariff / Import Exposure)

**The AI has built:** the full data pipeline (CRSP daily returns, Fama–French market,
Compustat fundamentals, the BEA imported-input-intensity industry measure), the paired
market-model event study around the April 2 shock and the April 9 pause, all six tables,
two figures, and a complete paper draft. **The core result is real:** conditional on size
and market beta, firms in high imported-input-intensity industries underperformed on the
tariff shock (−0.73pp per SD, t = −2.35) and rebounded on the pause (+0.60pp per SD,
t = 1.78); the pattern is opposite-signed and nearly symmetric among non-microcap firms
(−0.77pp / +0.77pp, both t ≈ 2.1).

**Your work is not a footnote — it is the only path to a *firm-level, causal* version of
this paper.** The AI's exposure measure is an **industry** proxy from input-output tables.
It has two known weaknesses that only a careful human reading actual filings can fix, and
fixing them is a genuine research contribution:

1. It is measured at the **industry** level, so every firm in an industry gets the same
   exposure. Two apparel firms — one sourcing entirely from Vietnam, one reshored to
   Mexico — look identical to it. They are not.
2. It captures **imported intermediate inputs** but, by input-output construction,
   **misses retailers/brands that import *finished* goods** (Nike, Five Below, Wayfair).
   Those are among the most tariff-exposed firms in the market, and our industry measure
   scores them *low*. This is the single biggest gap in the paper.

Your hand-collected 10-K sourcing data closes both gaps and — critically — lets us date
*which* countries' tariffs mattered on April 2 (broad) versus April 9 (pause excluded
China), which is what turns a correlation into an identification.

## Task 1 (PIVOTAL) — Hand-verify 10-K input sourcing for 80–100 firms (Weeks 1–4)
The AI will give you `data/interim/firms_to_verify.csv`: a stratified sample of ~90 firms
spanning the exposure quartiles (so you are not just reading obvious importers). For each
firm, open the most recent **10-K** (SEC EDGAR) and record, in
`data/interim/sourcing_verified.csv`:
- `import_reliance` (High / Medium / Low / None): does the firm describe material reliance
  on imported inputs or imported finished goods? Quote the sentence.
- `source_countries`: the specific countries named (China, Vietnam, Mexico, Canada, EU, …).
- `finished_vs_input`: does it import **finished goods for resale** or **inputs/components**?
  (This is the flag our industry measure cannot see.)
- `tariff_language` (0/1): does the filing's risk factors explicitly discuss tariffs/trade
  policy as a risk?
- `page`/`url` and a one-line quote for **every** field. **If you cannot find it, write
  "not found" — never guess.**
Read the "Business," "Risk Factors," and "MD&A" sections. Log every firm in
`logs/student_log.md` with the date and how long it took.

## Task 2 (PIVOTAL) — Build the April-2025 country-tariff map (Weeks 4–5)
The two events differ in *which countries* were affected: April 2 hit ~90 countries; the
April 9 pause **exempted China** (whose tariff was instead raised). Build
`data/interim/country_tariff_apr2025.csv` (country, apr2_tariff_pct, apr9_status
[paused/raised/unchanged], source_url) from the official announcements and reputable
coverage. This lets the AI construct a *firm-specific* treatment: a China-sourcing firm and
a Vietnam-sourcing firm should react **differently** on April 9. That heterogeneity is a
clean test the industry proxy cannot run.

## Task 3 — Re-score and re-run (Weeks 5–6)
Merge your Task 1 sourcing flags to the panel. The AI will re-estimate the shock/pause
regressions with (a) your firm-level `import_reliance` in place of the industry proxy and
(b) a **China-exposure × April-9** interaction from Task 2. You report whether the effect
**strengthens, weakens, or reverses**, and whether finished-goods importers (the ones the
industry measure missed) show the largest reaction. Either outcome is publishable.

## Task 4 — Confounds and clean events (Weeks 6–7)
For your ~90 firms, hand-check for **firm-specific news** in the April 2–10 window (earnings,
guidance cuts, analyst actions) using company IR pages and the business press. Record
`data/interim/news_flags.csv` (permno, date, headline, source). Firms with idiosyncratic
news are dropped in a robustness run. Separately, note any firm that **pre-announced**
sourcing shifts before April 2 — these speak to the pre-trend the paper flags honestly.

## Weeks 7–8 — Write and present
Write the paper's **Data section** on the firm-level sourcing measure (you will know it best)
and a one-page memo: *what did hand-reading the filings change?* Present the before/after —
industry proxy vs. your firm-level measure — and the China-vs-rest April-9 split.

## Ground rules
- **Never invent a number or a source.** Every sourcing flag needs a quote + a URL.
- Log dated entries in `logs/student_log.md`: firms read, judgment calls, time spent.
- When a firm's sourcing is genuinely ambiguous (diversified conglomerate, no country
  named), code it "ambiguous" and explain — those judgment calls are the real skill.
