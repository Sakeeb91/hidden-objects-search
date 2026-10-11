You are an independent, adversarial reviewer of a finished astrophysics search. READ-ONLY:
do not modify files. You may run read-only Python (`.venv/bin/python -c ...`) on the
committed results and the cached data in data/ (gitignored, present locally).

Read: PROJECT.md, DECISIONS.md, docs/trackA_spider_report.md, docs/trackB_selflensing_report.md,
docs/review/RESPONSE_TO_REVIEWS.md, pipeline/a05_calibrate.py, pipeline/a06_targets.py,
pipeline/a07_injection.py, pipeline/a08_vet_candidates.py, pipeline/a09_followup_c01.py,
src/hos/period.py, src/hos/stats.py, results/trackA/*.

Questions:
1. Is the headline "no spider candidate; 30 spider-like vs 35.0 expected; 0 X-ray" supported?
   Recompute the population-level comparison yourself from a05/a06 outputs with an
   appropriate test (account for overdispersion between fields; per-target matched nulls).
   What is the 95% upper limit on the number of spider companions (detectable at the
   injection-recovery completeness) among the 15 targets?
2. Was the freeze honoured? Check git history order (calibration commit before any a06
   output; code hashes in the frozen JSON vs current files). Note DECISIONS entries made
   after looking at calibration (common-period veto, band agreement) - are any of them
   post-hoc relative to targets?
3. Injection-recovery: is it representative (pool of null-field sources, magnitude
   distribution vs known spider companions G~15-21, period distribution, injection on top of
   intrinsically variable stars)? Is "complete for redbacks brighter than G~19.5" justified?
4. C01 vetting: is the SX Phe conclusion and the Gaia distance bound (parallax -0.69 +- 0.21,
   inflated x1.3, 3 sigma) sound? Could a negative parallax that is -3.2 sigma indicate a
   bad astrometric solution (check RUWE etc. in results/trackA/a09_c01_followup.json), and
   does that weaken the argument? Any other test that would separate SX Phe from a
   black-widow companion with existing public data?
5. Overstatements or errors anywhere in either report.
End with a prioritised list of required changes (max 8). Be quantitative and concise.
