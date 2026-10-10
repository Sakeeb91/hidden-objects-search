# Independent review 2 — Codex GPT-6-Astra (xhigh reasoning, read-only), 2026-10-09

Mathematical and statistical audit run with `codex exec -m gpt-6-astra -c model_reasoning_effort="xhigh" -s read-only`. Prompt: `docs/review/codex_math_audit_prompt.md`. Responses are in `RESPONSE_TO_REVIEWS.md`. Reproduced verbatim below; absolute links refer to the audited checkout.

---

The basic lensing physics is correct. The main problems are the interpretation of “minimum mass,” the uncalibrated Gaia exclusion rule, and the pooled Poisson comparison. **I also found a duration error that rejects the survivor under the pipeline’s own circular-orbit assumptions.**

All calculations were read-only. Track A files changed externally during the audit; findings below reflect my latest reads. No `a05` calibration, `a06` target-count, or `a07` injection results currently exist, so Track A’s numerical significance cannot yet be recomputed.

**1. Self-lensing amplitude — correct approximation; “minimum mass” needs qualification.**

For a centered uniform disk, the lensed images form an annulus with area
\[
A_{\rm images}=\pi R_*\sqrt{R_*^2+4R_E^2}.
\]
Consequently,
\[
\frac{\Delta F}{F}
=\sqrt{1+4(R_E/R_*)^2}-1
\simeq2(R_E/R_*)^2.
\]
There is **no missing factor of two** in [selflens.py](</Users/sakeeb/Code repositories/Astrophysics/src/hos/selflens.py:33>).

