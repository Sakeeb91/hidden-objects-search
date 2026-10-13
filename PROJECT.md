# PROJECT.md

## Goal

Search public archival survey data for astronomical objects that appear in no existing
catalog, using a pipeline that tries hard to prove each signal is *not* real before
calling it a candidate. Inspired by
[paraschopra/tess-planet-candidates](https://github.com/paraschopra/tess-planet-candidates)
and the r/ClaudeAI post "I think I found a planet nobody knew existed" (see
`docs/references/inspiration.md`).

Two tracks:

- **Track A — spider-pulsar companions (main).** Millisecond pulsars that irradiate or
  evaporate a low-mass companion (black widows, redbacks) are often first seen as
  unassociated Fermi-LAT gamma-ray sources. The companion star shows optical
  modulation at the orbital period (typically 2–24 h). Search optical light curves of
  every Gaia source inside the error ellipses of pulsar-like, unassociated 4FGL-DR4
  sources for such periodic modulation.
- **Track B — self-lensing compact companions (quick look).** A white dwarf, neutron
  star or black hole orbiting a star magnifies it briefly once per orbit: a periodic
  *brightening* pulse, the mirror image of a transit. The reference project ran exactly
  this search on 526 nearby stars, but only as a false-alarm baseline ("inverted" light
  curves). Revisit those signals as possible astrophysics.

## Scope

In scope: public catalogs and light curves (Fermi-LAT 4FGL-DR4, Gaia DR3, ZTF, TESS,
eROSITA eRASS1, SIMBAD, VSX, ATNF, TOI/CTOI); periodicity searches; injection-recovery;
null surveys; novelty cross-matching; independent review; written reports.

Out of scope: raw radio filterbank searches (TB-scale), proprietary data, claiming
confirmed discoveries, submitting to external services (ExoFOP, journals, Zenodo)
without the user's explicit go-ahead.

## Definition of done

1. A pipeline that reruns end to end from public data with documented commands.
2. Injection-recovery sensitivity and a null-survey false-alarm rate for each track,
   computed from this project's own null runs.
3. A ranked, vetted candidate list (or a calibrated null result), each candidate with a
   dated novelty check against the catalogs above.
4. An independent review (fresh agent session, Claude Science or Codex) and a written
   response to every finding.
5. A plain-language report in `docs/`.

## Profile and stack or methods

Profile: hybrid (research + code). Python 3.12 managed with `uv`
(`pyproject.toml` + `uv.lock`). Key libraries: astropy, astroquery, numpy, scipy,
pandas, matplotlib, lightkurve, wotan. Periodograms: Lomb-Scargle (Track A),
box-least-squares on inverted flux (Track B).

## Working directory

`/Users/sakeeb/Code repositories/Astrophysics` — GitHub remote
`Sakeeb91/hidden-objects-search` (public).

## Layout requirements and directory map

| Path | Purpose |
|---|---|
| `AGENTS.md`, `PROJECT.md`, `STATUS.md`, `DECISIONS.md` | Foundation docs (org-dir) |
| `src/hos/` | Importable library code shared by pipeline stages |
| `pipeline/` | Numbered, runnable stage scripts (`a01_…` Track A, `b01_…` Track B) |
| `tests/` | pytest suite, including deliberate-failure tests for every guard |
| `data/` | Downloaded catalogs/light curves and caches — **gitignored**, re-fetchable |
| `results/` | Small, committed outputs (CSV/JSON summaries, candidate tables) |
| `docs/` | Reports, figures, review notes |
| `docs/references/` | Inspiration notes and external method references |
| `docs/review/` | Independent reviews (verbatim) and point-by-point responses |
| `docs/handoff/` | Session handoff documents and kickoff prompts |
