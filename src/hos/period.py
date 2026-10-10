"""Period search on ZTF light curves.

Sources: ZTF assigns separate object ids per band and per field/CCD. Ids within
MATCH_ARCSEC of each other are merged into one source, keeping each band separate.

Periodogram: Lomb-Scargle per band on a shared frequency grid; the score is the mean
power across bands with enough points, and the best peak must agree between bands when
both are available. Frequencies near daily and sidereal-daily aliases are masked.
"""
import numpy as np
import pandas as pd
from astropy.timeseries import LombScargle
from scipy.spatial import cKDTree

MATCH_ARCSEC = 1.5
MIN_POINTS = 40
F_MIN, F_MAX = 1 / 2.0, 25.0          # periods 0.96 h - 2 d (cycles per day); the
                                      # ceiling covers P/2 of the shortest (2 h) spiders
OVERSAMPLE = 5
GRID_BASELINE_D = 2700.0              # ONE grid for every search (production, controls,
                                      # injections): ZTF spans ~2018-2025
ALIAS_HALFWIDTH = 0.004               # c/d masked around each alias
_N = np.arange(1, 21)
ALIASES = np.concatenate([
    _N * 1.0, _N * 1.0027379,                       # solar and sidereal day
    _N + 1 / 29.53, _N - 1 / 29.53,                 # lunar-month sidebands
    _N + 1 / 365.25, _N - 1 / 365.25,               # yearly sidebands
])
BAND_AGREE = 0.002                    # relative argmax agreement (diagnostic only)
BAND_DETECT = 2.0                     # each band: -log10 FAP >= 2 AT the shared frequency


def group_sources(df: pd.DataFrame) -> pd.DataFrame:
    """Add a 'src' column grouping object ids that sit within MATCH_ARCSEC."""
    pos = df.groupby("oid")[["ra", "dec"]].median()
    dec0 = np.radians(pos["dec"].median())
    xy = np.column_stack([pos["ra"] * np.cos(dec0), pos["dec"]]) * 3600
    tree = cKDTree(xy)
    parent = np.arange(len(pos))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in tree.query_pairs(MATCH_ARCSEC):
        parent[find(i)] = find(j)
    roots = np.array([find(i) for i in range(len(pos))])
    src = pd.Series(roots, index=pos.index, name="src")
    return df.join(src, on="oid")


def frequency_grid(baseline_d: float = GRID_BASELINE_D) -> np.ndarray:
    """Regular grid (required by the fast Lomb-Scargle); aliases are masked afterwards.
    Production and injection searches must both use the default (review 2)."""
    df = 1 / (OVERSAMPLE * max(baseline_d, 30.0))
    return np.arange(F_MIN, F_MAX, df)


def alias_mask(freq: np.ndarray) -> np.ndarray:
    """True where a frequency is usable (not within ALIAS_HALFWIDTH of an alias)."""
    keep = np.ones(freq.size, bool)
    for a in ALIASES:
        keep &= np.abs(freq - a) > ALIAS_HALFWIDTH
    return keep


def band_power(t, y, dy, freq):
    return LombScargle(t, y, dy).power(freq, method="fast")


def band_log_fap(t, y, dy, power) -> float:
    """-log10 of the Baluev white-noise false-alarm probability of a peak of this power
    over the searched band. Accounts for the number of points; floored at 1e-300."""
    fap = LombScargle(t, y, dy).false_alarm_probability(
        power, method="baluev", minimum_frequency=F_MIN, maximum_frequency=F_MAX)
    return float(-np.log10(max(fap, 1e-300)))


