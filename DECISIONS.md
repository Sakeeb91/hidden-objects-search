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
