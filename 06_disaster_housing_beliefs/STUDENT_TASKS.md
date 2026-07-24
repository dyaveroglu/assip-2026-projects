# Student manual tasks — Mateo Eduardo Stine (Project 06, Disaster Housing & Beliefs)

**The AI has built:** the full data pipeline (Zillow ZHVI, OpenFEMA declarations, Yale climate
opinion, FEMA National Risk Index, 2020 vote share), a stacked exposure
difference-in-differences around Hurricanes Ian (2022) and Helene (2024), belief-moderation
tests, pre-trend diagnostics, three figures, and a complete paper draft.

**The current honest finding is a null / reversal.** On average, hard-hit counties' home
values did **not** re-price disaster risk (Treat x Post = +0.001, t=0.34). The
"believers re-price" pattern that a naive belief split appears to show is a **pre-trend
artifact**: it is driven by Florida's booming, high-belief Ian coast, it reverses within
Helene, and it vanishes once we remove pre-trends. The single weakest link in the whole
design is **how we measure exposure** -- and that is your job.

**Your work is not a footnote. It is the only path to a clean test.** The AI proxied
"hard-hit" with a coarse yes/no FEMA flag (did a county get Individuals & Households Program
aid?). That flag mixes a county buried under 30 inches of rain with one designated for
administrative convenience, and it has no notion of *distance to the track*, *wind speed*, or
*surge depth*. Only a careful human working from NOAA/FEMA primary sources can turn this
into a graded, credible exposure measure -- the thing the belief test actually needs.

## Task 1 (PIVOTAL) -- Hand-collect exact landfall geography (Weeks 1-3)
For **each** storm (Ian, 28 Sep 2022; Helene, 26 Sep 2024):
- From **NOAA National Hurricane Center Tropical Cyclone Reports** record the exact landfall
  point(s) (lat/lon), date/time, and Saffir-Simpson category at landfall.
- From the **NHC wind-swath and storm-surge products**, list the counties inside the
  hurricane-force (64-kt) wind swath and the surge-inundation footprint.
- Save `data/interim/landfall_geography.csv`
  (`event, county_fips, county_name, dist_km_to_track, peak_wind_kt, surge_ft, source_url`).
- **This creates the graded distance/intensity exposure** that replaces the AI's binary IHP
  flag. The AI will re-run every regression using your continuous exposure.

## Task 2 (PIVOTAL) -- Validate & correct the FEMA treatment set (Weeks 3-4)
The AI's treated set is the IHP-designated counties in `data/raw/fema_declarations.csv`.
- Cross-check each against the county lists in the **FEMA disaster-declaration amendments**
  and NHC reports. Flag counties that are IHP-designated but were *barely* affected (false
  positives) and hard-hit counties that were *not* IHP-designated (false negatives, e.g.
  administrative gaps).
- Save `data/interim/treatment_corrections.csv` (`event, county_fips, ai_treated,
  your_treated, reason, source_url`).

## Task 3 -- Belief-data judgment call (Week 5)
The AI used Yale YCOM "worried" (2020 vintage) as the belief measure. Decide, and document,
whether a **pre-storm** vintage is the right one (it should predate the storm so beliefs are
not themselves a response to it), and whether "worried," "happening," or "personal harm"
best captures the mechanism in H2. Note the vintage/variable choice in a short memo.

## Task 4 -- Re-test with your data (Weeks 6-7)
With your graded exposure (Task 1) and corrected treatment (Task 2), the AI re-runs: (i) the
baseline DiD with continuous distance/intensity, (ii) the belief triple-interaction, and
(iii) the pre-trend diagnostics. **You interpret whether the honest null survives** a sharper
exposure measure, or whether a belief-conditional effect emerges once exposure is measured
correctly.

## Weeks 7-8 -- Write & present
Write the **Data and Institutional Background** section (the storm timelines and affected-
county tables are yours), and a memo on whether your hand-collected geography changes the
conclusion.

## Ground rules
- **Never invent a coordinate, a county, or a wind speed.** "Not found / ambiguous" is a
  valid, valuable answer.
- Every row in your CSVs must carry a `source_url` to an NOAA or FEMA primary document.
- Log dated entries in `logs/student_log.md`.
- The judgment calls (was this county *really* hard-hit? is this belief vintage pre-storm?)
  are the skill -- flag hard cases for discussion.
