# hidden-objects-search

A reproducible search of public archival survey data for astronomical objects that are in
no existing catalogue, built to try to prove each signal is *not* real before calling it a
candidate. Every threshold was frozen before targets were examined, and two independent
reviews (a fresh Claude agent and Codex GPT-6-Astra, three passes in all) audited the
code, the maths and the final claims.

## Results (2026-10-10)

| Track | Question | Result |
|---|---|---|
| **A — spider pulsars** | Do the unassociated Fermi-LAT sources **new in 4FGL-DR4** hide black-widow/redback companions visible in ZTF? | **No significant excess and no compelling identification.** 15 target ellipses: 30 spider-like periodic stars vs 35.0 expected from 45 matched off-source ellipses (matched permutation p = 0.74); none has an X-ray counterpart. Blind recovery of known spiders 8/11 (7/11 also ranked first). Report: [docs/trackA_spider_report.md](docs/trackA_spider_report.md) |
| **B — self-lensing** | Are any periodic *brightenings* in 526 nearby TESS stars (from the reference project) a white dwarf, neutron star or black hole lensing its companion? | **No candidate.** All 17 flag-free signals excluded under circular orbits (16 by Gaia radial velocities, familywise false-exclusion ≤ 0.0034 at 95% Monte Carlo confidence; one by a mass-aware duration test). Report: [docs/trackB_selflensing_report.md](docs/trackB_selflensing_report.md) |

By-product: uncatalogued periodic variables in the Fermi ellipses, notably C01
(P = 1.2287 h), an SX Phe / δ Sct candidate (`results/trackA/a09_c01_followup.json`).

Nothing here is a confirmed discovery.

## Layout

See [PROJECT.md](PROJECT.md) for scope and the directory map, [DECISIONS.md](DECISIONS.md)
for every consequential choice, [STATUS.md](STATUS.md) for state, and `docs/review/` for the
reviews and point-by-point responses.

## Quick start

```bash
uv sync
uv run pytest -q -m "not network"
# Track B
uv run python pipeline/b01_selflens_quicklook.py
# Track A (downloads ZTF light curves; hours)
uv run python pipeline/a01_fermi_select.py && uv run python pipeline/a02_build_fields.py
uv run python pipeline/a03_fetch_ztf.py 8 && uv run python pipeline/a04_period_search.py 10
uv run python pipeline/a05_calibrate.py   # commit its output before the next step
uv run python pipeline/a06_targets.py && uv run python pipeline/a07_injection.py 300
uv run python pipeline/a08_vet_candidates.py && uv run python pipeline/a09_followup_c01.py
uv run python pipeline/a10_population.py
```

Inspired by [paraschopra/tess-planet-candidates](https://github.com/paraschopra/tess-planet-candidates);
lessons are in [docs/references/inspiration.md](docs/references/inspiration.md).

## License

Code: MIT. Text and figures: CC BY 4.0.
