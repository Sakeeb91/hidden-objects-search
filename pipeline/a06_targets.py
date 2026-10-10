"""Track A stage 6: apply the FROZEN calibration to the target ellipses.

Refuses to run unless results/trackA/a05_frozen_calibration.json is committed and
unmodified in git, so thresholds provably predate looking at targets.

For each target ellipse: spider-like periodic sources (same cuts as a05), uniform and
targeted X-ray matches, Gaia DR3 astrometry, and a novelty check (SpiderCat, Lu+2024, SIMBAD,
VSX, ZTF periodic variables of Chen et al. 2020) with the date of the check. Each field's
count is compared with its own
three matched off-source fields (exact conditional binomial) and with all off-source counts
(negative-binomial posterior predictive), Holm-corrected across targets.

Writes results/trackA/a06_candidates.csv and a06_fields.csv.
Usage: uv run python pipeline/a06_targets.py
"""
import datetime as dt
import json
import subprocess

import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord

from a05_calibrate import add_xray, code_hashes, cuts, load, spider_like
from hos import archives as A
from hos import known, stats
from hos.fields import read_fields
from hos.paths import RESULTS, ROOT
from hos.sky import sep_arcsec

FROZEN = RESULTS / "trackA" / "a05_frozen_calibration.json"
NOVELTY_RADIUS = 3.0  # arcsec


def assert_frozen_committed():
    rel = FROZEN.relative_to(ROOT)
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", str(rel)], cwd=ROOT,
                             capture_output=True).returncode == 0
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", str(rel)],
                           cwd=ROOT).returncode == 0
    if not (tracked and clean):
        raise SystemExit("frozen calibration must be committed and unmodified before a06")


def assert_code_matches(frozen: dict):
    """The cuts and search code in use must be exactly those that were frozen."""
    if frozen.get("cuts") != cuts():
        raise SystemExit("cut constants differ from the frozen calibration")
    if frozen.get("code_sha256") != code_hashes():
        raise SystemExit("search/cut code changed since the calibration was frozen")


def _vizier_cone(cat, ra, dec, radius):
    def build():
        import astropy.units as u
        from astroquery.vizier import Vizier

        r = Vizier(columns=["**"], row_limit=20).query_region(
            SkyCoord(ra, dec, unit="deg"), radius=radius * u.arcsec, catalog=cat)
        return r[0].to_pandas() if len(r) else pd.DataFrame()

    return A.cached_frame("novelty", [cat, round(ra, 6), round(dec, 6), radius], build)


def simbad_cone(ra, dec, radius):
    q = ("SELECT b.main_id, b.otype FROM basic AS b WHERE CONTAINS(POINT('ICRS', b.ra, b.dec), "
         f"CIRCLE('ICRS', {ra:.6f}, {dec:.6f}, {radius / 3600:.6f})) = 1")

    def build():
        import io

        import requests

        r = requests.post("https://simbad.cds.unistra.fr/simbad/sim-tap/sync", timeout=120,
                          data={"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": q})
        r.raise_for_status()
        return pd.read_csv(io.StringIO(r.text))

    return A.cached_frame("simbad", [q], build)


def novelty(ra, dec, spiders: pd.DataFrame, lu: pd.DataFrame) -> dict:
    sc = spiders[sep_arcsec(spiders.ra, spiders.dec, ra, dec) < 10.0]
    lc = lu[sep_arcsec(lu.ra, lu.dec, ra, dec) < NOVELTY_RADIUS]
    sim = simbad_cone(ra, dec, NOVELTY_RADIUS)
    vsx = _vizier_cone("B/vsx/vsx", ra, dec, NOVELTY_RADIUS)
    chen = _vizier_cone("J/ApJS/249/18/table2", ra, dec, NOVELTY_RADIUS)
    return {"spidercat": ";".join(sc["Name"]) if len(sc) else "",
            "lu2024": ";".join(lc["ztf_name"]) if len(lc) else "",
            "simbad": ";".join(f"{a} [{b}]" for a, b in zip(sim.get("main_id", []), sim.get("otype", []))),
            "vsx": ";".join(vsx["Name"].astype(str)) if "Name" in vsx else "",
            "ztf_chen2020": ";".join(chen["ID"].astype(str)) if "ID" in chen else ""}


