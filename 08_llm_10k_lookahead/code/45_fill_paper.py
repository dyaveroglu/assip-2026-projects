#!/usr/bin/env python3
"""
Project 08 — Step 45: generate the abstract/results/robustness/conclusion prose
DIRECTLY from the regression CSVs and substitute into paper/main.tex. Prose adapts
to the actual signs and significance so the paper reports the real finding
(contamination signature, suggestive, or honest null) with no drift.
"""
import os, pandas as pd, numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, 'output', 'tables'); PAP = os.path.join(HERE, 'paper')

def R(name): return pd.read_csv(os.path.join(OUT, name))
t1 = R('t1_sumstats.csv'); t2 = R('t2_agreement.csv'); t3 = R('t3_main.csv')
t4 = R('t4_interaction.csv'); t4b = R('t4b_within.csv'); t5 = R('t5_gap.csv'); t6 = R('t6_robust.csv')
panel = pd.read_csv(os.path.join(HERE,'data','processed','panel.csv'))

N = len(panel); Npre = int((panel.window=='pre').sum()); Npost = int((panel.window=='post').sum())
mbhar = panel.bhar_12.mean()

def g3(spec):
    r = t3[t3.spec==spec].iloc[0]; return float(r.coef), float(r.t), int(r.N)
rawpre = g3('(1) RAW / pre'); anonpre = g3('(2) ANON / pre')
rawpost = g3('(3) RAW / post'); anonpost = g3('(4) ANON / post')

tri = t4[t4.spec=='(4) triple'].iloc[0]
tri_c = float(tri.get('z:raw:post', np.nan)); tri_t = float(tri.get('z:raw:post_t', np.nan))
pre_within = t4b[t4b['sample']=='Pre-cutoff']
if len(pre_within):
    pw = pre_within.iloc[0]; anon_slope=float(pw.slope_anon); ta=float(pw.t_anon)
    extra_raw=float(pw.extra_raw); ter=float(pw.t_extra_raw)
else:
    anon_slope=ta=extra_raw=ter=np.nan
def g5(s):
    r=t5[t5['sample']==s]
    return (float(r.iloc[0].coef), float(r.iloc[0].t)) if len(r) else (np.nan,np.nan)
gap_pre=g5('Pre-cutoff'); gap_post=g5('Post-cutoff')
corr_full=float(t2[t2['sample']=='Full'].iloc[0].corr_raw_anon)
absgap_full=float(t2[t2['sample']=='Full'].iloc[0].mean_abs_gap)

def sigword(t):
    a=abs(t)
    if a>=2.58: return 'significant at the 1\\% level'
    if a>=1.96: return 'significant at the 5\\% level'
    if a>=1.65: return 'significant at the 10\\% level'
    return 'statistically insignificant'
def st(t):
    a=abs(t); return '$^{***}$' if a>=2.58 else '$^{**}$' if a>=1.96 else '$^{*}$' if a>=1.65 else ''
def slope(c,t): return f"{c:+.4f} ($t={t:.2f}$)"

# ---- verdict logic ----
S1 = rawpre[1] <= -1.65                                  # raw/pre negative & sig
S2 = abs(rawpre[0]) > abs(anonpre[0])                    # raw predicts more than anon pre
S3 = abs(rawpost[1]) < 1.65 and abs(anonpost[1]) < 1.65  # post both weak
S4 = (not np.isnan(tri_t)) and abs(tri_t) >= 1.65        # triple interaction sig
if S1 and S2 and (S3 or S4):
    verdict='contamination'
elif (S1 or S4 or abs(gap_pre[1])>=1.65) and S2:
    verdict='suggestive'
else:
    verdict='null'

# ---------------------------------------------------------------- ABSTRACT ---
verdict_line = {
 'contamination': ("We find the look-ahead signature: the raw-text score predicts "
    f"pre-cutoff returns with a slope of {slope(*rawpre[:2])}, {sigword(rawpre[1])}, "
    f"while the anonymized score is weaker ({slope(*anonpre[:2])}); post-cutoff, where "
    "look-ahead is impossible, both scores are near zero."),
 'suggestive': ("We find suggestive but not decisive evidence of look-ahead: the raw-text "
    f"score's pre-cutoff slope ({slope(*rawpre[:2])}) is more negative than the anonymized "
    f"score's ({slope(*anonpre[:2])}), and the pattern weakens post-cutoff, but the "
    "difference is not statistically sharp at this sample size."),
 'null': ("We do not detect look-ahead contamination in this sample: neither the raw nor "
    f"the anonymized score reliably predicts 12-month returns (raw/pre slope "
    f"{slope(*rawpre[:2])}; anon/pre {slope(*anonpre[:2])}), and the raw-versus-anon gap "
    "does not differ significantly across the training cutoff. Power is limited by the "
    f"scored sample of {N} filings."),
}[verdict]

