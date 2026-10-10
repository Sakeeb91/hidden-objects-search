# AGENTS.md

Read PROJECT.md and STATUS.md before work. The project's goals, required outputs,
directory map and the constraints below determine its folder structure.

## Layout constraints

Preserve working stack-native source, tests, manifests and commands. Add optional
folders only when the project needs them; keep one authoritative home per artifact.

- Library code in `src/hos/`; runnable stages in `pipeline/`; tests in `tests/`.
- Raw downloads and caches go in `data/` (gitignored). Never commit large data.
- Committed results in `results/` must be small (< 5 MB per file) and regenerable.

## Rules and commands

```bash
uv sync                      # create .venv from uv.lock (Python 3.12)
uv run pytest -q             # run tests
uv run python pipeline/<stage>.py   # run a stage
```

### Scientific discipline (lessons from the reference project and its reviews)

1. **Try to prove it isn't.** Every candidate must survive tests designed to kill it.
2. **Calibrate from your own nulls.** False-alarm rates come from null surveys run with
   the identical pipeline (inverted/scrambled light curves, off-source positions).
   Re-check thresholds whenever the null grows. Local SNR is not discovery significance.
3. **Make every check go red once.** Each vetting guard has a test that feeds it a
   known-bad input and asserts it fails. An empty input must never count as a pass.
4. **Re-derive numbers from raw output**, never from an agent-written summary.
5. **Cross-match early.** Check SIMBAD/VSX/ATNF/TOI/known-spider lists before investing
   in a candidate; record the date of every novelty check.
6. **Status language:** "candidate" until independent follow-up. No "discovery" claims.
7. **Freeze selection before looking.** Cuts and thresholds are fixed in code and
   committed before the real (non-null) run is inspected.

### Git

Atomic commits: one logical change per commit (a stage, a test, a doc), pushed to
`origin main`. No secrets in the repo; API keys only via environment variables.
