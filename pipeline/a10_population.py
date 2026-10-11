"""Track A stage 10: population-level summary requested by review 3.

1. Exact stratified permutation test. Each target and its three off-source fields form a
   matched quartet; under the null, which member is "the target" is arbitrary. The
   distribution of the summed "target" count is the convolution over quartets of a
   uniform choice among the four counts (exact, no Monte Carlo).
2. Blind-control recovery as intersections (correct period AND every cut, AND rank 1),
   and uniform-survey X-ray matches, recomputed from the per-control table.
3. A conditional upper limit on companions among the targets: assuming at most one
   companion per target and a common detection efficiency eps, N95 is the largest N <= 15
   with P(Binomial(N, eps) <= n_fields_with_survivors) >= 0.05. Efficiencies come from the
   injection summary (ZTF median magnitude 19-20). Illustrative, not a population limit.

Writes results/trackA/a10_population.json.
"""
import json

import numpy as np
import pandas as pd
from scipy.stats import binom

from hos.paths import RESULTS

A = RESULTS / "trackA"


def permutation_test(groups):
    """groups: list of (target_count, [null counts]). Returns observed sum and exact p."""
    dist = {0: 1.0}
    for _, members in groups:
        new = {}
        for s, p in dist.items():
            for c in members:
                new[s + c] = new.get(s + c, 0.0) + p / len(members)
        dist = new
    obs = sum(t for t, _ in groups)
    vals = np.array(sorted(dist))
    probs = np.array([dist[v] for v in vals])
    mean = float((vals * probs).sum())
    p_hi = float(probs[vals >= obs].sum())
    p_lo = float(probs[vals <= obs].sum())
    p_two = float(probs[np.abs(vals - mean) >= abs(obs - mean) - 1e-12].sum())
    return {"observed": int(obs), "expected": mean, "p_excess": p_hi, "p_deficit": p_lo,
            "p_two_sided": p_two}


def n95(eps, k_obs, n_max=15, alpha=0.05):
    ok = [n for n in range(n_max + 1) if binom.cdf(k_obs, n, eps) >= alpha]
    return max(ok) if ok else 0


def main():
    frozen = json.loads((A / "a05_frozen_calibration.json").read_text())
    fields = pd.read_csv(A / "a06_fields.csv")
    nulls = frozen["null_counts"]
    groups, groups_x = [], []
    for f in fields.itertuples():
        parent = "4FGL " + f.field.replace("tgt_", "")
        mine = [v for v in nulls.values() if v["parent"] == parent]
        if len(mine) != 3:
            raise RuntimeError(f"{f.field}: expected 3 matched nulls, found {len(mine)}")
        groups.append((f.spider_like_n, [f.spider_like_n] + [v["spider_like"] for v in mine]))
        groups_x.append((f.spider_like_xray_n,
                         [f.spider_like_xray_n] + [v["spider_like_xray"] for v in mine]))

    ctrl = pd.read_csv(A / "a05_controls.csv")
    ind = ctrl[ctrl["independent"]]
    both = ind["period_ok"].fillna(False).astype(bool) & ind["spider_like"].fillna(False).astype(bool)
    controls = {
        "independent_n": int(len(ind)),
        "period_ok_and_all_cuts": int(both.sum()),
        "period_ok_and_all_cuts_and_rank1": int((both & (ind["rank_by_score"] == 1)).sum()),
        "uniform_xray_all13": int(ctrl["xray_uniform"].fillna(False).astype(bool).sum()),
        "uniform_xray_and_recovered_all13": int((ctrl["xray_uniform"].fillna(False).astype(bool)
                                                 & ctrl["period_ok"].fillna(False).astype(bool)
                                                 & ctrl["spider_like"].fillna(False).astype(bool)).sum()),
    }

    inj = pd.read_csv(A / "a07_injection.csv")
    inj["succ"] = inj["mean"] * inj["size"]
    k_fields = int((fields["spider_like_n"] > 0).sum())
    limits = []
    for amp in (0.2, 0.4):
        s = inj[(inj["amp"] == amp) & (inj["mag_bin"].astype(str) == "(19, 20]")]
        eps = float(s["succ"].sum() / s["size"].sum())
        limits.append({"semi_amplitude_mag": amp, "ztf_mag_bin": "19-20", "efficiency": eps,
                       "n_trials": int(s["size"].sum()),
                       "N95_conditional": n95(eps, k_fields),
                       "N95_with_95pct_containment": n95(0.95 * eps, k_fields)})

    out = {"optical": permutation_test(groups), "optical_plus_uniform_xray": permutation_test(groups_x),
           "fields_with_survivors": k_fields, "controls": controls,
           "conditional_limits": limits,
           "limit_caveat": "assumes <=1 companion per target and a common efficiency; "
                           "with 7 fields containing survivors, no bound below 15 is "
                           "defensible for an unspecified population"}
    (A / "a10_population.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
