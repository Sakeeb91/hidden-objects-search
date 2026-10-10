"""Track B follow-up: does the surviving signal's star show the phase curve a compact
companion would force on it?

A lens heavy enough to make the observed brightening pulls the star around at K km/s,
which brightens/dims it by Doppler beaming at the orbital period P, and tides stretch it
into ellipsoidal variation at P/2. Both amplitudes follow from the minimum lens mass.

Method (no detrending that could eat the signal): per-segment cubic polynomials for
instrumental trends plus sin/cos terms at P and P/2, fitted jointly by least squares.
Calibration: the identical fit at many random trial periods gives the empirical noise
distribution of each amplitude. Injection: the predicted phase curve is added to the real
data and the fit must recover it, or the test is declared uninformative (never a pass).

Writes results/trackB/<TIC>_phasecurve.json.
Usage: uv run python pipeline/b02_survivor_phasecurve.py [TIC SIGNAL]
"""
import json
import sys
import warnings

import numpy as np
import pandas as pd

from hos import selflens as sl
from hos.paths import DATA, RESULTS, ensure

warnings.filterwarnings("ignore")

ALPHA_BEAM = 0.8     # conservative (low) TESS-band beaming factor for a ~4700 K star
ALPHA_ELL = 1.0      # conservative ellipsoidal prefactor
N_NULL = 400
GAP_D = 0.5          # split segments at gaps longer than this
SEG_MAX_D = 7.0      # and cap segment length so polynomials track scattered light
POLY_DEG = 3


def load_lc(tic: int) -> pd.DataFrame:
    import lightkurve as lk

    cache = ensure(DATA / "lightcurves") / f"{tic}_trackB.csv"
    if cache.exists():
        return pd.read_csv(cache)
    res = lk.search_lightcurve(f"TIC {tic}")
    frames = []
    for author in ("TESS-SPOC", "QLP"):
        sub = res[res.author == author]
        for i in range(len(sub)):
            sector = int(sub.table["sequence_number"][i])
            if any(f["sector"].iloc[0] == sector for f in frames):
                continue  # one reduction per sector, SPOC preferred
            lc = sub[i].download(download_dir=str(DATA / "lk_cache"))
            q = lc.quality.value == 0 if hasattr(lc.quality, "value") else lc.quality == 0
            lc = lc[q].remove_nans()
            flux = lc.flux.value / np.nanmedian(lc.flux.value)
            frames.append(pd.DataFrame({"time": lc.time.value, "flux": flux,
                                        "flux_err": lc.flux_err.value / np.nanmedian(lc.flux.value),
                                        "sector": sector, "author": author}))
    if not frames:
        raise RuntimeError(f"no light curves for TIC {tic}")
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(cache, index=False)
    return df


def segments(t: np.ndarray) -> np.ndarray:
    seg = np.zeros(len(t), dtype=int)
    start, k = t[0], 0
    for i in range(1, len(t)):
        if t[i] - t[i - 1] > GAP_D or t[i] - start > SEG_MAX_D:
            k += 1
            start = t[i]
        seg[i] = k
    return seg


def design(t, seg, period, t0):
    cols = []
    for s in np.unique(seg):
        m = seg == s
        x = np.zeros_like(t)
        tt = t[m]
        x[m] = 2 * (tt - tt.min()) / max(np.ptp(tt), 1e-3) - 1
        for d in range(POLY_DEG + 1):
            c = np.zeros_like(t)
            c[m] = x[m] ** d
            cols.append(c)
    ph = 2 * np.pi * (t - t0) / period
    cols += [np.sin(ph), np.cos(ph), np.sin(2 * ph), np.cos(2 * ph)]
    return np.column_stack(cols)


def fit_amplitudes(t, f, seg, period, t0):
    """Return (A_P, A_P/2) semi-amplitudes in ppm from a joint linear fit."""
    X = design(t, seg, period, t0)
    beta, *_ = np.linalg.lstsq(X, f - 1, rcond=None)
    s1, c1, s2, c2 = beta[-4:]
    return float(np.hypot(s1, c1) * 1e6), float(np.hypot(s2, c2) * 1e6)


def mask_pulses(t, period, t0, dur_hr):
    ph = ((t - t0) / period + 0.5) % 1 - 0.5
    return np.abs(ph * period * 24) > dur_hr  # drop +-1 duration around each pulse


