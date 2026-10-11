# Track A: spider-pulsar companions in new Fermi-LAT sources (2026-10-10)

## Question

Millisecond pulsars that irradiate or evaporate a close companion ("spiders": black widows
and redbacks) are often found first as unidentified Fermi-LAT gamma-ray sources, then
pinned down by the companion's optical modulation at the orbital period (2–24 h). A
systematic ZTF search of the *previous* catalogue (4FGL-DR3) exists (Lu et al. 2024). Do
the unassociated sources **new in 4FGL-DR4** hide spider companions that ZTF can see?

## What was searched

| | Fields | ZTF sources searched | Inside the 95% ellipse | Area (deg²) |
|---|---:|---:|---:|---:|
| Targets (DR4-new, unassociated, pulsar-like) | 15 | 11,961 | 9,349 | 0.58 |
| Off-source nulls (3 per target, same ellipse) | 45 | 40,436 | 31,874 | 1.75 |
| Known-spider controls (searched blind) | 13 | 2,604 | 2,206 | 0.10 |

Target selection (`a01`): unassociated 4FGL-DR4 sources first released in DR4, Dec > −28°,
clean flags, 95% ellipse ≤ 0.2°, pulsar-likeness ≥ 0.1 (random forest, CV AUC 0.987),
|b| > 10°, and ≤ 50,000 Gaia sources/deg² (five targets deferred: three near the plane,
two too dense for the archive). Light curves: ZTF DR24 (`a03`), one backend per field.

Pipeline: multiband Lomb-Scargle on one fixed grid (0.96 h–2 d), aliases masked
(`a04`); a source is **spider-like** if inside the ellipse, the period is significant in
every band and in both halves of the data, the fitted amplitude is ≥ 0.05 mag at ≥ 5σ,
and its period is not shared by ≥ 3 spider-like stars in the same field. The
**compound** tier also requires an X-ray source from a uniform all-sky survey (eRASS1 or
2RXS). Cuts, null rates and code hashes were frozen and committed (`1554eac`) before any
target was examined; `a06` refuses to run otherwise.

## Calibration (off-source and controls only)

- Spider-like periodic stars per null ellipse: **2.33** (dispersion index 6.8).
- Spider-like **with** a uniform X-ray match: **2 in 45 ellipses** (0.044 per ellipse).
- Blind controls: all 11 independent known companions are in the ZTF tables; **9/11** are
  recovered at the right period (or P/2), pass every cut and rank **first** in their
  field. Misses: transitional pulsar 3FGL J1544.6−1125 (disk state, no coherent orbit),
  J1048+2339 (wrong period), J2129−0429 (coherence 1.3 < 2).
- Only **2/13** known spiders have a uniform-survey X-ray match: the compound tier is
  high-purity but low-completeness.
- Control ellipses are ~7× smaller than target ellipses, so ranks overstate sensitivity.

## Sensitivity (injection-recovery, `a07`)

1,500 irradiation/ellipsoidal signals planted in real off-source light curves:

| Semi-amplitude | G < 18 | 18–19 | 19–20 | > 20 |
|---|---|---|---|---|
| 0.05 mag | ~100% | 50–58% | 15–25% | ~1% |
| 0.10 mag | 100% | 71–85% | 33–48% | 4% |
| 0.20 mag | 90–100% | 76–82% | 69–77% | 23–29% |
| 0.40 mag | 71–100% | 89–100% | 78–90% | 57–66% |

Complete for typical redback companions (0.2–1 mag) brighter than G ≈ 19.5; weak for
black-widow companions fainter than G ≈ 20.

## Result

| | Targets | Expected from matched nulls |
|---|---:|---:|
| Spider-like periodic stars | **30** | 35.0 |
| … with a uniform-survey X-ray match | **0** | 0.67 |
| … with any X-ray match (incl. Swift/XMM) | 0 | — |
| Known pulsar / spider candidate (SpiderCat, Lu+2024, ATNF) | 0 | — |

Per field, the largest excess is 4FGL J1627.0+1035 (7 vs 4 in its three nulls,
matched-binomial p = 0.0076, **Holm-adjusted 0.11**). **No target field shows a
significant excess, and the population of spider-like stars in the ellipses matches the
off-source background.**

## The uncatalogued periodic stars (`a08`, `a09`)

24 spider-like stars in the target ellipses appear in no catalogue checked (SpiderCat,
Lu+2024, ATNF, VSX, ZTF periodic variables of Chen+2020; SIMBAD reported separately;
checked 2026-10-10). Vetting (`results/trackA/a08_vetting.csv`, figures in
`docs/figures/trackA/`):

- 5 have periods that recur among off-source stars (0.2516, 0.3365, 0.4897, 0.5072,
  0.9619 d): cadence systematics.
- 3 look like contact/ellipsoidal binaries (equal minima at 2P); 1 like a pulsator; the
  rest are faint and unclassified.
- **C01** (P = 1.229 h, G = 19.0, BP−RP = 0.43, 4FGL J1627.0+1035 ellipse) was the most
  spider-like (symmetric sinusoid; black widows reach 75-min orbits). It fails the
  spider interpretation: monoperiodic and stable over 2018–2025; Gaia parallax
  −0.69 ± 0.21 mas puts it beyond ~7 kpc (conservative), so M_G ≲ 4.7, more than 6 mag
  brighter than a 1.2-h black-widow companion; no radio (NVSS, FIRST, VLASS, LoTSS) or
  X-ray (eRASS1, 2SXPS, 4XMM) counterpart. Most likely a **halo SX Phe pulsator**.
- C15 (P = 2.46 h, sharp brightenings) has Gaia M_G = 9.2, BP−RP = 2.1: an M dwarf, most
  likely a flaring fast rotator.

## Verdict

**No spider-pulsar candidate in the 15 new 4FGL-DR4 sources searched**, at the
sensitivity above. The search did find **uncatalogued periodic variables** in these
ellipses, the clearest being C01, a probable new SX Phe star; these are ordinary stars,
not the gamma-ray sources.

## Caveats

- Five DR4-new targets were deferred (plane and density cuts).
- Faint black-widow companions (G > 20) are largely beyond ZTF's reach here.
- The compound X-ray tier has low completeness (2/13 known spiders).
- The cadence-systematic periods were identified from off-source fields; the per-field
  veto catches clusters within a field but not single stars sharing a systematic
  period across fields. They are flagged at vetting, not removed from the frozen counts.
- Spider-like counts are overdispersed between fields (index 6.8); the matched-null
  test uses each target's own three nulls, but three fields give a noisy local rate.
