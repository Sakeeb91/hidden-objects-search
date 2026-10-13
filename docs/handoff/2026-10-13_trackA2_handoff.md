# Handoff: extend the spider-pulsar search (Track A2)

Written 2026-10-13 at the end of the session that built Tracks A1 and B. Read this, then
`AGENTS.md`, `PROJECT.md`, `DECISIONS.md` and `docs/trackA_spider_report.md`, before
touching code.

## 1. Where things stand

- Repo: `Sakeeb91/hidden-objects-search` (public), local
  `/Users/sakeeb/Code repositories/Astrophysics`. Python 3.12 via `uv`; CI runs
  `uv run pytest -q -m "not network"` on every push (97 tests, all green).
- Tag **`trackA1-final`** marks the fully reviewed state. Track A1's freeze guard
  (`pipeline/a06_targets.py`) checks the cut constants and SHA-256 hashes of
  `pipeline/a05_calibrate.py`, `src/hos/{period,sky,xray,fields}.py` against
  `results/trackA/a05_frozen_calibration.json`. **Editing any of those files means A1
  can only be re-run from the tag.** That is acceptable; record it in DECISIONS.md.
- **Track A1** (15 unassociated sources new in 4FGL-DR4): no significant excess, no
  compelling identification (30 spider-like stars vs 35.0 expected; matched permutation
  p = 0.74; 0 X-ray matches). Controls 8/11 recovered (7/11 rank 1).
- **Track B** (self-lensing): 17/17 excluded under circular orbits. Done; do not touch.
- Three independent reviews and point-by-point responses: `docs/review/`.

## 2. The task: Track A2

Extend the identical, frozen-before-looking search to the **unassociated 4FGL sources
first released in DR1–DR3**. Lu et al. 2024 (arXiv:2412.11616) already searched DR3
unassociated sources with ZTF, so frame A2 as a *re-search* with: ZTF DR24 (more
epochs), calibrated matched nulls, blind controls, uniform X-ray tier, injection-recovery,
Holm/permutation statistics, and novelty checks including Lu+2024's 24 candidates
(`docs/references/lu2024_candidates.csv`).

Sample size with the A1 cuts (Dec > −28°, flags == 0, a95 ≤ 0.2°, |b| > 10°, before the
density cut), measured 2026-10-13:

| p_psr ≥ | DR1–3 targets | (DR4, done) |
|---|---:|---:|
| 0.1 (A1 setting) | 152 | 17 |
| 0.3 | 107 | 6 |
| 0.5 | 78 | 0 |