def search_source(g: pd.DataFrame, freq: np.ndarray) -> dict | None:
    """Period search for one merged source. Returns None if too few points."""
    powers, bands, best, series = [], [], {}, {}
    ok = alias_mask(freq)
    for band, b in g.groupby("filtercode"):
        if len(b) < MIN_POINTS:
            continue
        # per-oid offsets: different fields/CCDs have small zero-point differences
        y = b["mag"] - b.groupby("oid")["mag"].transform("median")
        p = band_power(b["mjd"].to_numpy(), y.to_numpy(), b["magerr"].to_numpy(), freq)
        p = np.where(ok, p, 0.0)
        powers.append(p)
        bands.append(band)
        series[band] = (b["mjd"].to_numpy(), y.to_numpy(), b["magerr"].to_numpy(), p)
        best[band] = freq[np.argmax(p)]
    if not powers:
        return None
    mean = np.mean(powers, axis=0)
    i = int(np.argmax(mean))
    f_best = freq[i]
    argmax_agree = (len(best) < 2) or (abs(best.get("zg", f_best) - best.get("zr", f_best))
                                       / f_best < BAND_AGREE)
    # Significance at the shared best frequency, per band and summed (independent data).
    # Bands "agree" if the period is independently significant in each of them; requiring
    # identical per-band argmaxes failed when daily aliasing swapped one band's peak
    # (review 1 minor; seen on control 1FGL J0523.5-2529).
    band_lf = [band_log_fap(t, y, dy, pw[i]) for t, y, dy, pw in series.values()]
    score = sum(band_lf)
    agree = (len(band_lf) < 2) or (min(band_lf) >= BAND_DETECT)
    out = {"n_bands": len(bands), "bands": ",".join(sorted(bands)), "power": float(mean[i]),
           "score": float(score), "coherence": half_coherence(series, f_best),
           "period_d": float(1 / f_best), "bands_agree": bool(agree),
           "argmax_agree": bool(argmax_agree), "min_band_logfap": float(min(band_lf)),
           "ra": float(g["ra"].median()), "dec": float(g["dec"].median()),
           "n_points": int(len(g))}
    for band in ("zg", "zr"):
        b = g[g["filtercode"] == band]
        if len(b) >= MIN_POINTS:
            out.update(fold_stats(b, 1 / f_best, prefix=band[1]))
    return out


def sine_fit(t, y, dy, period):
    """Weighted least-squares fit y = c + a sin + b cos at the period.

    Returns (semi-amplitude, its 1-sigma error). The error is scaled by sqrt(reduced chi2)
    when the scatter exceeds the quoted errors (ZTF magerr is often underestimated)."""
    ph = 2 * np.pi * t / period
    X = np.column_stack([np.ones_like(t), np.sin(ph), np.cos(ph)])
    w = 1 / np.clip(dy, 1e-3, None)
    beta, *_ = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)
    resid = (y - X @ beta) * w
    dof = max(len(t) - 3, 1)
    scale = max(np.sum(resid**2) / dof, 1.0)
    cov = np.linalg.pinv((X * w[:, None]).T @ (X * w[:, None])) * scale
    a, b = beta[1], beta[2]
    amp = float(np.hypot(a, b))
    # propagate to amplitude (delta method); floor avoids division by zero at amp = 0
    g = np.array([a, b]) / max(amp, 1e-9)
    err = float(np.sqrt(max(g @ cov[1:, 1:] @ g, 1e-12)))
    return amp, err


def half_coherence(series: dict, f_best: float) -> float:
    """Persistence test against stochastic variability (review 1, M3: blazars flicker but
    are not strictly periodic). Split every band's light curve at its median time; in each
    half, sum over bands the -log10 Baluev FAP of the power AT f_best. Return the smaller
    half's value: a coherent orbit is significant in both halves, red noise rarely is."""
    halves = [0.0, 0.0]
    for t, y, dy, _ in series.values():
        cut = np.median(t)
        for k, m in enumerate((t < cut, t >= cut)):
            if m.sum() < MIN_POINTS // 2:
                continue
            pw = LombScargle(t[m], y[m], dy[m]).power(np.array([f_best]))[0]
            halves[k] += band_log_fap(t[m], y[m], dy[m], pw)
    return float(min(halves))


def fold_stats(b: pd.DataFrame, period: float, prefix: str) -> dict:
    """Median mag, fitted peak-to-peak amplitude (2 x semi-amplitude) with its S/N, and
    minima-depth asymmetry when folded at 2P."""
    y = (b["mag"] - b.groupby("oid")["mag"].transform("median")).to_numpy()
    t = b["mjd"].to_numpy()
    semi, err = sine_fit(t, y, b["magerr"].to_numpy(), period)
    # At 2P a double-humped (ellipsoidal/contact) curve shows two minima; compare them.
    ph2 = (t / (2 * period)) % 1
    m1, m2 = np.nanmedian(y[ph2 < 0.5]), np.nanmedian(y[ph2 >= 0.5])
    return {f"{prefix}_mag": float(np.median(b["mag"])), f"{prefix}_amp": 2 * semi,
            f"{prefix}_amp_snr": semi / err, f"{prefix}_half_diff": float(abs(m1 - m2))}