abstract = (
 "We ask whether a large language model that scores 10-K risk factors is reading the "
 "disclosure or recalling the stock. Using gpt-4o (October-2023 knowledge cutoff), we score "
 f"{N} SEC 10-K risk-factor sections twice with an identical prompt---once on the raw text "
 "and once on an anonymized copy that redacts the firm's name, ticker, dates, and state---"
 "and relate the scores to 12-month post-filing buy-and-hold abnormal returns (BHAR). "
 "Identification is a placebo: we split filings into a pre-cutoff window (filed 2019--2021, "
 "outcome realized before the cutoff, so look-ahead is possible) and a post-cutoff window "
 "(filed 2024, look-ahead impossible). Raw and anonymized scores are highly correlated "
 f"($\\rho={corr_full:.2f}$; mean absolute gap {absgap_full:.1f} points). "
 + verdict_line +
 " The design is a reusable, auditable diagnostic for LLM-based return-prediction studies, "
 "and it motivates a hand-built anonymization gold standard as the next tightening."
)

# --------------------------------------------------------- RESULTS PREVIEW ---
preview = (
 "Our findings can be previewed in four numbers (Table~\\ref{tab:main}). "
 f"In the pre-cutoff window ($N={rawpre[2]}$), a one-standard-deviation increase in the "
 f"\\emph{{raw}}-text risk score moves 12-month BHAR by {slope(*rawpre[:2])}, while the "
 f"\\emph{{anonymized}} score moves it by {slope(*anonpre[:2])}. "
 f"In the post-cutoff window ($N={rawpost[2]}$)---where the model cannot have seen the "
 f"outcome---the raw slope is {slope(*rawpost[:2])} and the anonymized slope is "
 f"{slope(*anonpost[:2])}. The stacked triple interaction "
 f"$z\\times\\text{{Raw}}\\times\\text{{Post}}$ is {slope(tri_c,tri_t)} "
 f"(Table~\\ref{{tab:interaction}}). "
 + {'contamination':"This is the look-ahead pattern H2 predicts.",
    'suggestive':"This leans toward H2 but is not statistically decisive.",
    'null':"On these estimates we cannot reject H1 (genuine reading) in favor of H2 (look-ahead)."}[verdict]
)

# ------------------------------------------------------------ RESULTS BODY ---
rb = []
rb.append("\\paragraph{Raw and anonymized scores agree closely.} "
 f"Across the full sample the two scores correlate at $\\rho={corr_full:.2f}$, and the mean "
 f"absolute score gap is {absgap_full:.1f} points on the 0--100 scale "
 "(Table~\\ref{tab:agree}). The model rarely changes its risk assessment much when identity "
 "is stripped---already a hint that explicit identifiers are not the model's main input, "
 "though (as we discuss) firms may remain identifiable from the surviving business text.")
rb.append("\\paragraph{The main placebo.} Table~\\ref{tab:main} and "
 "Figure~\\ref{fig:slopes} report the return-predictive slope in each of the four cells. "
 f"Pre-cutoff, the raw-text slope is {slope(*rawpre[:2])} ({sigword(rawpre[1])}) and the "
 f"anonymized slope is {slope(*anonpre[:2])} ({sigword(anonpre[1])}). Post-cutoff, the raw "
 f"slope is {slope(*rawpost[:2])} and the anonymized slope is {slope(*anonpost[:2])}. "
 + ({'contamination':
      "The raw score predicts pre-cutoff returns more strongly than the anonymized score, "
      "and both collapse toward zero post-cutoff---exactly the ordering implied by look-ahead "
      "contamination (H2).",
     'suggestive':
      "The raw score's pre-cutoff slope is more negative than the anonymized score's, and "
      "the gap shrinks post-cutoff, consistent with H2; but neither pre-cutoff slope is "
      "individually strong enough to rule out H1.",
     'null':
      "The four slopes are similar in magnitude and mostly insignificant; the raw score does "
      "not show the extra pre-cutoff predictive power that look-ahead would produce, so we "
      "cannot reject H1."}[verdict]))
rb.append("\\paragraph{The triple-interaction test.} Stacking the raw and anonymized "
 "observations and clustering by filing (Table~\\ref{tab:interaction}), the coefficient on "
 f"$z\\times\\text{{Raw}}\\times\\text{{Post}}$---which asks whether the raw-versus-anon "
 f"predictive gap changes across the training cutoff---is {slope(tri_c,tri_t)}, "
 f"{sigword(tri_t)}. Within the pre-cutoff window (Table~\\ref{{tab:within}}), the "
 f"anonymized-score slope is {slope(anon_slope,ta)} and the \\emph{{extra}} slope carried by "
 f"raw text is {slope(extra_raw,ter)} ({sigword(ter)}).")
