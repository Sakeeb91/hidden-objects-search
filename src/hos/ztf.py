"""ZTF light curves, cached per field.

Tables: oid, mjd, mag, magerr, filtercode, ra, dec, limitmag; good epochs only
(catflags == 0); objects with >= NOBS_MIN good epochs.

Every field uses ONE backend, 'hats' (ZTF DR24 light curves as HATS/Parquet on AWS S3
via lsdb; time column is heliocentric MJD). The IRSA light-curve API ('api') is kept for
spot checks only: it timed out on dense fields and returned a different object count
(27 vs 20 for the J1023+0038 field), so mixing backends would unmatch target and null
fields.
"""
import io
import threading
import time

import numpy as np
import pandas as pd
import requests

from hos.paths import DATA, ensure

API = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
KEEP = ["oid", "mjd", "mag", "magerr", "catflags", "filtercode", "ra", "dec", "limitmag"]
CACHE = DATA / "ztf"
HATS_URL = "s3://ipac-irsa-ztf/ztf/enhanced/dr24/lc/hats"
BACKEND = "hats"
_HATS = None
_HATS_LOCK = threading.Lock()
NOBS_MIN = 40  # server-side: skip objects too sparse for the period search
TILE_DEG = 0.05  # cones larger than this are split into sub-cones (dense fields time out)


def tile_for_density(density_per_deg2: float, target_objects=300.0) -> float:
    """Tile radius giving ~target_objects Gaia-bright sources per sub-cone (0.02-0.05 deg)."""
    if not np.isfinite(density_per_deg2) or density_per_deg2 <= 0:
        return TILE_DEG
    return float(np.clip(np.sqrt(target_objects / (np.pi * density_per_deg2)), 0.02, TILE_DEG))


def tile_centres(ra: float, dec: float, radius_deg: float, tile=TILE_DEG):
    """Centres of sub-cones of radius `tile` whose union covers the cone (square grid,
    spacing tile*sqrt(2), so neighbouring circles overlap and leave no gaps)."""
    if radius_deg <= tile:
        return [(ra, dec)]
    step = tile * np.sqrt(2)
    n = int(np.ceil(radius_deg / step)) + 1
    out = []
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            dx, dy = i * step, j * step
            # keep a tile if any part of it can overlap the big circle
            if np.hypot(dx, dy) <= radius_deg + tile:
                out.append((ra + dx / np.cos(np.radians(dec)), dec + dy))
    return out


def _query(ra, dec, radius_deg, retries=3, timeout=600) -> pd.DataFrame:
    params = {"POS": f"CIRCLE {ra:.6f} {dec:.6f} {radius_deg:.5f}", "BANDNAME": "g,r",
              "FORMAT": "csv", "BAD_CATFLAGS_MASK": 32768, "NOBS_MIN": NOBS_MIN}
    for attempt in range(retries):
        try:
            r = requests.get(API, params=params, timeout=timeout)
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == retries - 1:
                raise
            time.sleep(10 * (attempt + 1))
    text = r.text
    if text.lstrip().startswith("<"):
        raise RuntimeError(f"IRSA error: {text[:300]}")
    return pd.read_csv(io.StringIO(text)) if text.strip() else pd.DataFrame(columns=KEEP)


def _hats_cone(ra: float, dec: float, radius_deg: float) -> pd.DataFrame:
    global _HATS
    import lsdb
    from upath import UPath

    with _HATS_LOCK:
        if _HATS is None:
            _HATS = lsdb.open_catalog(UPath(HATS_URL, anon=True))
    obj = _HATS.cone_search(ra, dec, radius_deg * 3600).compute()
    if obj.empty:
        return pd.DataFrame(columns=KEEP)
    rows = []
    for o in obj.itertuples():
        lc = o.lightcurve
        band = {1: "zg", 2: "zr", 3: "zi"}.get(int(o.filterid))
        if band is None or band == "zi":
            continue
        rows.append(pd.DataFrame({"oid": int(o.objectid), "mjd": lc["hmjd"].to_numpy(),
                                  "mag": lc["mag"].to_numpy(), "magerr": lc["magerr"].to_numpy(),
                                  "catflags": lc["catflags"].to_numpy(), "filtercode": band,
                                  "ra": float(o.objra), "dec": float(o.objdec),
                                  "limitmag": np.nan}))
    df = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=KEEP)
    good = df[df["catflags"] == 0]
    n = good.groupby("oid")["mjd"].transform("size")
    return good[n >= NOBS_MIN].assign(catflags=0)[KEEP] if len(good) else pd.DataFrame(columns=KEEP)


def cone(ra: float, dec: float, radius_deg: float, field: str, tile=TILE_DEG,
         density=np.nan, backend=BACKEND) -> pd.DataFrame:
    """All ZTF light-curve points inside a cone, good-quality epochs only (catflags == 0).

    Large cones are tiled into TILE_DEG sub-cones, de-duplicated on (oid, mjd, filter) and
    clipped back to the original radius. Cached as data/ztf/<field>.csv.gz; an empty result
    is cached with the expected columns so 'no objects' differs from 'failed'.
    """
    path = ensure(CACHE) / f"{field}.csv.gz"
    if path.exists():
        return pd.read_csv(path)
    if backend == "api":
        tiles = tile_centres(ra, dec, radius_deg, tile)
        tile_r = radius_deg if len(tiles) == 1 else tile
        parts = [_query(tr, td, tile_r)[KEEP] for tr, td in tiles]
        df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=KEEP)
    elif backend == "hats":
        df = _hats_cone(ra, dec, radius_deg)
    else:
        raise ValueError(backend)
    (CACHE / f"{field}.backend").write_text(backend)
    df = df.drop_duplicates(["oid", "mjd", "filtercode"])
    if len(df):
        sep = np.hypot((df["ra"] - ra) * np.cos(np.radians(dec)), df["dec"] - dec)
        df = df[sep <= radius_deg]
    df = df[df["catflags"] == 0].drop(columns="catflags")
    df.to_csv(path, index=False, compression="gzip")
    return df
