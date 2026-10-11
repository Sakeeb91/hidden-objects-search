"""Track B quick look: are any reference "inverted" signals plausible self-lensing pulses?

The reference project (paraschopra/tess-planet-candidates) flipped 526 TESS light curves
and searched them for dips, i.e. searched the original data for periodic *brightenings*.
It used that as a false-alarm baseline. A compact companion (WD/NS/BH) crossing in front
of its star produces exactly such a brightening. This stage asks, for each flag-free
inverted signal, whether physics allows it to be self-lensing, and tries to kill it:

  K1  duration: a central crossing lasts T = (P/pi) arcsin(R*/a), with a from Kepler's law
      using the star's mass PLUS the minimum lens mass (review 2: the reference's ratio
      assumed a planet). The minimum mass gives the smallest a and the longest allowed T,
      so the test is conservative for circular orbits; eccentric orbits can be longer.
  K2  Gaia RV: the minimum lens mass forces a semi-amplitude K. Given Gaia DR3's robust RV
      range over N transits, compute the probability that a real companion would show a
      range this small at random phases, including Gaia's 3-IQR clipping (Monte Carlo).
      Exclude only if its 95% Monte Carlo upper bound, times the number of signals
      screened, is < ALPHA.
  K3  occultation: for a WD the implied pure-lensing mass is a lower bound; flagged only.

Inputs are pinned to reference commit 74d5624. Detection statistics come from the
reference triage and are NOT recomputed here; this is a physics screen, not a search.

Writes results/trackB/selflens_quicklook.csv. Usage: uv run python pipeline/b01_selflens_quicklook.py
"""
import warnings

import numpy as np
import pandas as pd

from scipy.stats import beta as beta_dist

from hos import archives as A
from hos import selflens as sl
from hos.paths import DATA, RESULTS, ensure

warnings.filterwarnings("ignore")

REF_COMMIT = "74d5624"
REF_URL = ("https://raw.githubusercontent.com/paraschopra/tess-planet-candidates/"
           f"{REF_COMMIT}/results/phase3/inverted_triage.csv")

DUR_RATIO_MAX = 1.3        # longer than a central crossing (+30% for the BLS duration grid)
GAIA_MIN_RV_TRANSITS = 3
ALPHA = 0.05               # familywise false-exclusion rate across all screened signals
N_SIM = 400_000


def load_signals() -> pd.DataFrame:
    path = A.fetch_url(REF_URL, DATA / "reference" / f"inverted_triage_{REF_COMMIT}.csv")
    df = pd.read_csv(path)
    clean = df[df["clean"] == True].copy()  # noqa: E712 - column holds booleans
    if clean.empty:
        raise RuntimeError("no flag-free inverted signals found; refusing to report a pass")
    return clean


def screen(row, gaia, n_tests=1) -> dict:
    m_star = row.rho * row.rstar**3            # rho in solar units -> mass in Msun
    amp = row.depth_ppm * 1e-6
    m_lens = sl.implied_lens_mass(amp, m_star, row.rstar, row.period)
    k = sl.rv_semi_amplitude_kms(row.period, m_star, m_lens)
    ell = sl.ellipsoidal_amplitude(m_star, m_lens, row.rstar, row.period)
    out = {
        "tic": int(row.tic), "signal": int(row.signal), "period_d": row.period,
        "amp_ppm": row.depth_ppm, "amp_err_ppm": row.depth_err_ppm, "sde": row.sde,
        "dur_hr": row.duration_hr, "dur_ratio": row.dur_ratio, "m_star": m_star,
        "r_star": row.rstar, "m_lens_min": m_lens, "K_kms": k, "ellip_ppm": ell * 1e6,
    }
    expected_hr = sl.central_duration_hr(row.period, m_star + m_lens, row.rstar)
    out["dur_expected_hr"] = expected_hr
    out["dur_ratio_massive"] = row.duration_hr / expected_hr
    kills = []
    if out["dur_ratio_massive"] > DUR_RATIO_MAX:
        kills.append("K1:too_long_circular")
    g = gaia.get(int(row.GAIA)) if pd.notna(row.GAIA) else None
    if g is None:
        out["gaia"] = "no_match"
    else:
        out.update({"gaia_ruwe": g["ruwe"], "gaia_rv_n": g["rv_nb_transits"],
                    "gaia_rv_amp": g["rv_amplitude_robust"],
                    "gaia_rv_p": g["rv_chisq_pvalue"], "gaia_nss": g["non_single_star"]})
        n = g["rv_nb_transits"]
        if np.isfinite(n) and n >= GAIA_MIN_RV_TRANSITS and np.isfinite(g["rv_amplitude_robust"]):
            r = g["rv_amplitude_robust"] / k
            p_ideal = sl.rv_range_cdf(r, int(n))
            p_mc = sl.rv_range_cdf_clipped(r, int(n), nsim=N_SIM)
            # one-sided 95% Clopper-Pearson upper bound on the Monte Carlo estimate (review 3)
            p_clip = float(beta_dist.ppf(0.95, round(p_mc * N_SIM) + 1, N_SIM - round(p_mc * N_SIM)))
            out.update({"rv_range_over_K": r, "p_false_excl_ideal": p_ideal,
                        "p_false_excl_clipped": p_clip,
                        "p_false_excl_familywise": min(1.0, p_clip * n_tests)})
            if p_clip * n_tests < ALPHA:
                kills.append("K2:gaia_rv_too_quiet")
        else:
            out["gaia"] = "rv_insufficient"
    out["kills"] = ";".join(kills)
    out["verdict"] = "excluded" if kills else "not_excluded"
    out["note"] = ("pure-lensing mass is a lower bound for a WD (occultation reduces the "
                   "signal)" if m_lens < 1.4 else "requires NS/BH-mass companion")
    return out


def main():
    sig = load_signals()
    tic = A.tic_rows(sig["tic"]).rename(columns={"ID": "tic"})
    sig = sig.merge(tic[["tic", "GAIA"]], on="tic", how="left")
    g = A.gaia_dr3_from_dr2(sig["GAIA"].dropna().astype("int64"))
    gaia = {int(r["dr2_source_id"]): r for r in g.to_dict("records")}
    rows = [screen(r, gaia, n_tests=len(sig)) for r in sig.itertuples()]
    if len(rows) != len(sig):
        raise RuntimeError("screen dropped rows")
    out = pd.DataFrame(rows).sort_values(["verdict", "sde"], ascending=[False, False])
    path = ensure(RESULTS / "trackB") / "selflens_quicklook.csv"
    out.to_csv(path, index=False, float_format="%.6g")
    print(out[["tic", "signal", "period_d", "amp_ppm", "dur_ratio_massive", "m_lens_min", "K_kms",
               "gaia_rv_n", "rv_range_over_K", "p_false_excl_familywise", "verdict",
               "kills"]].to_string(index=False))
    print(f"\n{(out.verdict == 'not_excluded').sum()} of {len(out)} not excluded -> {path}")


if __name__ == "__main__":
    main()