Away from the stellar edge, the leading-order result is independent of position on a uniform disk. Nonzero impact parameter primarily shortens the pulse; grazing crossings require the full finite-source calculation. With limb darkening,
\[
\delta(t)\simeq
\frac{2R_E^2-R_L^2}{R_*^2}
\frac{I[\mu(t)]}{\langle I\rangle},
\]
before dilution by other light. This agrees with [Agol’s large-source result](https://arxiv.org/abs/astro-ph/0303457).

For linear limb darkening,
\[
q_I(b)=\frac{1-u+u\sqrt{1-b^2}}{1-u/3}.
\]
Thus the uniform-disk inversion **overestimates** a central point-lens mass, but can **underestimate** a near-limb mass. For a BLS box depth, use the intensity averaged over the fitted pulse, not its central maximum. For an ideal full-chord average,
\[
\bar q_I(b)=
\frac{1-u+(\pi u/4)\sqrt{1-b^2}}{1-u/3}.
\]

For TIC 243307945, taking illustrative \(u=0.6\):

| Model | Mass \(M_\odot\) | \(K\), km/s |
|---|---:|---:|
| Current uniform, pure lens | 0.4058 | 42.30 |
| Central **peak**, limb darkened | 0.3318 | 36.13 |
| Central **box average**, limb darkened | 0.3758 | 39.86 |

These are model estimates, not confidence bounds. Occultation raises the required WD mass: using the code’s Nauenberg relation gives **0.7628 \(M_\odot\)** for uniform intensity, or **0.7265 \(M_\odot\)** for the illustrative limb-darkened central peak.

The KOI-3278 test numbers check out:
\[
a=99.032R_\odot,\quad R_E=0.023088R_\odot,\quad
R_{\rm WD}=0.012006R_\odot,
\]
giving **1,147.23 ppm pure lensing**, **155.12 ppm occultation**, and **992.11 ppm net**. This is an appropriate order-of-magnitude check against the published approximately 0.1% pulse, not a full reproduction of its fitted light curve. [Kruse & Agol](https://arxiv.org/abs/1404.4379)

**2. Gaia K2 — wrong as a generally conservative exclusion rule; most actual rows are much stronger than the cutoff.**

For circular orbits with independent uniform phases, \(X=v/K=\sin\phi\) has
\[
F(x)=\tfrac12+\frac{\arcsin x}{\pi},\qquad
f(x)=\frac1{\pi\sqrt{1-x^2}}.
\]
Conditioning on the minimum gives the exact untrimmed range distribution:
\[
P(\Delta v<rK)=
N\int_{-1}^{1}f(x)
\left[F\{\min(1,x+r)\}-F(x)\right]^{N-1}dx.
\]

My quadrature and simulations give:

| Epochs \(N\) | \(P(\Delta v<K)\), untrimmed | After illustrative Gaia-style clipping |
|---:|---:|---:|
| 5 | 0.08870 | ≈0.1886 |
| 6 | 0.04358 | ≈0.0916 |
| 7 | 0.02126 | ≈0.0468 |
| 10 | 0.002457 | ≈0.01145 |
| 20 | \(2.10\times10^{-6}\) | ≈\(5.8\times10^{-5}\) |

The final column uses two million simulations per \(N\), removing values outside \(Q_1-3\,IQR,\ Q_3+3\,IQR\), with NumPy’s linear percentile convention. Gaia documents that rejection rule; its precise percentile implementation should be matched before claiming exact catalog probabilities. **Five transits are plainly insufficient for an automatic conservative kill.** [Gaia data model](https://gea.esac.esa.int/archive/documentation/GDR3/Gaia_archive/chap_datamodel/sec_dm_main_source_catalogue/ssec_dm_gaia_source.html)

Recomputing every excluded row from [the CSV](</Users/sakeeb/Code repositories/Astrophysics/results/trackB/selflens_quicklook.csv>), using its actual observed amplitude:

| TIC | \(N\) | Observed range / predicted \(K\) | Ideal untrimmed tail probability |
|---:|---:|---:|---:|
| 147162665 | 10 | 0.07314 | \(1.72\times10^{-9}\) |
| 81810692 | 8 | 0.02361 | \(1.24\times10^{-9}\) |
| 138959895 | 24 | 0.07453 | \(3.43\times10^{-22}\) |
| 181164483 | 32 | 0.01921 | \(6.05\times10^{-39}\) |
| 370612437 | 7 | 0.01144 | \(1.45\times10^{-9}\) |
| 442920493 | 13 | 0.09027 | \(1.23\times10^{-11}\) |
| 365986270 | 13 | 0.02490 | \(2.63\times10^{-15}\) |
| 105995278 | 33 | 0.06231 | \(1.15\times10^{-31}\) |
| 71820872 | 29 | 0.04892 | \(2.06\times10^{-29}\) |
| 249718859 | 20 | 0.08517 | \(5.73\times10^{-18}\) |
| 63216220 | 6 | 0.01691 | \(1.02\times10^{-7}\) |
| 396659482 | 43 | 0.10222 | \(1.88\times10^{-36}\) |
| 430533621 | 13 | 0.02464 | \(2.45\times10^{-15}\) |
| 362506371 | 5 | 0.00922 | \(4.05\times10^{-7}\) |
| 54127932 | 15 | 0.01084 | \(2.52\times10^{-20}\) |
| 252721481 | 19 | 0.06666 | \(4.11\times10^{-18}\) |

These tiny values are **ideal-model probabilities, not calibrated Gaia exclusion confidences**.

Clipping simulations materially weaken the least secure rows:

- **TIC 362506371:** approximately \(2.19\times10^{-4}\), versus \(4.05\times10^{-7}\) untrimmed.
- **TIC 63216220:** approximately \(2.35\times10^{-5}\).
- **TIC 147162665:** approximately \(4.5\times10^{-6}\).

Under the circular, independent-phase model, all 16 remain strong at a 5% familywise standard. TIC 362506371 is **marginal relative to a 3σ familywise requirement**: multiplying its clipped probability by 16 gives approximately 0.0035. TIC 63216220 is next least secure. The remaining rows are solid within that model.

Important limitations:

- **Inclination:** self-lensing requires \(|\cos i|\lesssim R_*/r_{\rm conjunction}\). For the circular parameters here, \(\sin i\gtrsim0.989\); inclination cannot explain factors of 10–100.
- **Combined spectra:** Gaia combines three CCD measurements within a transit. The robust amplitude uses epoch RVs for bright stars; it is not an amplitude measured from a spectrum averaged over the entire orbit. [Gaia single-transit processing](https://gea.esac.esa.int/archive/documentation/GDR3/Data_processing/chap_cu6spe/sec_cu6spe_procsteps/ssec_cu6spe_sta.html)
- **Cadence:** \(N\) visits need not represent \(N\) independent phases. For TIC 362506371, replacing five independent phases with two gives an untrimmed probability of **1.45%**, illustrating the sensitivity to clustering.
- **Eccentricity:** use
  \[
  K_e=\frac{K_{\rm circular}}{\sqrt{1-e^2}},\quad
  v=\gamma+K_e[\cos(\nu+\omega)+e\cos\omega],
  \]
  and conjunction separation—not \(a\)—in \(R_E\). Uniform time means uniform mean anomaly, not true anomaly. Larger \(K_e\) does not guarantee a well-sampled range.

The actual epoch times, rejection behavior, and eccentricity assumptions are therefore needed for unconditional exclusions. The high RUWE values for TIC 81810692, 63216220, and 249718859 additionally warrant checking which component supplies the RV and photometric signal.

**3. Beaming and ellipsoidal amplitudes — approximately right, with deliberately low prefactors.**

The factor \(4\alpha_{\rm beam}\) is a convention:
\[
A_{\rm beam}=\bar B\,K/c,\qquad
B_\lambda=5+\frac{d\ln F_\lambda}{d\ln\lambda},
\]
where \(\bar B\) is weighted by throughput and photon counts. For a blackbody, \(B_\lambda=x/(1-e^{-x})\). My 4700 K calculation through an illustrative 600–1000 nm top-hat gives **\(\bar B=3.993\), \(\alpha=0.998\)**, hence **563 ppm**, versus the code’s 451 ppm. Actual TESS throughput and an atmosphere model are needed for precision. [Claret et al.](https://arxiv.org/html/2007.15715)

The leading ellipsoidal semi-amplitude is
\[
A_{\rm ell}=
0.15\frac{(15+u)(1+\tau)}{3-u}
\frac{M_2}{M_1}\left(\frac{R_*}{a}\right)^3\sin^2 i,
\]
with band-dependent gravity-darkening coefficient \(\tau\). Illustrative \(u=0.6,\tau=0.32\) gives **\(\alpha_{\rm ell}=1.287\)** and **207 ppm**, versus 161 ppm. [Ellipsoidal expansion](https://academic.oup.com/mnras/article/501/2/2822/6055674)

I reproduced [b02’s fit](</Users/sakeeb/Code repositories/Astrophysics/pipeline/b02_survivor_phasecurve.py:140>) from the cached photometry, including all 338 retained null periods:

| Harmonic | Measured | Corrected illustrative prediction | Null 95th percentile |
|---|---:|---:|---:|
| \(P\) | 467.8 ppm | 563.4 ppm | **1,679.3 ppm** |
| \(P/2\) | 72.2 ppm | 207.2 ppm | **279.5 ppm** |

**Prefactors alone do not change “untested.”**

However, enforcing the WD occultation model from question 1 raises the illustrative ellipsoidal prediction to **291 ppm**. That would flip the existing heuristic to “excludes.” It is model-dependent and only barely clears its sensitivity threshold; it is not a robust statistical exclusion.

**4. Period-search score — acceptable ranking statistic; not a calibrated combined significance.**

There is an important distinction in [period.py](</Users/sakeeb/Code repositories/Astrophysics/src/hos/period.py:68>). Let \(Z_b=\max_f P_b(f)\), and let \(\hat f\) maximize the mean periodogram. Then
\[
P_b(\hat f)\le Z_b
\quad\Longrightarrow\quad
p_b[P_b(\hat f)]\ge p_b(Z_b).
\]
Thus, **a valid maximum-periodogram FAP evaluated at the shared frequency remains conservative**. Choosing the shared frequency does not itself make this anti-conservative. It simply is not the exact FAP of the shared-frequency statistic. Baluev’s white-noise approximation and assumptions still matter. [Astropy documentation](https://docs.astropy.org/en/stable/timeseries/lombscargle.html#false-alarm-approximations)

For \(S=\sum_b-\log_{10}p_b\), Fisher’s statistic is
\[
T=2\ln(10)S.
\]
Independent uniform p-values give \(T\sim\chi^2_{2B}\). For two bands and \(S=5\), the combined tail is **\(1.25\times10^{-4}\)**, not \(10^{-5}\).

Shared-frequency p-values are dependent. Nevertheless, under independent bands and valid individual maximum FAPs, the pointwise bound above makes Fisher calibration conservative relative to combining the separate maxima. It does **not** justify exact Fisher equality.

Red noise, correlated band systematics, estimated per-object offsets, and underestimated errors break the analytic calibration. Daily sampling transfers slow variability into short-period aliases; masking narrow frequency intervals cannot remove every alias. Aliasing alone does not automatically invalidate Baluev under white noise.

**The score remains usable for ranking if the entire selection is calibrated on representative off-source fields**, including cadence, brightness, band availability, and preprocessing. Those fields estimate unrelated-variable contamination, not merely Gaussian-noise false alarms.

**5. Background comparison — wrong as calibrated per-target significance.**

[a06](</Users/sakeeb/Code repositories/Astrophysics/pipeline/a06_targets.py:124>) treats the pooled mean as a known, universal Poisson rate. Four corrections are necessary.

For total null count \(C\) in 51 equal-exposure fields, a Gamma prior gives
\[
\lambda\mid C\sim\Gamma(\alpha+C,\beta+51).
\]
The predictive count in one additional field is
\[
Y_{\rm new}\mid C\sim
\operatorname{NB}\!\left(
r=\alpha+C,\;
p=\frac{\beta+51}{\beta+52}
\right).
\]
This incorporates rate uncertainty. Illustratively, \(C=51\), Jeffreys prior, and \(Y\ge5\) gives **0.00428**, versus plug-in Poisson **0.00366**.

Field heterogeneity requires more:
\[
Y_j\sim\operatorname{NB}(\mu_j,\kappa),\qquad
\operatorname{Var}(Y_j)=\mu_j+\mu_j^2/\kappa.
\]
For illustration, \(\mu=1,\kappa=1\) gives \(P(Y\ge5)=0.03125\), **8.5 times** the Poisson tail. Overdispersion must be estimated from actual counts; it cannot presently be quantified.

A useful per-target exact test compares target count \(Y_j\) with its three matched null counts totaling \(C_j\):
\[
Y_j\mid(Y_j+C_j)\sim
\operatorname{Binomial}\!\left(Y_j+C_j,\frac14\right),
\]
assuming equal exposures and a common local Poisson rate. With unequal exposures, replace \(1/4\) by
\[
\frac{E_{\rm target}}{E_{\rm target}+\sum E_{\rm null}}.
\]
A hierarchical Gamma–Poisson/NB model can partially pool the poorly determined local rates while including density and selection covariates.

The actual ellipse areas span **0.0132–0.0767 deg²**, a factor **5.81**. Null latitudes differ from their parent targets by up to **2.97°**. Equal ellipse sizes within each group help, but do not guarantee equal stellar density, extinction, cadence, or X-ray sensitivity. Pooling can preserve the survey-average expectation while miscalibrating individual fields.

Finally:

- Apply Holm/Bonferroni across 17 targets: initial 5% cutoff **0.00294**. Account for both optical and X-ray tests if either can trigger a claim.
- Seventeen independent nominal 5% tests have **58.2%** probability of at least one false positive.
- Zero events in 51 nulls does **not** imply zero background: the one-sided 95% upper rate is **0.0587 per ellipse**, permitting approximately **one expected event across 17 targets**.

**6. Additional errors and overstatements.**

- **Duration uses the wrong companion-mass assumption.** [b01](</Users/sakeeb/Code repositories/Astrophysics/pipeline/b01_selflens_quicklook.py:63>) uses the reference’s `dur_ratio`. Recompute
  \[
  T_{\rm central}=\frac P\pi\arcsin(R_*/a),\qquad
  a^3=\frac{G(M_*+M_2)P^2}{4\pi^2}.
  \]
  TIC 243307945 has **3.214 h expected versus 4.808 h observed**, ratio **1.496**, exceeding 1.3. TIC 396659482 also changes to **1.312**. K1 failures increase **2→4**, leaving **zero survivors under the current circular toy model**. Eccentric apastron crossings can last longer, so “impossible” remains too strong.

- **The b02 injection is algebraically guaranteed at coefficient level.** Since the injected signal lies in the fitted design matrix,
  \[
  \hat\beta(y+X a)=\hat\beta(y)+a.
  \]
  The reported amplitude difference mostly measures vector addition to existing noise. It does not establish confidence coverage or test losses in upstream photometric processing. Use a phase-aware likelihood and noise simulations at the actual period.

- **Current caches invalidate the revised control selection.** [a04](</Users/sakeeb/Code repositories/Astrophysics/pipeline/a04_period_search.py:25>) reuses tables without checking their generating code. All 11 existing control tables lack the newly required amplitude-SNR columns. Nine companions passed the former cuts; reusing these tables with the new cuts makes **all 11 fail** through missing values. The new code-hash freeze check does not establish cache provenance.

- **Injection completeness is conditional and the searches differ.** [a07](</Users/sakeeb/Code repositories/Astrophysics/pipeline/a07_injection.py:45>) uses a source-specific grid, while a04 uses a field-specific grid. Its pool also excludes undetected/sparsely sampled sources. Moreover, the 1.2-hour search floor excludes the true modulation frequency of **7.34% of its log-uniform ellipsoidal injections** with orbital periods 2–2.4 hours.

- **Report claims exceed the evidence.** Comparing the survivor with the same inverted sample from which it was selected is not an independent false-alarm calibration. Elevated RUWE does not establish a companion. Two random-phase spectra have a **21.7%** chance of differing by less than 10 km/s even for the stated circular \(K=42.30\) km/s; schedule known quadratures instead.

Required fixes, in priority order:

1. Replace K2’s amplitude cutoff with a calibrated sampling-and-clipping likelihood, including cadence and eccentricity assumptions.
2. Fit self-lensing amplitude and duration jointly, including limb darkening, occultation, dilution, and companion mass.
3. Recalculate K1 and revise Track B’s survivor/exclusion claims.
4. Replace pooled Poisson tails with matched per-target or hierarchical predictive tests; correct for multiple testing.
5. Invalidate stale period tables and attach code, configuration, and input provenance to caches.
6. Calibrate b02 confidence limits using phase-aware models and realistic noise simulations.
7. Retain the period score as a ranking statistic; calibrate its full selection empirically.
8. Make injection searches identical to production searches and report conditional versus survey completeness.
9. Remove unsupported statistical-significance, binarity, and two-spectrum guarantees from the report.