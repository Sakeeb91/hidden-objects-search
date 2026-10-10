"""Track B: reproducible context and a falsification test design for the survivor.

Review 1 (M7) found report numbers with no generating code, and (M8) found the
"two spectra would settle it" claim wrong. This stage derives every survivor number
from raw queries and designs the radial-velocity test properly:

- K for the minimum lens mass over a range of stellar radii (the TIC radius may be
  inflated by an unresolved companion), for a pure lens (NS/BH) and for a white dwarf
  whose occultation must be overcome (larger mass, larger K).
- Monte Carlo: probability that N spectra at random orbital phases show a peak-to-peak
  RV below a decision threshold even though the companion is real.

Writes results/trackB/243307945_context.json.
Usage: uv run python pipeline/b03_survivor_context.py
"""
import json
import warnings

import numpy as np
import pandas as pd
from scipy.optimize import brentq

from hos import archives as A
from hos import selflens as sl
from hos.paths import RESULTS

warnings.filterwarnings("ignore")

TIC, SIGNAL = 243307945, 3
R_STAR_RANGE = [0.85, 0.92, 1.01]   # Rsun; 1.01 is the TIC value
DECISION_KMS = 20.0                 # peak-to-peak below this counts as "no companion"
RV_NOISE_KMS = 1.0
N_EPOCHS = [2, 3, 4, 6, 8]
N_MC = 200_000


def gaia_context(dr2_id: int) -> dict:
    q = ("SELECT g.source_id, g.phot_g_mean_mag, g.bp_rp, g.parallax, g.ruwe, "
         "g.astrometric_excess_noise, g.astrometric_excess_noise_sig, g.ipd_frac_multi_peak, "
         "g.ipd_gof_harmonic_amplitude, g.radial_velocity, g.rv_nb_transits, "
         "g.non_single_star, g.ra, g.dec FROM gaiadr3.dr2_neighbourhood AS n "
         "JOIN gaiadr3.gaia_source AS g ON g.source_id = n.dr3_source_id "
         f"WHERE n.dr2_source_id = {dr2_id}")
    res = A.gaia_query(q, "b03_gaia")
    if res.empty:  # an empty answer must never be read as "no binarity signal"
        raise RuntimeError(f"no Gaia DR3 match for DR2 {dr2_id}")
    row = res.iloc[0].to_dict()
    row["source_id"] = int(res["source_id"].iloc[0])  # exact: row dicts upcast to float
    nq = ("SELECT source_id, phot_g_mean_mag, parallax, "
          f"DISTANCE(ra, dec, {row['ra']}, {row['dec']}) * 3600 AS sep_arcsec "
          "FROM gaiadr3.gaia_source WHERE 1 = CONTAINS(POINT(ra, dec), "
          f"CIRCLE({row['ra']}, {row['dec']}, {30 / 3600})) ORDER BY sep_arcsec")
    nb = A.gaia_query(nq, "b03_neighbours")
    nb = nb[nb["source_id"].astype("int64") != row["source_id"]]
    nb["flux_ratio"] = 10 ** (-0.4 * (nb["phot_g_mean_mag"] - row["phot_g_mean_mag"]))
    return {"gaia": row, "neighbours_30arcsec": nb.head(10).to_dict("records")}


def xp_rv(source_id: int, ra: float, dec: float) -> dict:
    def build():
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.vizier import Vizier

        r = Vizier(columns=["**"]).query_region(SkyCoord(ra, dec, unit="deg"),
                                                radius=2 * u.arcsec,
                                                catalog="J/A+A/684/A29/extend")
        return r[0].to_pandas() if len(r) else pd.DataFrame()

    d = A.cached_frame("b03_xp_rv_cone", [source_id], build)
    if not d.empty:
        d = d[d["GaiaDR3"].astype("int64") == source_id]  # cone may catch neighbours
    if d.empty:
        return {"xp_rv": None}
    return {"xp_rv_kms": float(d["RV"].iloc[0]), "xp_rv_err_kms": float(d["e_RV"].iloc[0]),
            "source": "Gaia XP spectra RVs, VizieR J/A+A/684/A29"}


