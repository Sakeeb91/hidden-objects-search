# Independent review 3 — Codex GPT-6-Astra (xhigh, read-only): audit of results, 2026-10-10

Run with `codex exec -m gpt-6-astra -c model_reasoning_effort="xhigh" -s read-only`. Prompt: `docs/review/codex_results_audit_prompt.md`. Responses: `RESPONSE_TO_REVIEWS.md`. Verbatim below; absolute links refer to the audited checkout.

---

**The counts are correct; the strongest defensible headline is “no significant excess and no compelling spider identification.”** “No spider candidate,” “complete to G≈19.5,” and the definitive rejection of C01 overstate the evidence.

Reviewed through `07f6f96`; no files modified.

**1. Population comparison and upper limit**

I independently reproduce **30 target survivors, 105 off-source survivors, expectation 105/3 = 35.0**, and **zero X-ray catalogue matches** among the target survivors. Null-field variance is **15.955**, giving dispersion **6.838**.

An exact, stratified permutation test—selecting one “target” from each matched quartet, preserving whole-field counts—gives:

| Test | Result |
|---|---:|
| Population excess, one-sided | **p = 0.7397** |
| Population difference, two-sided | **p = 0.6006** |
| J1627 matched Poisson/binomial test | p = 0.007561; Holm **0.1134** |

These support **no detected excess**, conditional on local exchangeability and the frozen selection. They do not establish that every survivor is unrelated.

Global overdispersion is largely between matched groups: within-null squared deviations total **67.33**, versus **70.0** expected under local Poisson rates. Thus matching is useful. However, the pooled “negative-binomial” calculation only propagates uncertainty in **one shared rate**; its variance/mean is **1.022**, not 6.838. It does not model field heterogeneity. [stats.py:23](</Users/sakeeb/Code repositories/Astrophysics/src/hos/stats.py:23>)

**There is no single calibrated completeness-corrected 95% companion limit in these products.** A zero-detection “rule of three” is inappropriate: seven target fields contain optical survivors. Even subtracting one hypothetical detected companion from each of those seven leaves a matched permutation lower-tail **p = 0.0928**.

A conservative finite-sample limit is possible **conditional on** at most one companion per target and independent, common detection efficiency \(\epsilon\):

\[
N_{95}=\max\{N\le15:\Pr[\mathrm{Binomial}(N,\epsilon)\le7]\ge0.05\}.
\]

Using the measured **19–20 ZTF-magnitude** recovery fractions:

| Injected semi-amplitude | Optical efficiency | Conditional \(N_{95}\) | Including 95% ellipse containment |
|---|---:|---:|---:|
| 0.20 mag | 51/70 = 0.729 | **14** | **15** |
| 0.40 mag | 40/48 = 0.833 | **11** | **12** |

These are illustrative bounds, not validated population limits: efficiency varies by target, brightness and waveform, and excludes several selection losses. **For an unspecified spider population, the current evidence supplies no defensible bound below all 15.**

**2. Injection recovery does not justify “complete”**

[a07:28](</Users/sakeeb/Code repositories/Astrophysics/pipeline/a07_injection.py:28>) samples already-detected ZTF sources uniformly from **40,436** off-source objects. This preserves real cadence and intrinsic variability, but:

- **805/1,499 reported trials (53.7%)** lie above magnitude 20; only **245 (16.3%)** are below 18. This is not a known-spider population weighting.
- The magnitude is the median of combined ZTF measurements, **not Gaia G**. One of the nominal 1,500 trials is absent from the binned summary.
- Periods are log-uniform **2–24 h**, with equal sinusoidal/ellipsoidal templates. This omits C01-like **1.23-h** orbits and realistic distributions of colours, irradiation shapes and state changes.
- Signals are added to intrinsically variable stars without separating quiet/variable hosts. That is a useful stress test, but not a calibrated companion population.
- `inside=True` bypasses localization losses; the single-source trial bypasses the **field-level common-period veto**. Catalogue inclusion, magnitude-dependent missing epochs, X-ray selection and subsequent classification are also untested.

At 19–20, recovery is **72.9% (95% binomial interval 60.9–82.8%)** for 0.20-mag semi-amplitude and **83.3% (69.8–92.5%)** for 0.40 mag. Even at 18–19, the former is only **22/28 = 78.6%**. There is no justified sharp completeness boundary at 19.5.

**3. C01: pulsator plausible, SX Phe unestablished**

The distance arithmetic is correct:

\[
-0.690568+3(1.3)(0.212716)=0.139024\ {\rm mas},
\]
giving **d > 7.193 kpc** and **\(M_G<4.704\)** under that error model.

