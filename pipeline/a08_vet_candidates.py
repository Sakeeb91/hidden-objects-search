"""Track A stage 8: characterise uncatalogued spider-like stars in the target ellipses.

The frozen statistics (a06) found no excess over background, so every star here is
expected to be an ordinary field variable. This stage asks what each one most likely
is, using light-curve information NOT used by the detection cuts:

- 3-harmonic Fourier fit at the detected period P and at 2P;
- equal vs unequal minima at 2P (contact/ellipsoidal binaries have two minima per orbit);
- rise-time fraction (pulsators and RR Lyrae rise fast: < 0.4 of the cycle);
- g - r colour amplitude at P (irradiated companions are bluest at maximum light);
- Gaia DR3 parallax -> absolute G where the parallax is significant.

Heuristic labels are hints for follow-up priority, not classifications.
Writes results/trackA/a08_vetting.csv and docs/figures/trackA/<id>.png.
Usage: uv run python pipeline/a08_vet_candidates.py [N_MAX]
"""
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from a05_calibrate import load, spider_like_source  # noqa: E402
from hos import period as P  # noqa: E402
from hos.fields import read_fields  # noqa: E402
from hos import ztf  # noqa: E402
from hos.paths import DOCS, RESULTS, ensure  # noqa: E402

FIG = DOCS / "figures" / "trackA"
SYSTEMATIC_MIN_N = 10   # a period shared by >= this many off-source stars is a cadence artefact
SYSTEMATIC_TOL = 0.002


def systematic_periods() -> np.ndarray:
    """Periods that recur among off-source spider-like stars (before the per-field veto).
    Vetting information only; the frozen statistics are not changed."""
    f = read_fields()
    d = load(f[f.kind == "offsource"])
    lp = np.log(d.loc[spider_like_source(d), "period_d"].to_numpy())
    n = (np.abs(lp[:, None] - lp[None, :]) < SYSTEMATIC_TOL).sum(axis=1)
    reps = []
    for v in np.sort(lp[n >= SYSTEMATIC_MIN_N]):
        if not reps or v - reps[-1] > SYSTEMATIC_TOL:
            reps.append(v)
    return np.exp(np.array(reps))


def fourier(t, y, period, nh=3):
    ph = 2 * np.pi * t / period
    cols = [np.ones_like(t)]
    for k in range(1, nh + 1):
        cols += [np.sin(k * ph), np.cos(k * ph)]
    X = np.column_stack(cols)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    amps = [np.hypot(beta[2 * k - 1], beta[2 * k]) for k in range(1, nh + 1)]
    return beta, X, amps


def model_curve(beta, period, nh=3, n=400):
    ph = np.linspace(0, 1, n)
    m = np.full(n, beta[0])
    for k in range(1, nh + 1):
        m += beta[2 * k - 1] * np.sin(2 * np.pi * k * ph) + beta[2 * k] * np.cos(2 * np.pi * k * ph)
    return ph, m


def shape_metrics(t, y, period):
    beta, _, a = fourier(t, y, period)
    ph, m = model_curve(beta, period)
    i_max, i_min = np.argmin(m), np.argmax(m)  # magnitudes: smaller = brighter
    rise = ((ph[i_max] - ph[i_min]) % 1.0)
    beta2, _, _ = fourier(t, y, 2 * period)
    ph2, m2 = model_curve(beta2, 2 * period)
    half = len(m2) // 2
    d1, d2 = m2[:half].max(), m2[half:].max()
    return {"a2_over_a1": a[1] / max(a[0], 1e-6), "rise_frac": float(rise),
            "minima_diff_2p": float(abs(d1 - d2)), "ptp_model": float(m.max() - m.min())}


def colour_amplitude(g, r, period):
    if g is None or r is None:
        return np.nan
    bg, *_ = fourier(g[0], g[1], period, nh=1)
    br, *_ = fourier(r[0], r[1], period, nh=1)
    return float(np.hypot(bg[1], bg[2]) - np.hypot(br[1], br[2]))  # g minus r semi-amplitude