def wd_mass_for(amp, m_star, r_star, p):
    f = lambda m: sl.net_amplitude(m, m_star, r_star, p, "wd") - amp  # noqa: E731
    ms = np.linspace(0.2, 1.43, 400)
    v = np.array([f(m) for m in ms])
    idx = np.flatnonzero(np.sign(v[:-1]) != np.sign(v[1:]))
    return float(brentq(f, ms[idx[0]], ms[idx[0] + 1])) if len(idx) else None


def miss_probability(k, n, rng):
    """P(peak-to-peak of n random-phase RVs < DECISION_KMS | semi-amplitude k)."""
    ph = rng.uniform(0, 2 * np.pi, (N_MC, n))
    v = k * np.sin(ph) + rng.normal(0, RV_NOISE_KMS, (N_MC, n))
    return float((np.ptp(v, axis=1) < DECISION_KMS).mean())


def main():
    q = pd.read_csv(RESULTS / "trackB" / "selflens_quicklook.csv")
    r = q[(q.tic == TIC) & (q.signal == SIGNAL)].iloc[0]
    # Take the id from the column, not from a row: a mixed-dtype row upcasts the nullable
    # integer to float64 and corrupts the 19-digit id (caught by the empty-result guard).
    dr2 = int(A.tic_rows([TIC])["GAIA"].iloc[0])
    ctx = gaia_context(dr2)
    g0 = ctx["gaia"]
    ctx.update(xp_rv(int(g0["source_id"]), g0["ra"], g0["dec"]))

    amp, m_star, p = r.amp_ppm * 1e-6, r.m_star, r.period_d
    scen = []
    for rs in R_STAR_RANGE:
        m_ns = sl.implied_lens_mass(amp, m_star, rs, p)
        m_wd = wd_mass_for(amp, m_star, rs, p)
        scen.append({"r_star": rs, "m_lens_pure": m_ns,
                     "K_pure_kms": sl.rv_semi_amplitude_kms(p, m_star, m_ns),
                     "m_lens_wd": m_wd,
                     "K_wd_kms": sl.rv_semi_amplitude_kms(p, m_star, m_wd) if m_wd else None})
    k_min = min(s["K_pure_kms"] for s in scen)
    rng = np.random.default_rng(1)
    miss = {n: miss_probability(k_min, n, rng) for n in N_EPOCHS}
    n_needed = next((n for n in N_EPOCHS if miss[n] < 0.01), None)

    out = {"tic": TIC, "signal": SIGNAL, "period_d": p, "amp_ppm": r.amp_ppm, "m_star": m_star,
           **ctx, "k_scenarios": scen, "k_min_kms": k_min,
           "rv_test": {"decision_ptp_kms": DECISION_KMS, "rv_noise_kms": RV_NOISE_KMS,
                       "miss_probability_at_k_min": miss, "epochs_for_miss_below_1pct": n_needed}}
    path = RESULTS / "trackB" / f"{TIC}_context.json"
    path.write_text(json.dumps(out, indent=2, default=lambda o: None if pd.isna(o) else str(o)))
    g = ctx["gaia"]
    print(f"Gaia: G={g['phot_g_mean_mag']:.2f} RUWE={g['ruwe']:.2f} "
          f"excess-noise sig={g['astrometric_excess_noise_sig']:.1f} rv_n={g['rv_nb_transits']}")
    print("neighbours:", [(round(n['sep_arcsec'], 1), round(n['phot_g_mean_mag'], 2),
                           f"{n['flux_ratio']:.2%}") for n in ctx["neighbours_30arcsec"][:3]])
    print("XP RV:", ctx.get("xp_rv_kms"), "+-", ctx.get("xp_rv_err_kms"))
    for s in scen:
        print(s)
    print("miss prob at K_min:", miss, "-> epochs needed:", n_needed)


if __name__ == "__main__":
    main()
