"""Track A stage 2: define every sky field the optical search will process.

Three kinds, all searched with the identical pipeline:

- target:  the selected DR4-new unassociated ellipses (a01).
- offsource: NULLS_PER_TARGET copies of each target ellipse moved 1.5-3 deg away, clear of
           every 4FGL source. They measure how often a field with no gamma-ray source
           still yields a spider-like periodic star (the false-alarm rate).
- control: known spiders with a 4FGL association and a published orbital period,
           searched blind inside their full 95% ellipse; the true companion's rank
           tests whether the pipeline can find a real one. Never used to set thresholds.

Writes results/trackA/a02_fields.csv. Usage: uv run python pipeline/a02_build_fields.py
"""
import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord

from hos import fermi, known
from hos.paths import RESULTS, ensure

SEED = 20261009
NULLS_PER_TARGET = 3
NULL_OFFSET_DEG = (1.5, 3.0)
NULL_CLEARANCE_DEG = 0.3      # beyond both ellipses' semi-major axes
DEC_MIN = -28.0
CONTROL_GMAG_MAX = 20.0       # when SpiderCat lists g; otherwise a Gaia DR3 match is required
CONTROL_A95_MAX = 0.2
GLAT_MIN = 10.0               # Galactic-plane fields are too dense for the IRSA API;
                              # applied identically to targets, nulls and controls


def null_fields(targets: pd.DataFrame, cat: pd.DataFrame, rng) -> pd.DataFrame:
    allsrc = SkyCoord(cat["ra"].to_numpy() * u.deg, cat["dec"].to_numpy() * u.deg)
    rows = []
    for t in targets.itertuples():
        c0 = SkyCoord(t.ra * u.deg, t.dec * u.deg)
        made, tries = 0, 0
        while made < NULLS_PER_TARGET:
            tries += 1
            if tries > 500:
                raise RuntimeError(f"could not place null fields for {t.name}")
            c = c0.directional_offset_by(rng.uniform(0, 360) * u.deg,
                                         rng.uniform(*NULL_OFFSET_DEG) * u.deg)
            if c.dec.deg <= DEC_MIN or abs(c.galactic.b.deg) <= GLAT_MIN:
                continue
            sep = c.separation(allsrc).deg
            if np.any(sep < cat["a95"].fillna(0.2).to_numpy() + t.a95 + NULL_CLEARANCE_DEG):
                continue
            rows.append({"field": f"null_{t.name.replace('4FGL ', '')}_{made}", "kind": "offsource",
                         "parent": t.name, "ra": c.ra.deg, "dec": c.dec.deg, "a95": t.a95,
                         "b95": t.b95, "pa95": t.pa95})
            made += 1
    return pd.DataFrame(rows)


def control_fields(cat: pd.DataFrame) -> pd.DataFrame:
    sc = known.spidercat()
    bright = sc["gmag"].isna() | (sc["gmag"] < CONTROL_GMAG_MAX)
    sc = sc[(sc["fermi_name"] != "") & sc["pb_h"].notna() & (sc["dec"] > DEC_MIN)
            & sc["has_gaia"] & bright]
    m = sc.merge(cat, left_on="fermi_name", right_on="name", suffixes=("_psr", ""))
    m = m[(m["a95"] <= CONTROL_A95_MAX) & (m["glat"].abs() > GLAT_MIN)]
    return pd.DataFrame({
        "field": "ctrl_" + m["Name"].str.replace("PSR_", ""), "kind": "control",
        "parent": m["name"], "ra": m["ra"], "dec": m["dec"], "a95": m["a95"],
        "b95": m["b95"], "pa95": m["pa95"], "true_ra": m["ra_psr"],
        "true_dec": m["dec_psr"], "true_pb_h": m["pb_h"], "true_type": m["Type"],
        "true_gmag": m["gmag"]})


def main():
    rng = np.random.default_rng(SEED)
    cat = fermi.load_4fgl()
    sel = pd.read_csv(RESULTS / "trackA" / "a01_targets.csv")
    sel = sel[sel["selected"]]
    deferred = sel[sel["glat"].abs() <= GLAT_MIN]
    if len(deferred):
        print("deferred (|b| <= %.0f):" % GLAT_MIN, ", ".join(deferred["name"]))
    sel = sel[sel["glat"].abs() > GLAT_MIN]
    targets = pd.DataFrame({"field": "tgt_" + sel["name"].str.replace("4FGL ", ""),
                            "kind": "target", "parent": sel["name"], "ra": sel["ra"],
                            "dec": sel["dec"], "a95": sel["a95"], "b95": sel["b95"],
                            "pa95": sel["pa95"]})
    nulls = null_fields(sel, cat, rng)
    ctrl = control_fields(cat)
    fields = pd.concat([targets, nulls, ctrl], ignore_index=True)
    if fields["field"].duplicated().any():
        raise RuntimeError("duplicate field names")
    out = ensure(RESULTS / "trackA") / "a02_fields.csv"
    fields.to_csv(out, index=False, float_format="%.6f")
    print(fields.groupby("kind").size().to_string())
    print(ctrl[["field", "true_type", "true_pb_h", "true_gmag", "a95"]].to_string(index=False))


if __name__ == "__main__":
    main()