def hint(row) -> str:
    p_h = row.period_d * 24
    if row.minima_diff_2p < 0.3 * row.ptp_model and 5 < 2 * p_h < 24 and row.a2_over_a1 < 0.3:
        return "contact/ellipsoidal binary (true P = 2P_found)"
    if row.rise_frac < 0.35 and p_h < 7:
        return "pulsator (delta Sct / SX Phe / RR Lyr)"
    if row.colour_amp > 0.02 and row.a2_over_a1 < 0.3:
        return "irradiation-like (colour varies with phase)"
    return "unclassified"


def main():
    n_max = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    c = pd.read_csv(RESULTS / "trackA" / "a06_candidates.csv")
    c = c[~c["known_variable"] & ~c["known_pulsar_or_candidate"]].sort_values("score", ascending=False)
    c = c.head(n_max)
    ensure(FIG)
    sysp = systematic_periods()
    print("systematic periods from off-source fields (d):", np.round(sysp, 4).tolist())
    rows = []
    for k, r in enumerate(c.itertuples(), 1):
        lc = P.group_sources(pd.read_csv(ztf.CACHE / f"{r.field}.csv.gz"))
        g = lc[lc["src"] == r.src]
        bands = {}
        for b, gb in g.groupby("filtercode"):
            y = (gb["mag"] - gb.groupby("oid")["mag"].transform("median")).to_numpy()
            bands[b] = (gb["mjd"].to_numpy(), y)
        main_band = max(bands, key=lambda b: len(bands[b][0]))
        sm = shape_metrics(*bands[main_band], r.period_d)
        rec = {"id": f"C{k:02d}", "field": r.field, "src": int(r.src), "ra": r.ra, "dec": r.dec,
               "period_d": r.period_d, "score": r.score, "coherence": r.coherence,
               "g_mag": r.g_mag, "r_mag": getattr(r, "r_mag", np.nan), "main_band": main_band,
               **sm, "colour_amp": colour_amplitude(bands.get("zg"), bands.get("zr"), r.period_d),
               "gaia_parallax": r.gaia_parallax,
               "gaia_plx_snr": getattr(r, "gaia_parallax_over_error", np.nan),
               "gaia_G": getattr(r, "gaia_phot_g_mean_mag", np.nan), "gaia_bp_rp": r.gaia_bp_rp,
               "simbad": r.simbad if isinstance(r.simbad, str) else ""}
        snr = rec["gaia_plx_snr"]
        rec["abs_G"] = (rec["gaia_G"] + 5 * np.log10(rec["gaia_parallax"] / 100.0)
                        if np.isfinite(snr) and snr > 5 else np.nan)
        rec["systematic_period"] = bool(np.any(np.abs(np.log(r.period_d / sysp)) < SYSTEMATIC_TOL)) \
            if len(sysp) else False
        rec["hint"] = "cadence systematic (period recurs in off-source fields)" \
            if rec["systematic_period"] else hint(pd.Series(rec))
        rows.append(rec)

        fig, ax = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
        for b, col in (("zg", "#2a7ab9"), ("zr", "#c0392b")):
            if b not in bands:
                continue
            t, y = bands[b]
            for a, per, lab in ((ax[0], r.period_d, "P"), (ax[1], 2 * r.period_d, "2P")):
                ph = (t / per) % 1
                a.plot(np.r_[ph, ph + 1], np.r_[y, y], ".", ms=1.5, alpha=0.35, color=col,
                       label=b if lab == "P" else None)
                a.set_xlabel(f"phase at {lab} = {per * 24:.3f} h")
        ax[0].invert_yaxis()
        ax[0].set_ylabel("Δmag")
        ax[0].legend(loc="lower right", fontsize=7, markerscale=5)
        fig.suptitle(f"{rec['id']}  {r.field}  RA {r.ra:.5f} Dec {r.dec:+.5f}  ({rec['hint']})",
                     fontsize=8)
        fig.tight_layout()
        fig.savefig(FIG / f"{rec['id']}.png", dpi=110)
        plt.close(fig)

    out = pd.DataFrame(rows)
    out.to_csv(RESULTS / "trackA" / "a08_vetting.csv", index=False, float_format="%.5g")
    print(out[["id", "field", "period_d", "g_mag", "ptp_model", "a2_over_a1", "rise_frac",
               "minima_diff_2p", "colour_amp", "abs_G", "gaia_bp_rp", "hint"]].to_string(index=False))


if __name__ == "__main__":
    main()
