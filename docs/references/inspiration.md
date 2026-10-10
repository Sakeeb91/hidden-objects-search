# Inspiration and lessons

## Sources

- **Repo:** [paraschopra/tess-planet-candidates](https://github.com/paraschopra/tess-planet-candidates)
  — 526 nearby stars, TESS full-frame images, biweight detrending + iterative BLS
  (0.5–25 d), automatic red-flag triage calibrated with injected planets, an
  "upside-down" (inverted) light-curve false-alarm baseline, MCMC fits, hold-out
  seasons, pixel-level difference imaging. Two Earth-sized candidates (TIC 370612437,
  HIP 114417), both tentative.
- **Reddit:** r/ClaudeAI, "I think I found a planet nobody knew existed. I used Claude
  Code to find it." (u/This_Cell_1829, Oct 2026). TIC 4206066: 3.18-d, ~500 ppm,
  ~1.4 R⊕ candidate; hold-out-year test 3/3; 36 catalogs + 340,505 TCE alerts checked;
  TESS DDT program approved; transit times preregistered on Zenodo.

## Lessons we design around

From the reference project's Codex review (`results/review/REVIEW_CODEX.md` there):

| Finding | What we do differently |
|---|---|
| F1: discovery significance uncalibrated; false-alarm numbers extrapolated from 38 scrambles | Repeated complete null surveys with the identical pipeline; report counts, never extrapolated tails |
| F3: pixel probabilities failed a control check | Every statistic is applied to control positions/phases and reported as a rank |
| F5: "never searched" was false | Phrase novelty as "not found in catalogs X, Y, Z checked on date D" |
| F6: BJD formatted as UTC | Explicit time-scale handling with astropy; test it |
| F7: hold-outs overstated | Hold-outs are descriptive; only preregistered future data counts as confirmation |

From the Reddit thread (researcher and practitioner comments):

- "Keep giving it ways to prove that it isn't" — falsify, don't verify.
- **Make every check go red once on purpose**; agents write tests that pass.
- **Price the false-alarm rate from your own null, and re-check it** as the null grows
  (one commenter's threshold silently fell below the null's own maximum).
- **Re-derive numbers from raw output**, never from an agent-written summary.
- **Watch which way a guard fails** — an empty list wired to "pass".
- **Cross-match early** (a candidate turned out to be flagged already by SPOC).
- Derive stellar parameters yourself rather than copying catalog values; a 7.7σ
  stellar-density mismatch killed one candidate.
- The processing matters: the same signal ranked #1 on MIT QLP and outside the top 8
  on SPOC for identical exposures.
- Blends (background eclipsing binaries) are the dominant false positive at 21″ pixels;
  difference-image centroids and contrast limits matter.
