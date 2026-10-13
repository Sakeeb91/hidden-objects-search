# Kickoff prompt for the next Claude Code session (Track A2)

Paste everything between the lines into a new Claude Code session started in
`/Users/sakeeb/Code repositories/Astrophysics`.

---

You are continuing an astrophysics project in this repository (GitHub:
Sakeeb91/hidden-objects-search). A previous session built and completed Track A1 (a
search for spider-pulsar companions in 15 unassociated Fermi-LAT sources new in
4FGL-DR4, using ZTF light curves, matched off-source null fields, blind known-spider
controls and a calibration frozen before targets were examined) and Track B. Both ended
with negative results after three independent reviews.

Your task: **Track A2 — extend the identical spider search to the unassociated 4FGL
sources first released in DR1–DR3** (about 150 targets with the A1 cuts, ~600 fields
including 3 matched nulls per target).

Before doing anything else:
1. Read `docs/handoff/2026-10-13_trackA2_handoff.md` in full — it contains the sample
   sizing, compute budget, implementation plan, and a list of pitfalls that each cost hours
   last time.
2. Then read `AGENTS.md`, `PROJECT.md`, `STATUS.md`, `DECISIONS.md` and
   `docs/trackA_spider_report.md`. Skim `docs/review/RESPONSE_TO_REVIEWS.md`.
3. Run `uv sync && uv run pytest -q -m "not network"` and `git log --oneline | head` to
   confirm the starting state (tag `trackA1-final`).

Then propose a short plan (scope decisions: p_psr threshold, whether to include the 5
deferred DR4 targets, run parametrisation vs copied stages, batching) and ask me to
confirm the scope before fetching data. After I confirm, proceed autonomously.

Non-negotiable rules (also in AGENTS.md):
- Freeze before looking: controls + off-source fields → calibrate → commit the frozen JSON
  (cuts + code hashes) → only then run targets. Any design change must come from nulls or
  controls only and be recorded in DECISIONS.md.
- Every guard must be able to fail; empty inputs never count as a pass; re-derive numbers
  from raw outputs, not summaries.
- Atomic commits pushed to `origin main` after each logical change; check CI with
  `gh run list` after pushing and fix anything red.
- Long jobs (ZTF fetch, period search) run in the background with a single completion
  notification; they are resumable from caches if a session is closed.
- Honest language: "no significant excess / no compelling identification", "candidate" at
  most. No submissions to external services without my explicit go-ahead.
- When results are in, run an independent read-only audit with Codex GPT-6-Astra at xhigh
  (exact command in the handoff), save it verbatim in `docs/review/`, and respond to every
  finding before declaring A2 done.

---
