"""Track A stage 5: calibrate on null and control fields ONLY, then freeze.

Spider-like periodic source (cuts fixed here on physical grounds, not tuned):
  inside the 95% ellipse; periodogram peak 1-36 h (SpiderCat orbits are 2-17 h and an
  ellipsoidal companion peaks at P_orb/2, so the floor is 1 h); bands agree; folded amplitude >= AMP_MIN in some band; score >= S_MIN.

Null fields give the background rate lambda(S): spider-like periodic stars per ellipse
that have nothing to do with a gamma-ray source. Controls give blind recovery: the rank
of each true companion among all in-ellipse sources.

This stage refuses to read target fields. Its output JSON is committed BEFORE a06 runs.
Usage: uv run python pipeline/a05_calibrate.py
"""
import json

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

from hos import xray
from hos.fields import read_fields
from hos.paths import DATA, RESULTS
from hos.sky import in_ellipse, sep_arcsec

PERIOD_MIN_D, PERIOD_MAX_D = 1 / 24, 36 / 24
AMP_MIN = 0.05
S_MIN = 5.0
S_LEVELS = [5.0, 8.0, 12.0, 20.0, 40.0]
MATCH_ARCSEC = 2.0
PERIODS = DATA / "trackA" / "periods"


def load(fields: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for f in fields.itertuples():
        p = PERIODS / f"{f.field}.csv"
        if not p.exists():
            raise FileNotFoundError(f"period table missing for {f.field}; run a04 first")
        d = pd.read_csv(p)
        if d.empty:
            continue
        d["inside"] = in_ellipse(d.ra, d.dec, f.ra, f.dec, f.a95, f.b95, f.pa95)
        d["kind"] = f.kind
        frames.append(d)
    return pd.concat(frames, ignore_index=True)


def spider_like(d: pd.DataFrame, s_min=S_MIN) -> pd.Series:
    amp = d.reindex(columns=["g_amp", "r_amp"]).max(axis=1, skipna=True)  # a band may be absent
    return (d["inside"] & d["bands_agree"] & d["period_d"].between(PERIOD_MIN_D, PERIOD_MAX_D)
            & (amp >= AMP_MIN) & (d["score"] >= s_min))


def add_xray(d: pd.DataFrame) -> pd.DataFrame:
    """Uniform-survey X-ray match for each row (identical for every field kind)."""
    if d.empty:
        return d.assign(xray_uniform=pd.Series(dtype=bool), xray_any=pd.Series(dtype=bool))
    glon = SkyCoord(d["ra"].to_numpy(), d["dec"].to_numpy(), unit="deg").galactic.l.deg
    m = [xray.matches(r, de, gl) for r, de, gl in zip(d["ra"], d["dec"], glon)]
    return d.assign(xray_uniform=[x["uniform_match"] for x in m],
                    xray_any=[x["any_match"] for x in m])


def period_match(p, true_p, tol=0.01):
    return any(abs(p / (true_p * k) - 1) < tol for k in (1.0, 0.5, 2.0))


def main():
    fields = read_fields()
    fields = fields[fields["kind"].isin(["offsource", "control"])]  # never targets here
    d = load(fields)

    null_fields = fields[fields.kind == "offsource"]
    if null_fields.empty:
        raise SystemExit("no off-source fields: refusing to calibrate")
    nd = d[d.kind == "offsource"]
    per_field = {s: nd[spider_like(nd, s)].groupby("field").size()
                 .reindex(null_fields.field, fill_value=0) for s in S_LEVELS}
    lam = {str(s): {"mean_per_ellipse": float(v.mean()), "frac_fields_with_any": float((v > 0).mean())}
           for s, v in per_field.items()}
    # Compound statistic: spider-like AND a uniform-survey X-ray source at the position
    nsl = add_xray(nd[spider_like(nd)])
    nx = nsl[nsl["xray_uniform"]].groupby("field").size().reindex(null_fields.field, fill_value=0)
    lam_x = {"mean_per_ellipse": float(nx.mean()), "n_total": int(nx.sum()),
             "frac_fields_with_any": float((nx > 0).mean())}
    nsl.to_csv(RESULTS / "trackA" / "a05_null_spider_like.csv", index=False, float_format="%.7g")

    rows = []
    for c in fields[fields.kind == "control"].itertuples():
        cd = d[d.field == c.field]
        if cd.empty:
            rows.append({"field": c.field, "status": "no_sources"})
            continue
        sep = pd.Series(sep_arcsec(cd.ra, cd.dec, c.true_ra, c.true_dec), index=cd.index)
        rec = {"field": c.field, "type": c.true_type, "true_p_d": c.true_pb_h / 24,
               "n_inside": int(cd.inside.sum())}
        if sep.min() > MATCH_ARCSEC:
            rec["status"] = "companion_not_in_ztf_table"
        else:
            m = cd.loc[sep.idxmin()]
            ranked = cd[cd.inside].sort_values("score", ascending=False).reset_index()
            rank = int(np.flatnonzero(ranked["index"] == sep.idxmin())[0] + 1) if m.inside else -1
            sl = bool(spider_like(cd.loc[[sep.idxmin()]]).iloc[0])
            xr = add_xray(cd.loc[[sep.idxmin()]])
            rec.update({"status": "found", "score": float(m.score), "period_d": float(m.period_d),
                        "period_ok": period_match(m.period_d, c.true_pb_h / 24),
                        "rank_by_score": rank, "spider_like": sl,
                        "xray_uniform": bool(xr["xray_uniform"].iloc[0]),
                        "xray_any": bool(xr["xray_any"].iloc[0]),
                        "n_spider_like_in_field": int(spider_like(cd).sum())})
        rows.append(rec)
    ctrl = pd.DataFrame(rows)
    ctrl.to_csv(RESULTS / "trackA" / "a05_controls.csv", index=False, float_format="%.6g")

    frozen = {
        "frozen_before_targets": True,
        "cuts": {"period_min_d": PERIOD_MIN_D, "period_max_d": PERIOD_MAX_D, "amp_min_mag": AMP_MIN,
                 "s_min": S_MIN, "bands_agree": True, "inside_95pct_ellipse": True},
        "n_null_fields": int(len(null_fields)),
        "null_rate_by_score": lam,
        "null_rate_spider_like_with_uniform_xray": lam_x,
        "controls": {"n": int(len(ctrl)),
                     "found": int((ctrl.status == "found").sum()),
                     "period_ok": int(ctrl.get("period_ok", pd.Series(dtype=bool)).fillna(False).sum()),
                     "spider_like": int(ctrl.get("spider_like", pd.Series(dtype=bool)).fillna(False).sum()),
                     "rank1": int((ctrl.get("rank_by_score", pd.Series(dtype=float)) == 1).sum())},
    }
    (RESULTS / "trackA" / "a05_frozen_calibration.json").write_text(json.dumps(frozen, indent=2))
    print(json.dumps(frozen, indent=2))
    print(ctrl.to_string(index=False))


if __name__ == "__main__":
    main()