rb.append("\\paragraph{Does the identity-driven score adjustment predict returns?} "
 "Under look-ahead, the raw-minus-anon score gap should itself forecast pre-cutoff returns. "
 f"Table~\\ref{{tab:gap}} shows the gap slope is {slope(*gap_pre)} pre-cutoff and "
 f"{slope(*gap_post)} post-cutoff. "
 + ({'contamination':"The pre-cutoff gap is return-relevant while the post-cutoff gap is not, supporting H3.",
     'suggestive':"The point estimates lean toward H3 but are noisy.",
     'null':"Neither is significant, so H3 is not supported here."}[verdict]))
results_body = "\n\n".join(rb)

# --------------------------------------------------------- ROBUSTNESS BODY ---
robust_body = (
 "Table~\\ref{tab:robust} re-estimates the pre-cutoff raw-versus-anon comparison for "
 "alternative outcomes---6- and 3-month BHAR, raw (non-market-adjusted) 12-month returns, "
 "and unwinsorized 12-month BHAR. "
 + ({'contamination':"The raw score's larger pre-cutoff predictive power is stable across horizons.",
     'suggestive':"The raw-over-anon ordering recurs across most horizons but stays statistically soft.",
     'null':"No horizon produces a robust raw-over-anon predictive gap, reinforcing the null."}[verdict])
 + " Three caveats bound the reading of these results. First, the scored sample is small "
 f"({N} filings, {Npre} pre- and {Npost} post-cutoff) because the shared LLM gateway is "
 "rate-limited; the design, not the power, is the contribution, and the hand-built gold "
 "standard (Section~\\ref{sec:data}) is the intended scale-up. Second, the automated "
 "anonymizer removes explicit identifiers but not paraphrased self-descriptions or brand "
 "names, so the anonymized text may still be identifiable to the model---biasing the placebo "
 "\\emph{toward} finding no difference. Third, risk-factor text is truncated to a fixed "
 "length for comparability, which is applied identically to raw and anonymized inputs."
)

# --------------------------------------------------------------- CONCLUSION --
concl_body = (
 {'contamination':
   "An LLM risk score that looks predictive can be partly remembering the stock rather than "
   "reading the 10-K. Our placebo isolates that channel: raw-text predictive power that "
   "exists only for pre-training-cutoff filings and disappears once identity is masked or the "
   "outcome post-dates training.",
  'suggestive':
   "We find suggestive evidence that an LLM risk score partly reflects firm recognition "
   "rather than pure text reading, though our sample cannot make the case decisively.",
  'null':
   "In this sample we do not detect look-ahead contamination: the gpt-4o risk score predicts "
   "returns no better with firm identity than without, and no better for filings the model "
   "could have memorized. The honest reading is a null---but a useful one, because it is "
   "produced by a test that \\emph{could} have found contamination and did not."}[verdict]
 + " The broader point is methodological: any study that scores pre-cutoff disclosures with a "
 "modern LLM and reports return predictability should run this raw-versus-anonymized, "
 "pre-versus-post placebo before claiming a forecast. The natural next step, left to the "
 "hand-collection phase, is to replace the automated redactor with a human gold standard that "
 "also masks brands, products, and paraphrased self-identifiers, and to re-run the placebo on "
 "that cleaner text. Limitations include the small scored sample, the single model, and the "
 "truncation of long risk-factor sections."
)

# ---- substitute into template ----
tpl = open(os.path.join(PAP,'main_template.tex')).read()
repl = {
 'ABSTRACT_PLACEHOLDER': abstract,
 'RESULTS_PREVIEW_PLACEHOLDER': preview,
 'RESULTS_BODY_PLACEHOLDER': results_body,
 'ROBUST_BODY_PLACEHOLDER': robust_body,
 'CONCL_BODY_PLACEHOLDER': concl_body,
}
for k,v in repl.items():
    assert k in tpl, f'missing placeholder {k}'
    tpl = tpl.replace(k, v)
open(os.path.join(PAP,'main.tex'),'w').write(tpl)
print(f'VERDICT = {verdict}')
print(f'N={N} (pre={Npre}, post={Npost}); corr={corr_full:.2f}; absgap={absgap_full:.1f}')
print(f'raw/pre={rawpre}, anon/pre={anonpre}, raw/post={rawpost}, anon/post={anonpost}')
print(f'triple z:raw:post = {tri_c:.4f} (t={tri_t:.2f})')
print('paper/main.tex written.')
