"""Track A stage 9: adversarial follow-up of the most spider-like uncatalogued star (C01).

C01 (4FGL J1627.0+1035 ellipse): symmetric sinusoid, P = 1.229 h, 0.13 mag, G = 19.0,
BP-RP = 0.43. Spider interpretation (black-widow companion, cf. the 75-min PSR
J1653-0158) vs pulsator (SX Phe / delta Sct). Tests:

1. Multi-periodicity: pre-whiten the main frequency (3 harmonics) and search residuals.
2. Coherence over time: frequency and amplitude per ZTF observing season.
3. Distance from Gaia: the parallax bounds the absolute magnitude; a black-widow
   companion at P ~ 1.2 h is intrinsically faint.
4. Radio (NVSS, FIRST, VLASS, LoTSS-DR2) and X-ray (eRASS1, 2SXPS, 4XMM) counterparts.

Writes results/trackA/a09_c01_followup.json.
"""
import json

import astropy.units as u
import numpy as np
import pandas as pd
from astropy.coordinates import SkyCoord
from astropy.timeseries import LombScargle

from hos import archives as A
from hos import period as P
from hos import ztf
from hos.paths import RESULTS

FIELD = "tgt_J1627.0+1035"
CATALOGS = {"NVSS": "VIII/65/nvss", "FIRST": "VIII/92/first14", "VLASS": "J/ApJS/255/30/comp",
            "LoTSS-DR2": "J/A+A/659/A1", "eRASS1": "J/A+A/682/A34/erass1-m",
            "2SXPS": "IX/58/2sxps", "4XMM-DR13": "IX/69/xmm4d13s"}


def light_curve():
    v = pd.read_csv(RESULTS / "trackA" / "a08_vetting.csv").set_index("id").loc["C01"]
    cand = pd.read_csv(RESULTS / "trackA" / "a06_candidates.csv")
    r = cand[(cand.field == FIELD) & (cand.src == int(v.src))].iloc[0]  # match on source id
    lc = P.group_sources(pd.read_csv(ztf.CACHE / f"{FIELD}.csv.gz"))
    g = lc[lc["src"] == r.src].copy()
    g["y"] = g["mag"] - g.groupby("oid")["mag"].transform("median")
    return float(r.ra), float(r.dec), float(1 / v.period_d), g


def prewhiten(g, f0):
    out = {}
    freq = P.frequency_grid()
    ok = P.alias_mask(freq)
    for b, s in g.groupby("filtercode"):
        t, y, dy = s["mjd"].to_numpy(), s["y"].to_numpy(), s["magerr"].to_numpy()
        ph = 2 * np.pi * t * f0
        X = np.column_stack([np.ones_like(t)] + [fn(k * ph) for k in (1, 2, 3) for fn in (np.sin, np.cos)])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        res = y - X @ beta
        ls = LombScargle(t, res, dy)
        pw = np.where(ok, ls.power(freq, method="fast"), 0)
        i = int(pw.argmax())
        fap = ls.false_alarm_probability(pw[i], method="baluev", minimum_frequency=P.F_MIN,
                                         maximum_frequency=P.F_MAX)
        out[b] = {"n": int(len(t)), "residual_peak_cd": float(freq[i]),
                  "residual_peak_over_f0": float(freq[i] / f0), "residual_fap": float(fap),
                  "residual_rms": float(res.std()), "median_err": float(np.median(dy))}
    return out


def seasons(g, f0):
    out = []
    g = g.assign(season=np.floor((g["mjd"] - 58119) / 365.25).astype(int) + 2018)  # 2018-01-01
    for yr, s in g.groupby("season"):
        if len(s) < 60:
            continue
        f = np.linspace(f0 - 0.03, f0 + 0.03, 6000)
        pw = LombScargle(s["mjd"], s["y"], s["magerr"]).power(f)
        fb = f[pw.argmax()]
        ph = 2 * np.pi * s["mjd"] * fb
        X = np.column_stack([np.ones(len(s)), np.sin(ph), np.cos(ph)])
        b, *_ = np.linalg.lstsq(X, s["y"], rcond=None)
        out.append({"season": int(yr), "n": int(len(s)), "f_cd": float(fb),
                    "semi_amp_mag": float(np.hypot(b[1], b[2]))})
    return out


def gaia(ra, dec):
    q = ("SELECT source_id, phot_g_mean_mag, bp_rp, parallax, parallax_error, pmra, pmdec, "
         "pmra_error, pmdec_error, ruwe FROM gaiadr3.gaia_source WHERE 1=CONTAINS(POINT(ra,dec),"
         f"CIRCLE({ra},{dec},{2 / 3600}))")
    d = A.gaia_query(q, "a09_gaia")
    if d.empty:
        raise RuntimeError("no Gaia counterpart for C01")
    r = d.iloc[0].to_dict()
    r["source_id"] = int(d["source_id"].iloc[0])
    # Conservative bound: errors inflated x1.3 (Gaia DR3 underestimates faint-star parallax
    # errors), 3-sigma, and a 0.1 mas floor so a negative parallax never gives d = infinity.
    plx_ub = max(r["parallax"] + 3 * 1.3 * r["parallax_error"], 0.1)
    r["parallax_upper_conservative_mas"] = plx_ub
    r["distance_lower_kpc"] = 1 / plx_ub
    r["abs_G_upper_bound"] = r["phot_g_mean_mag"] + 5 * np.log10(plx_ub / 100.0)
    r["abs_G_bw_reference"] = 11.3  # PSR J1653-0158 companion (75-min orbit), G ~ 20.9 at ~0.84 kpc
    r["pm_total_masyr"] = float(np.hypot(r["pmra"], r["pmdec"]))
    r["pm_snr"] = r["pm_total_masyr"] / float(np.hypot(r["pmra_error"], r["pmdec_error"]))
    return r


def counterparts(ra, dec, radius=30.0):
    from astroquery.vizier import Vizier

    c = SkyCoord(ra, dec, unit="deg")
    out = {}
    for name, cat in CATALOGS.items():
        res = Vizier(row_limit=5).query_region(c, radius=radius * u.arcsec, catalog=cat)
        out[name] = int(sum(len(t) for t in res))
    return out


def main():
    ra, dec, f0, g = light_curve()
    rec = {"id": "C01", "field": FIELD, "ra": ra, "dec": dec, "f0_cd": f0, "period_h": 24 / f0,
           "prewhitening": prewhiten(g, f0), "seasons": seasons(g, f0), "gaia": gaia(ra, dec),
           "counterparts_within_30arcsec": counterparts(ra, dec)}
    (RESULTS / "trackA" / "a09_c01_followup.json").write_text(
        json.dumps(rec, indent=2, default=float))
    print(json.dumps(rec, indent=1, default=float))


if __name__ == "__main__":
    main()