def harmonic_verdict(pred, meas, injected, null) -> str:
    """Decide one harmonic. A test may only exclude if it could have seen the signal:
    the prediction must clear the null's 95th percentile and the injection must come
    back within the null's spread of the prediction. Otherwise it is 'insensitive'."""
    null = np.asarray(null)
    if null.size == 0 or not np.isfinite(pred) or pred <= 0:
        return "insensitive"  # an empty or meaningless null can never support a verdict
    p95, spread = np.percentile(null, 95), np.percentile(null, 50)
    if pred <= p95 or abs(injected - pred) > spread + 0.5 * pred:
        return "insensitive"
    return "excludes" if meas < 0.5 * pred else "consistent"


def combine(beam: str, ell: str) -> str:
    if "excludes" in (beam, ell):
        return "excluded: no beaming/ellipsoidal at the level the lens mass requires"
    if "consistent" in (beam, ell):
        return "not_excluded: phase-curve amplitude consistent with the lens prediction"
    return "untested: TESS phase curve not sensitive enough at this period"


def main():
    tic = int(sys.argv[1]) if len(sys.argv) > 1 else 243307945
    signal = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    q = pd.read_csv(RESULTS / "trackB" / "selflens_quicklook.csv")
    r = q[(q.tic == tic) & (q.signal == signal)].iloc[0]
    ref = pd.read_csv(DATA / "reference" / "inverted_triage_74d5624.csv")
    t0 = float(ref[(ref.tic == tic) & (ref.signal == signal)].t0.iloc[0])

    lc = load_lc(tic).sort_values("time")
    t, f = lc.time.to_numpy(), lc.flux.to_numpy()
    keep = mask_pulses(t, r.period_d, t0, r.dur_hr) & (np.abs(f - 1) < 0.02)
    t, f = t[keep], f[keep]
    seg = segments(t)

    k = r.K_kms
    pred_beam = 4 * ALPHA_BEAM * k / 299792.458 * 1e6
    pred_ell = ALPHA_ELL * r.ellip_ppm
    a_p, a_p2 = fit_amplitudes(t, f, seg, r.period_d, t0)

    # Null trial periods near P, so they share P's degeneracy with the trend polynomials.
    rng = np.random.default_rng(42)
    trial = rng.uniform(0.7 * r.period_d, 1.4 * r.period_d, N_NULL)
    trial = trial[np.abs(trial / r.period_d - 1) > 0.05]
    null = np.array([fit_amplitudes(t, f, seg, p, t0 + rng.uniform(0, p)) for p in trial])

    # Injection: predicted beaming (sin, max at quadrature) + ellipsoidal (min at conjunction)
    ph = 2 * np.pi * (t - t0) / r.period_d
    inj = f + pred_beam * 1e-6 * np.sin(ph) - pred_ell * 1e-6 * np.cos(2 * ph)
    i_p, i_p2 = fit_amplitudes(t, inj, seg, r.period_d, t0)

    def pct(x, col):
        return float((null[:, col] >= x).mean())

    out = {
        "tic": tic, "signal": signal, "period_d": r.period_d, "t0_btjd": t0,
        "sectors": sorted(int(s) for s in lc.sector.unique()), "n_points": int(len(t)),
        "m_lens_min": r.m_lens_min, "K_kms_min": k,
        "pred_beam_ppm": pred_beam, "pred_ellip_ppm": pred_ell,
        "meas_P_ppm": a_p, "meas_P2_ppm": a_p2,
        "null_P_median_ppm": float(np.median(null[:, 0])),
        "null_P_p99.7_ppm": float(np.percentile(null[:, 0], 99.7)),
        "null_P2_median_ppm": float(np.median(null[:, 1])),
        "null_P2_p99.7_ppm": float(np.percentile(null[:, 1], 99.7)),
        "meas_P_null_frac_ge": pct(a_p, 0), "meas_P2_null_frac_ge": pct(a_p2, 1),
        "inj_recovered_P_ppm": i_p, "inj_recovered_P2_ppm": i_p2,
    }
    beam = harmonic_verdict(pred_beam, a_p, i_p, null[:, 0])
    ell = harmonic_verdict(pred_ell, a_p2, i_p2, null[:, 1])
    out.update({"beam_test": beam, "ellip_test": ell, "verdict": combine(beam, ell)})
    path = ensure(RESULTS / "trackB") / f"{tic}_s{signal}_phasecurve.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
