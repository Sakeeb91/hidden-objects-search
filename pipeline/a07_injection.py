"""Track A stage 7: injection-recovery sensitivity on real null-field light curves.

Fake spider modulations are added to real ZTF light curves (real cadence, gaps and
noise) of sources in the null fields: an irradiation-like sinusoid at P, or an
ellipsoidal-like signal at P/2, with P log-uniform in 2-24 h and fixed amplitudes.
The identical search (hos.period) and the frozen spider-like cuts decide recovery.

Writes results/trackA/a07_injection.csv (summary by amplitude and magnitude).
Usage: uv run python pipeline/a07_injection.py [N_PER_AMP] [WORKERS]
"""
import sys
from multiprocessing import Pool

import numpy as np
import pandas as pd

from a05_calibrate import period_match, spider_like
from hos import period as P
from hos import ztf
from hos.fields import read_fields
from hos.paths import RESULTS

AMPS = [0.02, 0.05, 0.1, 0.2, 0.4]   # semi-amplitude, mag
ORBIT_MIN_D, ORBIT_MAX_D = 2 / 24, 1.0   # injected orbital periods (spider range)
SEED = 7


def pool_sources(n_fields=51):
    fields = read_fields()
    out = []
    for f in fields[fields.kind == "offsource"].field[:n_fields]:
        p = ztf.CACHE / f"{f}.csv.gz"
        if not p.exists():
            continue
        lc = pd.read_csv(p)
        if lc.empty:
            continue
        lc = P.group_sources(lc)
        for src, g in lc.groupby("src"):
            if g.groupby("filtercode").size().max() >= P.MIN_POINTS:
                out.append(g)
    return out


def trial(args):
    g, amp, period_d, shape, seed = args
    rng = np.random.default_rng(seed)
    g = g.copy()
    phase = 2 * np.pi * (g["mjd"] / period_d + rng.uniform())
    if shape == "irradiation":
        g["mag"] += amp * np.sin(phase)
    else:  # ellipsoidal: two minima per orbit
        g["mag"] += amp * np.cos(2 * phase)
    freq = P.frequency_grid()  # identical to production (a04)
    r = P.search_source(g, freq)
    if r is None:
        return None
    row = pd.DataFrame([{**r, "inside": True}])
    ok = period_match(r["period_d"], period_d) and bool(spider_like(row).iloc[0])
    return {"amp": amp, "shape": shape, "period_d": period_d, "mag": float(g["mag"].median()),
            "recovered": ok}


def main():
    n_per_amp = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    rng = np.random.default_rng(SEED)
    sources = pool_sources()
    if not sources:
        raise SystemExit("no null-field light curves available; run a03 first")
    jobs = []
    for amp in AMPS:
        for k in range(n_per_amp):
            g = sources[rng.integers(len(sources))]
            p = float(np.exp(rng.uniform(np.log(ORBIT_MIN_D), np.log(ORBIT_MAX_D))))
            shape = "irradiation" if k % 2 == 0 else "ellipsoidal"
            jobs.append((g, amp, p, shape, int(rng.integers(1 << 31))))
    with Pool(workers) as pool:
        res = [r for r in pool.imap_unordered(trial, jobs, chunksize=8) if r is not None]
    df = pd.DataFrame(res)
    df["mag_bin"] = pd.cut(df["mag"], [10, 17, 18, 19, 20, 22])
    summ = (df.groupby(["amp", "shape", "mag_bin"], observed=True)["recovered"]
            .agg(["mean", "size"]).reset_index())
    summ.to_csv(RESULTS / "trackA" / "a07_injection.csv", index=False, float_format="%.3f")
    print(df.groupby(["amp", "shape"])["recovered"].mean().unstack().round(3))
    print(summ.to_string(index=False))


if __name__ == "__main__":
    main()
