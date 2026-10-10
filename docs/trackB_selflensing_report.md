# Track B: self-lensing quick look (2026-10-09)

## Question

The reference TESS project flipped 526 light curves upside down and searched them for
dips. That is a search of the original data for periodic **brightenings**, which is
what a white dwarf, neutron star or black hole produces when it passes in front of its
star (self-lensing). The reference used this only as a false-alarm baseline. Could any
of its 17 flag-free "inverted" signals be a real compact companion?

**Scope.** Only 17 of the reference's 1,114 inverted signals passed its planet-oriented
flags; signals removed by flags such as `long_duration`, and pulses clipped by its 10σ
outlier rule, were never examined here. The screen tests a companion of the *target*
star; a blended neighbour producing the signal is not covered.

## Method

`pipeline/b01_selflens_quicklook.py` and `pipeline/b02_survivor_phasecurve.py`.

1. Invert the brightening amplitude for the **minimum** lens mass (pure lensing; a white
   dwarf also blocks light, which only raises the required mass — `src/hos/selflens.py`,
   tested against KOI-3278).
2. **Kill K1:** pulse longer than a central crossing for the star's density.
3. **Kill K2:** that mass forces a radial-velocity semi-amplitude K on the star. If Gaia
   DR3 measured the star's RV over ≥5 transits and its robust RV amplitude is below
   K (half the predicted peak-to-peak), the companion is excluded.
4. For survivors, fit Doppler beaming (at P) and ellipsoidal variation (at P/2) jointly
   with per-segment trends; calibrate on trial periods near P; inject the prediction.

## Result

| Outcome | Count |
|---|---|
| Excluded by Gaia RVs (needed K = 21–149 km/s; Gaia robust RV amplitude 0.8–4.1 km/s) | 16 |
| Also failed the duration test | 2 of those 16 |
| Not excluded | 1 |

**Survivor: TIC 243307945 signal 3 (CD-41 7984), P = 6.2698 d, +102 ± 13 ppm, 4.8 h.**

All numbers in this section are produced by `pipeline/b03_survivor_context.py`
(`results/trackB/243307945_context.json`).

- Gaia DR3 has no RV for it; RUWE 2.08 and astrometric excess noise at 76σ indicate an
  unresolved companion of *some* kind (a stellar binary would do this too).
- The only other archival RV (Gaia XP spectra, VizieR J/A+A/684/A29) is −84 ± 330 km/s:
  uninformative.
- Phase curve: predicted beaming 451 ppm and ellipsoidal 161 ppm; the TESS null at
  periods near 6.3 d has median amplitudes of 610 and 83 ppm. **The test is not
  sensitive enough at this period** ("untested", not "consistent").
- Its detection statistic (SDE 7.86) sits inside the distribution the reference
  project used as noise (max flag-free inverted SDE 8.38). Statistically it is
  indistinguishable from a false alarm.
- A G = 15.5 background star 6.8″ away (Gaia DR3 epoch 2016) contributes 0.40% of the
  G-band flux and could mimic a ~100 ppm brightening if it varies by a few percent.

## Verdict

No credible self-lensing candidate. The one survivor is untested, not supported.

**Falsifiable prediction.** If the 6.27-d pulse were self-lensing, CD-41 7984 must move
in radial velocity with semi-amplitude **K ≥ 33 km/s** for a neutron-star/black-hole lens
(range 33–42 km/s for R★ = 0.85–1.01 R☉; the TIC radius may be inflated by the unresolved
companion), or **K ≈ 63–67 km/s** for a white-dwarf lens, which must be heavier
(≈ 0.71–0.76 M☉) to overcome its own occultation. Two spectra are *not* enough: at
K = 33 km/s two random-phase epochs show a peak-to-peak below 20 km/s 44% of the time.
**Six spectra at random phases** (or fewer timed near quadrature) bring the chance of
missing a real companion below 1%. A peak-to-peak below 20 km/s across six epochs
would exclude self-lensing on this star.

## Caveats from review

- The RV kill compares Gaia's robust peak-to-peak with K. With few random-phase epochs
  this rule could in principle exclude a real companion; for the actual 16 stars the
  margins are 5–190×, and the reviewer's worst-case false-exclusion probability is
  1.4% (TIC 362506371, 5 RV transits). Independent math audit pending.
- Eccentric orbits could lengthen a pulse; both duration kills also failed the RV test.

## Lessons recorded

- My first phase-curve verdict said "not excluded: power present". The injection
  "recovery" was coincidental because the noise (median 1,100 ppm with long trial
  periods) exceeded the signal. Fixed: a test may only decide when the prediction
  clears the null's 95th percentile; otherwise it reports "untested". Regression tests
  in `tests/test_b02_verdict.py`.
- The reference cleaning step clips brightenings above 10σ per point, so the inverted
  search was blind to large (black-hole-scale) pulses. A dedicated search would need a
  different outlier policy.
