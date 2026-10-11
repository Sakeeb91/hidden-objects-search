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

`pipeline/b01_selflens_quicklook.py`, `b02_survivor_phasecurve.py`, `b03_survivor_context.py`.

1. Invert the brightening amplitude for the **minimum** lens mass (pure lensing, uniform
   disk; `src/hos/selflens.py`, checked against KOI-3278). A white dwarf also blocks light,
   which only raises the required mass. Review 2 notes limb darkening lowers a *central*
   mass estimate by up to ~18% (K 42 → 36 km/s for the former survivor); the kill margins
   below are far larger than that.
2. **Kill K1 (duration):** a central crossing lasts T = (P/π) arcsin(R★/a), with a from
   Kepler's law using the star's mass **plus** the minimum lens mass. (The first version
   reused the reference's planet-mass ratio; review 2 caught this.) A pulse longer than
   1.3 T is excluded *for a circular orbit*; eccentric orbits can lengthen it.
3. **Kill K2 (Gaia RVs):** the minimum mass forces a semi-amplitude K. From Gaia DR3's
   robust RV range over N transits, compute the probability that a real companion shows
   a range that small at random phases, including Gaia's 3-IQR clipping (exact quadrature
   and Monte Carlo, both matching review 2). Exclude only if the 95% Monte Carlo upper
   bound on that probability, times the 17 signals screened, is below 0.05.
4. Phase curve (beaming at P, ellipsoidal at P/2) for the signal that survived the first
   version of the screen.

## Result

| Outcome (circular orbits) | Count |
|---|---|
| Excluded by Gaia RVs (familywise false-exclusion probability, 95% Monte Carlo upper bound ≤ 0.0034; needed K = 21–149 km/s, Gaia robust ranges 0.8–4.1 km/s) | 16 |
| Excluded by the mass-aware duration test | 4 (3 of them also by RVs) |
| **Not excluded** | **0** |

The weakest RV exclusion is TIC 362506371 (5 RV transits; familywise upper bound 0.0033,
i.e. strong at 95% but not at 3σ). The tail probabilities assume independent random phases; Gaia's
actual epoch times could cluster, which would weaken the stars with few transits.

### The former survivor: TIC 243307945 signal 3 (CD-41 7984)

P = 6.2698 d, +102 ± 13 ppm, 4.8 h. Numbers from `b03_survivor_context.py`
(`results/trackB/243307945_context.json`) and `b01`.

- **Fails the mass-aware duration test:** a central crossing with the minimum companion
  mass lasts 3.21 h; the observed 4.81 h is 1.50× longer. Only an eccentric orbit seen
  near apastron could make this work.
- Gaia DR3 has no RV for it. RUWE 2.08 and astrometric excess noise at 76σ are consistent
  with an unresolved companion but do not establish one.
- The only other archival RV (Gaia XP spectra, VizieR J/A+A/684/A29) is −84 ± 330 km/s.
- Phase curve: with conservative prefactors, predicted beaming 451 ppm and ellipsoidal
  161 ppm against null 95th percentiles of 1,679 and 280 ppm, so "untested". Review 2's
  band-integrated prefactors (563 / 207 ppm) do not change that. Note the injection check
  in b02 is algebraically guaranteed (the injected signal lies in the fit's design matrix)
  and is not a coverage test.
- Its detection statistic (SDE 7.86) was selected from the same inverted sample the
  reference used as noise, so it has no independent significance.
- A G = 15.5 background star 6.8″ away contributes 0.40% of the G-band flux and could
  mimic a ~100 ppm brightening if it varies by a few percent.

## Verdict

**No self-lensing candidate among the 17 flag-free inverted signals** (circular orbits).

If anyone wants to close the eccentric-orbit loophole for CD-41 7984: a self-lensing
companion would force a radial-velocity semi-amplitude **K ≥ 33 km/s** in a circular
orbit (NS/BH lens, R★ = 0.85–1.01 R☉) or **≈ 63–67 km/s** (white-dwarf lens). Two
random-phase spectra are not enough (44% chance of a < 20 km/s range at K = 33 km/s).
Six random-phase spectra suffice for a circular orbit (miss < 1%), but the loophole being
closed *is* eccentricity: with conjunction at apastron and e = 0.8 (K held at 33 km/s), six
spectra miss 4.9% of the time and **twelve** are needed for < 1%
(`results/trackB/243307945_context.json`).

## Caveats

- Circular orbits assumed for K1; Gaia epochs assumed to sample independent phases for K2.
- Limb darkening, dilution by neighbours and the exact BLS depth definition shift the
  implied mass by tens of percent; the RV margins (ranges 1–10% of K) dwarf this.

## Lessons recorded

- My first phase-curve verdict said "not excluded: power present". The injection
  "recovery" was coincidental because the noise (median 1,100 ppm with long trial
  periods) exceeded the signal. Fixed: a test may only decide when the prediction
  clears the null's 95th percentile; otherwise it reports "untested". Regression tests
  in `tests/test_b02_verdict.py`.
- The reference cleaning step clips brightenings above 10σ per point, so the inverted
  search was blind to large (black-hole-scale) pulses. A dedicated search would need a
  different outlier policy.
