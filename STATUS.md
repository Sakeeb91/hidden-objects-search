# STATUS.md

## 2026-10-09 (evening)

**Done:**
- Foundation docs, uv environment, archive helpers, CI (offline tests).
- **Track B (self-lensing): complete, negative.** After two independent reviews, all 17
  flag-free inverted signals are excluded under circular orbits (16 by calibrated Gaia RV
  probabilities, familywise ≤ 0.003; the former survivor by the mass-aware duration test).
  Report: `docs/trackB_selflensing_report.md`.
- **Track A design** (spider pulsars in 4FGL-DR4-new unassociated sources): fields,
  period search, X-ray, novelty, statistics, freeze guard, injection stage — all revised
  per `docs/review/RESPONSE_TO_REVIEWS.md`.
- Reviews: `docs/review/REVIEW_CLAUDE_2026-10-09.md`, `REVIEW_CODEX_ASTRA_2026-10-09.md`.

**In progress:** ZTF download for 83 fields (tiled cones; dense fields are slow).

**Next:**
1. a04 period search on control + off-source fields (provenance-checked caches).
2. a05 calibration → commit frozen JSON (cuts + code hashes).
3. a04 on targets → a06 target evaluation → a07 injection-recovery.
4. Report + a second review pass on the Track A results.

**Blockers:** IRSA throughput only.