def gaia_params(ra, dec) -> dict:
    q = ("SELECT TOP 1 source_id, phot_g_mean_mag, bp_rp, parallax, parallax_over_error, ruwe, "
         "pmra, pmdec, phot_variable_flag, DISTANCE(ra, dec, %f, %f) * 3600 AS sep "
         "FROM gaiadr3.gaia_source WHERE 1 = CONTAINS(POINT(ra, dec), CIRCLE(%f, %f, %f)) "
         "ORDER BY sep" % (ra, dec, ra, dec, 1.5 / 3600))
    g = A.gaia_query(q, "gaia_cand")
    return {f"gaia_{k}": v for k, v in g.iloc[0].to_dict().items()} if len(g) else {"gaia_source_id": None}


def main():
    assert_frozen_committed()
    frozen = json.loads(FROZEN.read_text())
    assert_code_matches(frozen)

    fields = read_fields()
    tf = fields[fields.kind == "target"]
    d = load(tf)
    cand = add_xray(d[spider_like(d)].copy())
    spiders = known.spidercat()
    today = dt.date.today().isoformat()
    lu = known.lu2024()
    extra = [novelty(r.ra, r.dec, spiders, lu) | gaia_params(r.ra, r.dec) for r in cand.itertuples()]
    cand = pd.concat([cand.reset_index(drop=True), pd.DataFrame(extra)], axis=1)
    cand["novelty_checked"] = today
    cand["known"] = (cand[["spidercat", "lu2024", "simbad", "vsx", "ztf_chen2020"]].fillna("") != "").any(axis=1)
    cand = cand.sort_values(["xray_uniform", "score"], ascending=False)
    cand.to_csv(RESULTS / "trackA" / "a06_candidates.csv", index=False, float_format="%.7g")

    counts = frozen["null_counts"]
    n_null_fields = len(counts)
    per = []
    for f in tf.itertuples():
        c = cand[cand.field == f.field]
        mine = [v for v in counts.values() if v["parent"] == f.parent]
        xr = c["xray_uniform"].to_numpy(bool) if len(c) else np.array([], bool)
        rec = {"field": f.field, "n_matched_nulls": len(mine)}
        for level, mask in (("spider_like", np.ones(len(c), bool)), ("spider_like_xray", xr)):
            y = int(mask.sum())
            c_local = sum(v[level] for v in mine)
            c_total = sum(v[level] for v in counts.values())
            rec.update({f"{level}_n": y, f"{level}_matched_null_n": c_local,
                        f"{level}_p_matched": stats.matched_binomial_p(y, c_local, len(mine)),
                        f"{level}_p_pooled_nb": stats.nb_predictive_p(y, c_total, n_null_fields)})
        per.append(rec)
    per = pd.DataFrame(per)
    for level in ("spider_like", "spider_like_xray"):
        for kind in ("matched", "pooled_nb"):
            per[f"{level}_p_{kind}_holm"] = stats.holm(per[f"{level}_p_{kind}"])
    per.to_csv(RESULTS / "trackA" / "a06_fields.csv", index=False, float_format="%.4g")
    tot, tot_x = per["spider_like_n"].sum(), per["spider_like_xray_n"].sum()
    exp = sum(v["spider_like"] for v in counts.values()) * len(tf) / n_null_fields
    exp_x = sum(v["spider_like_xray"] for v in counts.values()) * len(tf) / n_null_fields
    print(f"targets: {tot} spider-like (null-scaled expectation {exp:.1f}); "
          f"{tot_x} with uniform X-ray (expectation {exp_x:.2f})")
    print(per.to_string(index=False))
    cols = ["field", "ra", "dec", "period_d", "score", "g_mag", "g_amp", "xray_uniform", "xray_any",
            "known", "simbad", "vsx", "gaia_parallax", "gaia_bp_rp"]
    print(cand[[c for c in cols if c in cand]].to_string(index=False))


if __name__ == "__main__":
    main()
