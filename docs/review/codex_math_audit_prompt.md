You are an independent mathematical and statistical auditor for an astrophysics search
pipeline. You are in a READ-ONLY sandbox: do not modify files. Read the code, re-derive the
math yourself, and run small read-only Python checks if useful (`.venv/bin/python -c ...`).

Read first: PROJECT.md, AGENTS.md, DECISIONS.md, docs/trackB_selflensing_report.md,
src/hos/selflens.py, pipeline/b01_selflens_quicklook.py, pipeline/b02_survivor_phasecurve.py,
src/hos/period.py, pipeline/a05_calibrate.py, pipeline/a06_targets.py, pipeline/a07_injection.py,
results/trackB/*.

Audit these specific questions. For each: give your own derivation or calculation, a verdict
(correct / wrong / approximately right with caveat), and if wrong, the corrected formula and
the numerical effect on the project's results.

1. Self-lensing amplitude. Is the fractional brightening for a point lens (Einstein radius
   R_E = sqrt(4 G M a)/c, lens-source distance a, observer at infinity) crossing a uniform
   stellar disk with R_E << R* equal to 2 (R_E/R*)^2? What changes with limb darkening and
   with impact parameter b > 0? Does using the central-crossing, uniform-disk formula make
   the minimum lens mass (implied_lens_mass) an over- or under-estimate? Check the
   KOI-3278 test numbers.
2. Track B kill K2: a companion of minimum mass m forces RV semi-amplitude K. The code
   excludes the companion if Gaia DR3 rv_amplitude_robust < 0.5 * 2K with >= 5 RV transits.
   rv_amplitude_robust is the max-minus-min of epoch RVs after outlier rejection. Given
   random orbital phases at N Gaia epochs, what is the probability that the observed
   peak-to-peak is below K (i.e. a false exclusion) for N = 5, 6, 7, 10, 20? Is the kill
   conservative? Also: inclination (self-lensing needs i ~ 90 deg, so sin i ~ 1), Gaia RV
   epochs being combined spectra, and eccentricity. Recompute for the actual 16 excluded
   rows in results/trackB/selflens_quicklook.csv and say which exclusions are solid and
   which are marginal.
3. Doppler beaming and ellipsoidal amplitudes used in b02 (4 alpha K/c with alpha = 0.8;
   alpha_ell (M2/M1)(R/a)^3). Are prefactors right for a ~4700 K star in the TESS band?
   Does this change the "untested" verdict for TIC 243307945?
4. Period-search score: per-band Baluev false-alarm probabilities evaluated at the SHARED
   best frequency of the mean periodogram, then -log10 FAP summed across bands. Is the
   Baluev formula valid when the frequency was chosen to maximise the mean power rather than
   each band's power? Is summing -log10 FAP (Fisher-like) appropriate? How do red noise and
   ZTF's cadence (daily aliasing) bias it? Since the threshold comes from null fields
   anyway, is the score still a valid ranking statistic?
5. Background comparison in a06: lambda (spider-like sources per ellipse) is estimated as
   the mean over 51 null fields (3 per target). Each target field count is compared with
   Poisson(lambda). Account for (a) uncertainty in lambda from 51 fields, (b) overdispersion
   between fields, (c) multiple testing across 17 targets, (d) null fields being copies of
   target ellipse sizes but at different sky positions (stellar density varies with
   latitude). Propose the correct test (e.g. a per-target comparison using its own 3 nulls,
   negative-binomial or posterior-predictive), with formulas.
6. Anything else mathematically wrong or overstated that you find.

Be concise and quantitative. End with a prioritised list of required fixes (max 10 items).
