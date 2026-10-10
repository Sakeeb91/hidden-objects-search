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
