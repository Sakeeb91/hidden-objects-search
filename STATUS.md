# STATUS.md

## 2026-10-09

**Done:**
- Foundation docs, uv environment, archive helpers.
- Track B (self-lensing quick look): 16/17 reference inverted signals excluded by Gaia
  RVs; 1 untested and statistically consistent with noise. Report:
  `docs/trackB_selflensing_report.md`.
- Track A prior-art check: DR3 already searched (Lu et al. 2024); focus on DR4-new
  unassociated sources (see DECISIONS.md).

**Next (Track A pilot):**
1. `a01` Fermi selection + pulsar-likeness classifier.
2. `a02` ZTF light curves per ellipse (cached).
3. `a03` multiband periodogram + alias masking + light-curve class.
4. Positive controls (known spiders, blind full-ellipse rank) and off-source null on
   ~30 pilot sources; freeze thresholds; commit; then on-source.

**Blockers:** none. arXiv API returned empty results from this machine; web search
used instead for prior art.
