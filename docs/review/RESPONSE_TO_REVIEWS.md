# Response to independent reviews (2026-10-09)

Review 1: fresh read-only Claude agent (`REVIEW_CLAUDE_2026-10-09.md`).
Review 2: Codex GPT-6-Astra, xhigh reasoning, read-only (`REVIEW_CODEX_ASTRA_2026-10-09.md`).
Every finding is listed with what changed. "Accepted" means fixed in code with a test unless
noted; commit subjects cite the review.

## Track B (self-lensing)

| Finding | Response |
|---|---|
| R2: K1 duration reused the reference's planet-mass ratio | **Accepted; changed the result.** Expected duration now uses star + minimum lens mass. The former survivor (TIC 243307945) is 1.50× too long for a circular orbit → 0/17 not excluded. Eccentricity caveat stated. |
| R1 minor, R2 Q2: "range < K" is not a calibrated exclusion (8.9% false kills at 5 epochs, 18.8% with clipping) | **Accepted.** K2 now uses the exact random-phase range probability and a Monte Carlo with Gaia's 3-IQR clipping, familywise over 17 signals. All 16 RV exclusions hold (≤ 0.003); TIC 362506371 is the weakest. `rv_range_cdf` reproduces the audit's values. |
| R2 Q1: uniform-disk inversion vs limb darkening | **Accepted as caveat.** Central masses may be ~18% lower; RV ranges are 1–10% of K, so no exclusion depends on it. Not modelled. |
| R2 Q3: beaming/ellipsoidal prefactors low (563/207 ppm vs 451/161) | **Accepted as caveat.** Does not change "untested" for the phase curve; with K1 the signal is excluded anyway. |
| R2: b02 injection is algebraically guaranteed | **Accepted.** Stated in the report; b02 is no longer used for any verdict. |
| R1 M7: survivor numbers not reproducible | **Accepted.** `b03_survivor_context.py` derives all of them; it also caught two id-precision bugs via an empty-result guard. |
| R1 M8, R2: two-spectrum claim wrong; K depends on R★ | **Accepted.** Report gives K = 33–42 (NS/BH) or 63–67 km/s (WD) and six random-phase epochs for < 1% miss. |
| R1: scope "16/17" to the 17 flag-free signals and the target star | **Accepted.** |
| R1: Gaia id float coercion | **Accepted.** Ids read as text into nullable integers. |

## Track A (spider pulsars)

| Finding | Response |
|---|---|
| R1 C1: "null" kind parsed as NaN, nulls silently dropped | **Accepted.** Kind renamed `offsource`; one validated reader; calibration refuses zero nulls; round-trip tests. |
| R1 C2: `idxmin` on ndarray | **Accepted** (fixed before freeze). |
| R1 C3, R1 M2, R2 Q5: plug-in Poisson, p = 0 at zero background, pooled λ, no multiplicity | **Accepted.** Per-target exact binomial vs its own three matched nulls, Jeffreys negative-binomial predictive vs all nulls, Holm across targets; dispersion index reported. |
| R1 M1: freeze guard bypassable by editing constants | **Accepted.** Frozen file stores cuts and SHA-256 of the search/cut code; a06 refuses on mismatch. |
| R1 M3: blazar confound | **Partly accepted.** Added a coherence cut (period significant in both time halves); Gaia astrometry reported for candidates. A full light-curve classifier is not implemented; any excess will be interpreted with this caveat. |
| R1 M4: controls ~7× smaller than targets; J1023/J1947 not independent | **Partly accepted.** J1023 and J1947 excluded from recovery statistics; size mismatch recorded in the calibration output. Re-ranking controls in target-sized cones is not done (data cost). |
| R1 M5: noise-biased binned amplitude | **Accepted.** Weighted sinusoid fit with χ²-scaled error; cut ≥ 0.05 mag at ≥ 5σ. |
| R1 M6, R2 Q4: Baluev FAP is not a probability under red noise; Fisher sum mis-stated | **Accepted.** The score is used only as a ranking statistic; all calibration is empirical from off-source fields. |
| R2: stale cached period tables | **Accepted.** Provenance (code + raw-data hashes) stored and checked; mismatch forces recompute. |
| R2: injection and production used different grids; 1.2 h floor | **Accepted.** One fixed grid to 0.96 h everywhere. |
| R1: empty fields not re-readable | **Accepted.** |
| R1: single-band sources pass `bands_agree` automatically | **Not changed.** Faint spider companions are often single-band in g; recorded via `n_bands`. |
| R1: no barycentric correction (~0.07 phase smear at 2 h) | **Not changed.** Smaller than the fold resolution; noted. |
| R1: SIMBAD-within-3″ "known" flag too aggressive; ATNF/TRAPUM not queried | **Partly accepted.** "Known" is now a set of named columns reported separately; ATNF query to be added at vetting. |

## Review 3 (Codex GPT-6-Astra, results audit, 2026-10-10)

| Finding | Response |
|---|---|
| "No spider candidate" overstated | **Accepted.** Headline is "no significant excess and no compelling identification". |
| Add a matched population test and a conditional limit | **Accepted.** `a10_population.py`: exact stratified permutation (p = 0.74); conditional N95 = 11–15; all values match the audit. |
| "Complete to G ≈ 19.5" unjustified; magnitudes are ZTF medians | **Accepted.** Report gives conditional efficiencies with CIs and lists what injections bypass. |
| C01 classification premature; distance bound model-dependent; eRASS1 no coverage | **Accepted.** "SX Phe / δ Sct candidate"; bounds for 1.3/1.5/2.0 error inflation; Gaia astrometric diagnostics added (clean); eRASS1 reported as no coverage. |
| a09 used a rounded period | **Accepted.** a08 refines each period; with the refined period the residuals show no second mode (FAP ≈ 0.05), as the audit found. |
| Control intersections and X-ray counts wrong (9/11, 2/13) | **Accepted.** 8/11, 7/11 with rank 1; 3/13 uniform X-ray, 1/13 also recovered. |
| Gaia ids rounded / corrupted in a06 output | **Accepted.** Exact Int64 ids via a tested helper; full-precision floats. Counts unchanged. |
| Track B "≤ 0.003" not a strict bound | **Accepted.** Exclusion now uses the 95% Clopper–Pearson Monte Carlo bound (worst 0.0033 → familywise ≤ 0.0034). |
| Six-spectrum recommendation ignores eccentricity | **Accepted.** e = 0.8 at apastron: six spectra miss 4.9%; twelve needed for < 1%. |
| Pooled NB models one shared rate, not field heterogeneity | **Accepted as stated limitation**; the matched per-target test and the permutation test carry the inference. |
| Git cannot prove target tables were unread | **Accepted as caveat** in the report. |
