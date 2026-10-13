# STATUS.md

## 2026-10-10

**Done:**
- **Track B (self-lensing): complete, negative.** All 17 flag-free inverted TESS signals
  excluded under circular orbits. `docs/trackB_selflensing_report.md`.
- **Track A (spider pulsars in 4FGL-DR4-new sources): complete, negative.** 15 targets,
  45 matched off-source fields, 13 blind controls; calibration frozen at `1554eac` before
  targets; 30 spider-like stars vs 35.0 expected, no X-ray counterparts; injection-recovery
  and vetting done; C01 is an SX Phe / δ Sct candidate.
  `docs/trackA_spider_report.md`.
- Two independent reviews of design and maths, with point-by-point responses
  (`docs/review/`). CI green.

**Done:** final results audit (review 3) and all its corrections; headline is "no significant excess, no compelling identification".

**Next (approved by the user 2026-10-13): Track A2** — extend the spider search to
DR1–3 unassociated sources. Handoff: `docs/handoff/2026-10-13_trackA2_handoff.md`;
kickoff prompt: `docs/handoff/KICKOFF_PROMPT_trackA2.md`. Reviewed A1 state is tag
`trackA1-final`.

**Other possible next steps (not started):**
1. Deferred Track A targets (3 near the plane, 2 dense) via a TAP pre-selection.
2. Extend Track A to all 2,563 unassociated/unk 4FGL sources not covered by Lu+2024.
3. Track B: a dedicated self-lensing search without the reference's 10σ clipping.
4. Report C01 to VSX as a new variable star.

**Blockers:** none.
