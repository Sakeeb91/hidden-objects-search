"""ZTF light curves from the IRSA light-curve API, cached per field."""
import io
import time

import numpy as np
import pandas as pd
import requests

from hos.paths import DATA, ensure

API = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
KEEP = ["oid", "mjd", "mag", "magerr", "catflags", "filtercode", "ra", "dec", "limitmag"]
CACHE = DATA / "ztf"
NOBS_MIN = 40  # server-side: skip objects too sparse for the period search
TILE_DEG = 0.05  # cones larger than this are split into sub-cones (dense fields time out)


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


def _query(ra, dec, radius_deg, retries=4, timeout=900) -> pd.DataFrame:
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


def cone(ra: float, dec: float, radius_deg: float, field: str) -> pd.DataFrame:
    """All ZTF light-curve points inside a cone, good-quality epochs only (catflags == 0).

    Large cones are tiled into TILE_DEG sub-cones, de-duplicated on (oid, mjd, filter) and
    clipped back to the original radius. Cached as data/ztf/<field>.csv.gz; an empty result
    is cached with the expected columns so 'no objects' differs from 'failed'.
    """
    path = ensure(CACHE) / f"{field}.csv.gz"
    if path.exists():
        return pd.read_csv(path)
    tiles = tile_centres(ra, dec, radius_deg)
    tile_r = radius_deg if len(tiles) == 1 else TILE_DEG
    parts = [_query(tr, td, tile_r)[KEEP] for tr, td in tiles]
    df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=KEEP)
    df = df.drop_duplicates(["oid", "mjd", "filtercode"])
    if len(df):
        sep = np.hypot((df["ra"] - ra) * np.cos(np.radians(dec)), df["dec"] - dec)
        df = df[sep <= radius_deg]
    df = df[df["catflags"] == 0].drop(columns="catflags")
    df.to_csv(path, index=False, compression="gzip")
    return df
