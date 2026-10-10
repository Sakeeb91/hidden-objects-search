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
F_MIN, F_MAX = 1 / 2.0, 1 / 0.05      # periods 1.2 h - 2 d (cycles per day)
OVERSAMPLE = 5
ALIAS_HALFWIDTH = 0.004               # c/d masked around each alias
ALIASES = np.concatenate([np.arange(1, 21) * 1.0, np.arange(1, 21) * 1.0027379])
BAND_AGREE = 0.002                    # relative frequency agreement between bands


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


def frequency_grid(baseline_d: float) -> np.ndarray:
    """Regular grid (required by the fast Lomb-Scargle); aliases are masked afterwards."""
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


def search_source(g: pd.DataFrame, freq: np.ndarray) -> dict | None:
    """Period search for one merged source. Returns None if too few points."""
    powers, bands, best = [], [], {}
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
        best[band] = freq[np.argmax(p)]
    if not powers:
        return None
    mean = np.mean(powers, axis=0)
    i = int(np.argmax(mean))
    f_best = freq[i]
    agree = (len(best) < 2) or (abs(best.get("zg", f_best) - best.get("zr", f_best))
                                / f_best < BAND_AGREE)
    out = {"n_bands": len(bands), "bands": ",".join(sorted(bands)), "power": float(mean[i]),
           "period_d": float(1 / f_best), "bands_agree": bool(agree),
           "ra": float(g["ra"].median()), "dec": float(g["dec"].median()),
           "n_points": int(len(g))}
    for band in ("zg", "zr"):
        b = g[g["filtercode"] == band]
        if len(b) >= MIN_POINTS:
            out.update(fold_stats(b, 1 / f_best, prefix=band[1]))
    return out


def fold_stats(b: pd.DataFrame, period: float, prefix: str, nbins=20) -> dict:
    """Median mag, binned peak-to-peak amplitude at P, and minima depth asymmetry at 2P."""
    y = (b["mag"] - b.groupby("oid")["mag"].transform("median")).to_numpy()
    t = b["mjd"].to_numpy()
    amp = _binned_ptp(t, y, period, nbins)
    # At 2P a double-humped (ellipsoidal/contact) curve shows two minima; compare them.
    ph2 = (t / (2 * period)) % 1
    m1, m2 = np.nanmedian(y[ph2 < 0.5]), np.nanmedian(y[ph2 >= 0.5])
    return {f"{prefix}_mag": float(np.median(b["mag"])), f"{prefix}_amp": float(amp),
            f"{prefix}_half_diff": float(abs(m1 - m2))}


def _binned_ptp(t, y, period, nbins):
    ph = (t / period) % 1
    idx = np.minimum((ph * nbins).astype(int), nbins - 1)
    med = np.array([np.median(y[idx == k]) if np.any(idx == k) else np.nan
                    for k in range(nbins)])
    return np.nanmax(med) - np.nanmin(med) if np.isfinite(med).sum() >= nbins // 2 else np.nan
