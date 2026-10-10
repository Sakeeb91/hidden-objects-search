# Independent review 1 — fresh Claude agent (read-only), 2026-10-09

Reviewer: a separate Claude Code subagent with no access to the main session's reasoning,
instructed to be adversarial, read-only. Scope: all code and docs at commit 9868661+.
Responses are in `RESPONSE_TO_REVIEWS.md`.

## Critical (Track A)

- **C1 (verified)** `pd.read_csv` parses the string `"null"` as NaN, so all 51 null fields in
  `a02_fields.csv` have `kind = NaN` downstream: a05 would keep 0 nulls (λ = NaN), a06 would
  produce NaN p-values silently, a07 would exit, and a03 fetches nulls last.
- **C2 (verified)** `sep.idxmin()` on a numpy array crashes a05 (masking C1).
- **C3 (verified)** `poisson.sf(0, 0.0) == 0`: if the compound statistic has zero null matches,
  any single target match gets p = 0.

## Moderate

- **M1** Freeze guard checks only the JSON; cut constants live in `a05_calibrate.py` and could be
  edited after seeing targets without tripping the guard.
- **M2** Pooled λ ignores per-target ellipse area (47–276 arcmin²) and latitude, λ uncertainty,
  and multiple testing across 17 targets. Use matched nulls / predictive distribution.
- **M3** Blazar confound: unassociated sources are often blazars (X-ray bright, red-noise
  variable); nulls contain no gamma-ray source, so a "variable + X-ray" excess is expected from
  any counterpart. Need coherence across seasons and Gaia astrometry.
- **M4** Controls have ~7× smaller ellipses than targets; ranks overstate sensitivity. J1023
  informed the score design; J1947 (P = 246 h) unrecoverable by construction.
- **M5** Fold amplitude = max−min of 20 bin medians is noise-biased upward (~0.14 mag for faint
  sources); the 0.05 mag cut rejects nothing at the faint end.
- **M6** Baluev FAP assumes white noise; fine as ranking, must not be read as a probability.
- **M7** Track B numbers (excess-noise 76σ, XP RV, neighbour star) not reproducible from code.
- **M8** "Two spectra would settle it" is wrong: two random-phase epochs differ by < 10 km/s 22%
  of the time at K = 42 km/s; K depends on R★ (possibly inflated); a WD lens (with occultation)
  needs ≈ 0.80 M☉ → K ≈ 69 km/s.

## Minor

RV-kill design false-kill rate up to 9% at 5 transits (actual worst case 1.4%, TIC 362506371);
Gaia ID float coercion risk; duration kill ignores eccentricity; "16/17" should be scoped to the
17 flag-free signals; empty fields crash on re-read; single-band sources pass `bands_agree`
automatically; no barycentric correction (~0.07 phase smear at 2 h); SIMBAD-anything-within-3″
is too aggressive a "known" flag and ATNF/TRAPUM not queried; a07 uses per-source baselines;
"1–4 km/s" is 0.8–4.1 km/s.

## Checked OK

Lensing amplitude and inversion; K and sin i ≈ 1; phase-curve prefactors conservative; units and
BTJD; DR2→DR3 cross-match exact; 4FGL PA convention; null placement matched in |b| and eRASS1
coverage (51/51).

## Verdicts

Track B conclusion stands (kill margins 5–190×) after fixing M7, M8 and scope wording.
Track A not ready: C1–C3 and M1 must be fixed; replace pooled Poisson with matched nulls (M2);
add a blazar discriminator (M3) before interpreting any excess as spiders.
