# hidden-objects-search

A reproducible search of public archival survey data for astronomical objects that
are in no existing catalog, built to try to prove each signal is *not* real before
calling it a candidate.

- **Track A: spider-pulsar companions.** Optical periodic modulation from Gaia sources
  inside unassociated Fermi-LAT gamma-ray sources (4FGL-DR4), using ZTF light curves.
- **Track B: self-lensing compact companions.** Periodic brightening pulses in TESS
  light curves, which a white dwarf, neutron star or black hole would produce.

**Status:** work in progress. Nothing here is a confirmed discovery. See
[STATUS.md](STATUS.md) for current state and [PROJECT.md](PROJECT.md) for scope.

Inspired by [paraschopra/tess-planet-candidates](https://github.com/paraschopra/tess-planet-candidates);
lessons we design around are in [docs/references/inspiration.md](docs/references/inspiration.md).

## Quick start

```bash
uv sync
uv run pytest -q
```

## License

Code: MIT. Text and figures: CC BY 4.0.
