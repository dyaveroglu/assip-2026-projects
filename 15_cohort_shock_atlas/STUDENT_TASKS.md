# Cohort capstone — division of labor (all 14 students co-author)

**The AI has built:** the uniform event-study atlas across ~2,000 firms and 10 dated shocks,
the meta-tests, figures, and a complete draft. Two robust findings: differentiation scales with
shock size (corr 0.69); SVB uniquely propagates (contagion).

**This paper is only as good as the event timing and exposure measures YOU bring.** The atlas
uses a single calendar date per shock and measures aggregate + dispersion only. Turning it into
a real market-efficiency study requires each shock's *exact* timing (announcement vs. effective,
before/after market close) and its *firm-level exposure* — both of which live with the student
who studied that shock.

## Shock owners (verify timing + contribute exposure)
Each owner does three things for their shock: (1) confirm the **exact event date/time** from a
primary source (was it pre- or post-close? announcement or effective date?); (2) hand off their
paper's **firm-level exposure measure** so the cohort can test whether it drives the dispersion;
(3) write that shock's paragraph.
- **SVB collapse** — Aaron Zhang (#10): uninsured-deposit / HTM exposure
- **ChatGPT & GPT-4** — Nam Ngo (#09): AI-exposure (AIIE) measure
- **April-2025 tariffs & pause** — Deniz Yaveroglu (#05): import-input intensity
- **CHIPS Act / awards** — Alexander Tang (#11): semiconductor/subsidy exposure
- **Reg-NMS half-cent tick** — Kushal Borra (#12): tick-constrained eligibility
- **GENIUS Act** — Dildora Jo'rabekova (#13): stablecoin/crypto exposure
- **Buyback excise tax (IRA)** — Christopher Dadoo (#04): repurchase intensity
- **SEC 5-day 13D rule** — (governance shock; Aiden Chen #03 to bring a governance proxy)

## Everyone (the exposure meta-test)
The whole cohort's papers each produced a firm-level exposure/treatment variable. Assemble them
into one crosswalk (`data/interim/exposure_by_shock.csv`, keyed by permno × shock) so the AI can
test the paper's central open question: **is the cross-sectional dispersion explained by
exposure, and was exposure priced before the announcement (leakage)?** Students without a dated
shock (Philipov, M. Zhou, Rakshana, Lasya, Mateo, Andy) each contribute one exposure column
and/or take a writing role (intro, method, robustness, the efficiency interpretation).

## Writing leads
- Introduction & framing: Deniz, Dadoo
- Methods & atlas table: Kushal, Nam
- Efficiency interpretation & conclusion: Andy Pham, Aaron

## Ground rules
- **Never invent a date or an exposure value.** Cite the primary source for every event time.
- Log dated entries in `logs/student_log.md`. Flag disagreements (e.g., is the tariff "event"
  April 2 after close or April 3?) — those judgment calls are the science.
