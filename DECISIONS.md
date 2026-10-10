# DECISIONS.md

## 2026-10-09 — Science targets: spider pulsars (A) + self-lensing quick look (B)

Chosen by the user from four options. Raw radio pulsar searches were rejected as
infeasible (TB-scale filterbank data). Spider-pulsar companions in Fermi unassociated
sources pass all feasibility constraints: downloadable catalog rows and light curves,
cheap novelty cross-match, natural null test (off-source positions), hours of compute.
Self-lensing reuses the reference project's inverted-light-curve search.
Rejected for now: Gaia DR3 dark-companion re-screen (heavily mined; DR4 not yet public),
long-period TESS planets (closest to prior work, least novel for "pulsars/black holes").

## 2026-10-09 — Layout and environment

- Reused the existing empty folder `Code repositories/Astrophysics`; GitHub remote is
  `Sakeeb91/hidden-objects-search` (public).
- org-dir hybrid profile: four foundation docs + `docs/`; stack-native `src/`,
  `pipeline/`, `tests/`; `data/` gitignored; `results/` for small committed outputs —
  mirroring the reference project's layout so its scripts are easy to compare.
- Python 3.12 via `uv` (system Python is 3.14; numba/lightkurve wheels lag).

## 2026-10-09 — Track A framing after prior-art check

A systematic ZTF search of 4FGL-**DR3** unassociated sources already exists
(Lu et al. 2024, ApJ, arXiv:2412.11616: 194 periodic variables → 24 candidates → 9 gold),
as does COBIPULSE (2024) and the SpiderCat compilation (Koljonen & Linares 2025,
VizieR J/ApJ/994/8). Track A is therefore framed as:

1. **Primary sample: unassociated sources new in 4FGL-DR4** (`DataRelease == 4`; 324
   total, 219 at Dec > −28°), which postdate the DR3 search.
2. Current ZTF data release (more epochs than 2024 work).
3. A compound detection statistic (optical periodicity + light-curve class + X-ray
   coincidence) whose false-alarm rate is measured with an off-source null run
   *before* the on-source run; thresholds frozen and committed first.
4. Blind positive controls: full-ellipse recovery of known spiders, reporting rank.
5. Novelty exclusion set: SpiderCat, Lu et al. 2024, COBIPULSE, ATNF, SIMBAD, VSX.

Practical: the IRSA ZTF light-curve API accepts a 0.05° cone (227 objects, 39 s);
larger ellipses are covered with one larger cone per source.

## 2026-10-09 — Period-search score design (informed by one control, not thresholds)

On the first blind control (J1023+0038, flickering disk state) raw Lomb-Scargle power
ranked the true companion 7th of 12, behind faint single-band stars and a 1.035-d
lunar sideband of the daily alias. Changed, on general grounds: mask lunar-month and
yearly sidebands of the daily aliases, and score each source by the summed −log10
Baluev false-alarm probability across bands (accounts for point counts). The companion
then ranks 1st. Controls were used to choose the *form* of the score only; detection
**thresholds will be set from the null fields alone**, before targets are inspected.

## 2026-10-09 — Galactic latitude cut |b| > 10° for the pilot

Plane fields (cones up to 0.2° at |b| < 10°) were too dense for the IRSA light-curve
API (a single field ran > 10 min without finishing). Applied |b| > 10° identically to
targets, null positions and controls. Deferred targets: 4FGL J1915.7−0846,
J0705.0+1331, J1745.0−1953 (to revisit with a TAP pre-selection of ZTF objects).
Also added NOBS_MIN = 40 server-side (objects sparser than the search minimum).

## 2026-10-09 — Stellar-density cut (matched groups)

The IRSA cone API could not serve fields toward the bulge (objects × high-cadence epochs):
a 0.05° tile stalled > 5 min. Fields are now cut at 50,000 Gaia DR3 (G < 20.5) sources
per deg² at the centre. A dense *target* is removed together with its three off-source
fields so every remaining comparison stays matched. Deferred targets: 4FGL J1801.3+0554,
J1920.5+3652 (in addition to the three |b| < 10° targets). Controls removed: J1705−1903,
4FGL J1701.8−2226. Retained positions unchanged.

## 2026-10-09 — Band agreement redefined (before freezing)

Review 1 noted that a g/r pair whose peaks differ by an alias is rejected; a control
(1FGL J0523.5−2529) showed it: g's maximum sat on the daily alias of the true P/2.
"Bands agree" now means the shared-frequency period is independently significant in
each band (−log10 Baluev FAP ≥ 2). Controls informed this design choice, as with the
score form; the detection thresholds are still set only from off-source fields.

## 2026-10-09 — One ZTF backend for every field: DR24 HATS on S3

The IRSA light-curve API timed out on moderately dense fields and returned a different
object count than DR24 HATS for the same cone (27 vs 20 objects with ≥ 40 good epochs,
J1023+0038 field). To keep targets, nulls and controls strictly comparable, all fields use
`lsdb` on `s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats` (heliocentric MJD). Earlier API
downloads were set aside (`data/ztf_api_superseded/`), not mixed in.

**Update (same evening):** the API/HATS object-count mismatch was a filtering artefact:
the API applied NOBS_MIN to all epochs server-side, HATS to good epochs. With one shared
post-filter the backends agree (20/20, 34/34, 17/18 objects; identical rows). Fields now
use the API when sparse (< 20,000 Gaia sources/deg²) and HATS when dense or when the API
fails; each field's backend is recorded. Time columns differ by ≤ 8 min (MJD vs HJD), which
does not matter within a field.