3 of the 152 ellipses contain a Lu+2024 candidate; median a95 is 0.084° (smaller than
A1's ~0.12°, so fewer stars per field). None is class `unk`.

**Recommendation (decide and record in DECISIONS.md before fetching):** keep p_psr ≥ 0.1
and the other A1 cuts unchanged so A1 and A2 are directly comparable, apply the same
50,000 Gaia/deg² density cut, and keep 3 matched nulls per target. Expect ~150 targets →
~600 fields.

Optional add-on: the 5 deferred DR4 targets (3 at |b| < 10°: J1915.7−0846,
J0705.0+1331, J1745.0−1953; 2 dense: J1801.3+0554, J1920.5+3652). Needs a different data
strategy (HATS only, smaller ellipses or a TAP pre-selection). Do this after A2, separately.

## 3. Compute budget (from A1)

| Step | A1 measurement | A2 estimate (~600 fields) |
|---|---|---|
| ZTF fetch (`a03`, 8–12 workers) | 73 fields in ~6 h wall time; ~7 MB/field | ~1.5–3 days wall time; ~4–5 GB disk (124 GB free) |
| Period search (`a04`) | ~0.5 s/source/core; 40k null sources ≈ 1.5 h on 8 cores | similar per field; overlap with fetch via `data/follow_a04.sh` |
| X-ray lookups (`a05`) | 632 null spider-like × 4 VizieR queries ≈ 30 min (cached) | proportional to spider-like count |
| Injection (`a07`) | 1,500 trials, 3 min on 9 cores | same |

Process **controls + nulls first, calibrate, freeze, commit, then targets**, exactly as A1.
Fetch is resumable (per-field cache); a04 tables carry provenance and recompute on any
code or raw-data change. Use background jobs plus a single completion notification; the
user may close sessions, so after any restart re-check for half-written files
(`gzip -t data/ztf/*.csv.gz`) and tables lacking `.provenance.json`.

## 4. Suggested implementation (atomic commits, one per step)

1. **Run parametrisation.** Add `src/hos/runs.py` (e.g. `RUN = os.environ.get("HOS_RUN",
   "trackA")`, mapping to `results/<run>/`, `data/<run>/periods/`, ZTF cache can stay
   shared in `data/ztf/` since field names are unique). Thread it through a01–a10. This
   edits frozen files; note in DECISIONS.md that A1 is reproducible from `trackA1-final`.
   Alternatively copy the stages to `pipeline/a2_*.py`; parametrisation is cleaner.
2. `a01`: a `--releases 1,2,3` (or run-config) selection; write `results/trackA2/a01_*`.
3. `a02`: build A2 fields with a new seed; reuse the density cut; controls can be the
   same 13 (already cached) — re-searching them is free.
4. `a03` + `a04` on controls and nulls (background; `follow_a04.sh` pattern).
5. `a05` calibrate → inspect null distribution (systematic periods!) → any design change
   from nulls only → re-run → **commit the frozen JSON** (code hashes included).
6. `a04` provenance check on targets → `a06` → commit.
7. `a07` injection (consider weighting the host pool toward G 15–21 and including 1–2 h
   orbits; review 3 criticised both), `a08` vetting, `a10` permutation test → commit.
8. Report `docs/trackA2_spider_report.md`; update README/STATUS.
9. Independent review of results with Codex (see §6); respond point by point; fix.

## 5. Hard-won pitfalls (each cost real time in A1)

- **pandas parses the string `"null"` as NaN**; field kind is now `offsource`. Always read
  the field table with `hos.fields.read_fields()`.
- **`df.flags` is a pandas attribute**, not the column: use `df["flags"]`.
- **19-digit Gaia ids** turn into lossy floats when mixed with None/NaN or taken from a
  mixed-dtype row (`.iloc[0].to_dict()`). Use `hos.archives.exact_int_column` and read
  ids from columns; cache reads use `dtype=str` for ids.
- **IRSA ZTF API** stalls above ~20k Gaia sources/deg² and times out under heavy
  parallel load; `ztf.cone(backend="auto")` falls back to **lsdb on
  `s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats`** (`UPath(..., anon=True)`; passing
  `storage_options` breaks). lsdb is latency-bound: use ~12 workers. Both backends agree
  only after the shared `good_epochs_filter` (API `NOBS_MIN` counts all epochs).
- **Gaia TAP**: use the sync endpoint (`archives.gaia_query`); astroquery async hung. An
  `ORDER BY` on an unselected joined column silently returned zero rows — always guard
  against empty results.
- **Cadence systematics**: high-cadence ZTF fields produce clusters of stars at the same
  period (A1: 0.2516, 0.3365, 0.4897, 0.5072, 0.9619 d). The per-field common-period veto
  handles clusters inside a field; cross-field matches are flagged at vetting.
- **Period precision**: a04 stores periods at 7 significant figures (~0.2 cycles drift over
  the ZTF baseline); a08 refines them. Never fold follow-ups on the stored value.
- **eRASS1 covers only Galactic l > 180°**; elsewhere report "no coverage", never "no
  detection". Swift/XMM are targeted at Fermi sources, so they are vetting-only.
- **Controls have ~7× smaller ellipses than targets**: control ranks overstate
  sensitivity. Report recovery as intersections (period ok AND cuts AND rank 1).
- **Claims**: say "no significant excess / no compelling identification", never "no
  candidate" when survivors exist; efficiencies are conditional, not completeness.
- Commit hook blocks commands containing `-q` after `-m` in some forms; use
  `git commit -q -m "..."`.

## 6. Tools and conventions

- Atomic commits pushed to `origin main`; check `gh run list` after pushes (user's global
  rule: CI must be green before calling anything done).
- Independent math/results audit: **Codex GPT-6-Astra, xhigh, read-only**:
  `codex exec -m gpt-6-astra -c model_reasoning_effort='"xhigh"' -s read-only -C . -o <out.md> - < prompt.md`
  (20–40 min; run in background). Save the output verbatim to `docs/review/` and add a
  section to `RESPONSE_TO_REVIEWS.md`. Previous prompts are in `docs/review/` as templates.
- Status language: "candidate" at most; no submissions to external services (VSX,
  ExoFOP, journals) without the user's explicit go-ahead.

## 7. Definition of done for A2

Frozen calibration committed before any A2 target output; a06/a07/a08/a10 results
committed; `docs/trackA2_spider_report.md` with the same honesty standard as A1; a
Codex results audit with every finding addressed; README/STATUS/DECISIONS updated; CI
green.
