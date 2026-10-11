# Track A: spider-pulsar companions in new Fermi-LAT sources (2026-10-10)

## Question

Millisecond pulsars that irradiate or evaporate a close companion ("spiders": black widows
and redbacks) are often found first as unidentified Fermi-LAT gamma-ray sources, then
pinned down by the companion's optical modulation at the orbital period (2–24 h). A
systematic ZTF search of the *previous* catalogue (4FGL-DR3) exists (Lu et al. 2024). Do
the unassociated sources **new in 4FGL-DR4** hide spider companions that ZTF can see?

## What was searched

| | Fields | ZTF sources searched | Inside the 95% ellipse | Area (deg²) |
|---|---:|---:|---:|---:|
| Targets (DR4-new, unassociated, pulsar-like) | 15 | 11,961 | 9,349 | 0.58 |
| Off-source nulls (3 per target, same ellipse) | 45 | 40,436 | 31,874 | 1.75 |
| Known-spider controls (searched blind) | 13 | 2,604 | 2,206 | 0.10 |

Target selection (`a01`): unassociated 4FGL-DR4 sources first released in DR4, Dec > −28°,
clean flags, 95% ellipse ≤ 0.2°, pulsar-likeness ≥ 0.1 (random forest, CV AUC 0.987),
|b| > 10°, and ≤ 50,000 Gaia sources/deg² (five targets deferred: three near the plane,
two too dense for the archive). Light curves: ZTF DR24 (`a03`), one backend per field.

Pipeline: multiband Lomb-Scargle on one fixed grid (0.96 h–2 d), aliases masked
(`a04`); a source is **spider-like** if inside the ellipse, the period is significant in
every band and in both halves of the data, the fitted amplitude is ≥ 0.05 mag at ≥ 5σ,
and its period is not shared by ≥ 3 spider-like stars in the same field. The
**compound** tier also requires an X-ray source from a uniform all-sky survey (eRASS1 or
2RXS). Cuts, null rates and code hashes were frozen and committed (`1554eac`) before any
target was examined; `a06` refuses to run otherwise.

## Calibration (off-source and controls only)

- Spider-like periodic stars per null ellipse: **2.33** (dispersion index 6.8).
- Spider-like **with** a uniform X-ray match: **2 in 45 ellipses** (0.044 per ellipse).
- Blind controls (`results/trackA/a10_population.json`): all 11 independent known
  companions are in the ZTF tables; **8/11** are recovered at the right period (or P/2)
  *and* pass every cut, and **7/11** of those also rank first in their field. Misses
  include the transitional pulsar 3FGL J1544.6−1125 (disk state, no coherent orbit),
  J1048+2339 (wrong period) and J2129−0429 (coherence 1.3 < 2).
- Only **3/13** known spiders have a uniform-survey X-ray match, and only **1/13** also
  passes the optical cuts at the right period: the compound tier is high-purity but
  very low completeness.
- Control ellipses are ~7× smaller than target ellipses, so ranks overstate sensitivity.

## Sensitivity (injection-recovery, `a07`)

1,500 irradiation/ellipsoidal signals (orbital periods 2–24 h, log-uniform) planted in real
off-source light curves; magnitudes are the **median ZTF magnitude** of the host, not Gaia G:

| Semi-amplitude | G < 18 | 18–19 | 19–20 | > 20 |
|---|---|---|---|---|
| 0.05 mag | ~100% | 50–58% | 15–25% | ~1% |
| 0.10 mag | 100% | 71–85% | 33–48% | 4% |
| 0.20 mag | 90–100% | 76–82% | 69–77% | 23–29% |
| 0.40 mag | 71–100% | 89–100% | 78–90% | 57–66% |

Recovery is high (≳ 75%) for 0.2–0.4 mag semi-amplitudes brighter than ZTF mag ≈ 20 and
poor fainter than 20, where most black-widow companions lie. These are **conditional
optical efficiencies**, not survey completeness: hosts are already-detected ZTF objects
(54% fainter than mag 20), the ellipse-containment and per-field common-period losses are
bypassed, shapes are idealised, and C01-like orbits below 2 h are not injected. At ZTF mag
19–20 the recovery is 73% (95% CI 61–83%) at 0.2 mag and 83% (70–93%) at 0.4 mag.

