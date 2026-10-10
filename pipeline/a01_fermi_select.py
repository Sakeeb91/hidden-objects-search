"""Track A stage 1: choose the gamma-ray error ellipses to search.

Primary sample: unassociated 4FGL-DR4 sources first released in DR4 (not covered by
the DR3 ZTF search of Lu et al. 2024), north of the ZTF limit, with clean catalog
flags and a usable 95% ellipse. Each is scored for pulsar-likeness. All cuts are
constants below and are fixed before any optical data is looked at.

Writes results/trackA/a01_targets.csv (all DR4-new unassociated sources with cut flags
and scores) and results/trackA/a01_classifier.json.
Usage: uv run python pipeline/a01_fermi_select.py
"""
import json

import numpy as np

from hos import fermi
from hos.paths import RESULTS, ensure

DEC_MIN = -28.0       # ZTF coverage
A95_MAX_DEG = 0.20    # larger ellipses contain too many field stars
P_PSR_MIN = 0.10      # loose: ranks, not a hard classifier decision


def main():
    df = fermi.load_4fgl()
    model, auc = fermi.train_classifier(df)
    df["p_psr"] = fermi.p_pulsar(model, df)

    un = df[df["cls"].isin(fermi.UNASSOC_CLASSES) & (df["data_release"] == 4)].copy()
    un["cut_dec"] = un["dec"] > DEC_MIN
    un["cut_flags"] = un["flags"] == 0
    un["cut_a95"] = np.isfinite(un["a95"]) & (un["a95"] <= A95_MAX_DEG)
    un["cut_ppsr"] = un["p_psr"] >= P_PSR_MIN
    un["selected"] = un[["cut_dec", "cut_flags", "cut_a95", "cut_ppsr"]].all(axis=1)
    un = un.sort_values(["selected", "p_psr"], ascending=False)

    out = ensure(RESULTS / "trackA")
    cols = ["name", "ra", "dec", "glat", "a95", "b95", "pa95", "signif", "flags", "p_psr",
            "cut_dec", "cut_flags", "cut_a95", "cut_ppsr", "selected"]
    un[cols].to_csv(out / "a01_targets.csv", index=False, float_format="%.6g")
    labelled = df[df["cls"].isin(fermi.PSR_CLASSES | fermi.AGN_CLASSES)]
    summary = {
        "catalog": fermi.FGL_URL, "cv_auc": auc, "features": fermi.FEATURES,
        "n_labelled_psr": int(labelled["cls"].isin(fermi.PSR_CLASSES).sum()),
        "n_labelled_agn": int((~labelled["cls"].isin(fermi.PSR_CLASSES)).sum()),
        "n_dr4_unassoc": int(len(un)), "n_selected": int(un["selected"].sum()),
        "cuts": {"dec_min": DEC_MIN, "a95_max_deg": A95_MAX_DEG, "p_psr_min": P_PSR_MIN,
                 "flags": 0},
        "cut_counts": {c: int(un[c].sum()) for c in ["cut_dec", "cut_flags", "cut_a95", "cut_ppsr"]},
    }
    (out / "a01_classifier.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print(un[un.selected].head(15)[["name", "dec", "glat", "a95", "p_psr"]].to_string(index=False))


if __name__ == "__main__":
    main()