But the measurement is **−3.246σ formally**, or **−2.497σ** after inflation. Such a result warrants checking astrometric reliability; it is not automatically invalid. **RUWE = 1.0239 is normal**, so the recorded RUWE supplies no evidence of a poor fit. Excess noise, visibility periods, image diagnostics, solution type and astrometric fidelity are absent from the follow-up product. Gaia documents spurious solutions and recommends multiple diagnostics. [Gaia validation](https://gea.esac.esa.int/archive/documentation/GDR3/Catalogue_consolidation/chap_cu9val/sec_cu9val_942/ssec_cu9val_942_astrometry.html), [Rybizki et al.](https://arxiv.org/abs/2101.11641)

The bound is consequently **conditional**, not an established distance. Increasing the inflation to 1.5 changes it to **3.75 kpc, \(M_G<6.12\)**; doubling errors gives **1.71 kpc, \(M_G<7.83\)**. Comparing against one black widow’s \(M_G=11.3\) does not establish a universal luminosity exclusion.

There is also a reproducible follow-up defect: [a09:35](</Users/sakeeb/Code repositories/Astrophysics/pipeline/a09_followup_c01.py:35>) reads the rounded a08 period. Relative to my joint weighted refit, this accumulates **0.230 cycles** over the observations. Refitting gives **19.5328597 d⁻¹**; residual white-noise FAPs become approximately **0.069 in g and 0.047 in r**, rather than the reported strong residual near the primary frequency. No convincing independent mode emerges, but monoperiodicity and stability fit **both** interpretations.

C01 is at **Galactic longitude 25.81°**, outside the released eRASS1 footprint. Its empty eRASS1 query is **no coverage**, not a nondetection. Other catalogue absences require exposure/limit checks; radio silence cannot exclude a spider. [eRASS1 footprint](https://erosita.mpe.mpg.de/dr1/), [radio-quiet J1653−0158](https://arxiv.org/abs/2009.01513)

Useful existing-data discriminants are independent nonharmonic modes reproduced across bands/seasons; extinction-corrected archival SED fitting against pulsator and Roche-lobe companion models; and archival spectra, where available, for metallicity, gravity and orbital RV variation. “SX Phe/δ Scuti candidate” is supportable; **halo SX Phe classification is premature**.

**4. Freeze: recorded chronology passes**

- Band-agreement change: `dde00e4`, **October 9, 22:37**.
- Common-period veto: `a32c209`, **October 10, 21:41:01**.
- Frozen calibration: `1554eac`, **21:41:20**.
- First committed a06 outputs: `f571c48`, **21:47:12**.

All **five frozen hashes match**, and all **73 cached provenance records** match current code and raw-data hashes. Relevant additional search/statistics files show no post-freeze changes.

The decisions are adaptive to controls/calibration, **not demonstrably post-hoc to targets**. Target period tables existed beforehand, as disclosed. Git establishes the committed sequence; it cannot prove nobody inspected those untracked tables. The guard checks the current committed calibration, not historical blindness.

**5. Other report errors**

The [control claims](</Users/sakeeb/Code repositories/Astrophysics/docs/trackA_spider_report.md:36>) confuse marginal counts with their intersection:

- Correct period **and** optical cuts: **8/11**, not 9/11.
- Those conditions **and rank first**: **7/11**.
- Uniform X-ray matches: **3/13**, not 2/13; only **1/13** also passes optical cuts at the correct period.

The assertion that all remaining variables are ordinary foreground/background stars does not follow from population nonsignificance. Contact-like morphology is also not an exclusion of an ellipsoidally modulated spider.

Track B’s **16 RV exclusions, four duration exclusions and zero nominal circular-orbit survivors** reproduce. For the former survivor I obtain **3.2144 h**, observed/expected **1.4958**, and **K = 42.299 km/s**. Its limitations are mostly disclosed. Two remaining overstatements:

- The weakest Monte Carlo result, **64/400,000**, gives adjusted **0.00272**, but its one-sided 95% Monte Carlo upper bound is **0.00335**; “≤0.003” is not a strict bound.
- The “six spectra close the eccentric loophole” recommendation uses circular velocities. As a sensitivity example, my simulation with **e=0.8**, apastron conjunction and fixed **K=33 km/s** gives a six-epoch miss rate of **4.9%**, not <1%. [b03:87](</Users/sakeeb/Code repositories/Astrophysics/pipeline/b03_survivor_context.py:87>)

Required changes, in priority order:

1. Replace categorical absence claims with “no significant excess; no compelling identification.”
2. Add the matched-field population test and an explicitly conditional companion-limit calculation.
3. Withdraw “complete to G≈19.5”; correct magnitude labels and quantify full selection efficiency.
4. Downgrade C01’s classification and qualify its distance/luminosity exclusion.
5. Correct coverage versus nondetection statements, particularly eRASS1 for C01.
6. Correct control intersections and X-ray counts.
7. Preserve full numerical periods and Gaia IDs—the a06 CSV rounds IDs into scientific notation—and rerun affected follow-up calculations.
8. Qualify Track B’s Monte Carlo bound and recompute its follow-up recommendation for eccentric orbits.