## Result

| | Targets | Expected from matched nulls |
|---|---:|---:|
| Spider-like periodic stars | **30** | 35.0 |
| … with a uniform-survey X-ray match | **0** | 0.67 |
| … with any X-ray match (incl. Swift/XMM) | 0 | — |
| Known pulsar / spider candidate (SpiderCat, Lu+2024, ATNF) | 0 | — |

Per field, the largest excess is 4FGL J1627.0+1035 (7 vs 4 in its three nulls,
matched-binomial p = 0.0076, **Holm-adjusted 0.11**). Across all targets, an exact
stratified permutation test over the matched quartets gives **p = 0.74** for an excess
(two-sided 0.60). **No target field and no population-level excess is detected.**

This does not show that every star in the ellipses is unrelated to the gamma-ray source:
seven target fields contain spider-like stars, so no small upper limit follows. Even under
favourable assumptions (≤ 1 companion per target, common efficiency 73–83%), the
conditional 95% limit is 11–15 companions among 15 targets (`a10_population.json`).

## The uncatalogued periodic stars (`a08`, `a09`)

24 spider-like stars in the target ellipses appear in no catalogue checked (SpiderCat,
Lu+2024, ATNF, VSX, ZTF periodic variables of Chen+2020; SIMBAD reported separately;
checked 2026-10-10). Vetting (`results/trackA/a08_vetting.csv`, figures in
`docs/figures/trackA/`):

- 5 have periods that recur among off-source stars (0.2516, 0.3365, 0.4897, 0.5072,
  0.9619 d): cadence systematics.
- 3 look like contact/ellipsoidal binaries (equal minima at 2P); 1 like a pulsator; the
  rest are faint and unclassified.
- **C01** (P = 1.2286984 h after refinement, G = 19.0, BP−RP = 0.43, 4FGL J1627.0+1035
  ellipse) was the most spider-like (symmetric sinusoid; black widows reach 75-min
  orbits). Evidence (`a09_c01_followup.json`): no significant second mode after
  pre-whitening (residual FAP ≈ 0.05 in g and r); frequency and amplitude stable over
  2018–2025 (both expected for a pulsator *and* for an orbit); clean astrometry (RUWE 1.02,
  20 visibility periods) with parallax −0.69 ± 0.21 mas (−3.2σ). The distance bound
  depends on the error model: d > 7.2 / 3.8 / 1.7 kpc and M_G < 4.7 / 6.1 / 7.8 for error
  inflations 1.3 / 1.5 / 2.0, each brighter than the 75-min black widow PSR J1653−0158's
  companion (M_G ≈ 11.3), though black-widow luminosities vary. No radio counterpart
  (NVSS, FIRST, VLASS, LoTSS; radio-quiet spiders exist) and none in 2SXPS or 4XMM;
  **eRASS1 does not cover it** (l = 25.8°). Verdict: an **SX Phe / δ Sct candidate**; the
  spider interpretation is disfavoured, not excluded.
- C15 (P = 2.46 h, sharp brightenings) has Gaia M_G = 9.2, BP−RP = 2.1: an M dwarf,
  plausibly a flaring fast rotator.
- Contact-like morphology (equal minima at 2P) does not exclude an ellipsoidally
  modulated spider companion; those stars are unexamined, not cleared.

## Verdict

**No significant excess and no compelling spider identification** in the 15 new
4FGL-DR4 sources searched. The search found **uncatalogued periodic variables** in these
ellipses, the clearest being C01, an SX Phe / δ Sct candidate; none has the multi-
wavelength evidence (X-ray, radio, colour-phase behaviour) needed to propose it as a
pulsar companion.

## Caveats

- Five DR4-new targets were deferred (plane and density cuts).
- Faint black-widow companions (G > 20) are largely beyond ZTF's reach here.
- The compound X-ray tier has low completeness (2/13 known spiders).
- The cadence-systematic periods were identified from off-source fields; the per-field
  veto catches clusters within a field but not single stars sharing a systematic
  period across fields. They are flagged at vetting, not removed from the frozen counts.
- Spider-like counts are overdispersed between fields (index 6.8); the matched-null
  test uses each target's own three nulls, but three fields give a noisy local rate.
