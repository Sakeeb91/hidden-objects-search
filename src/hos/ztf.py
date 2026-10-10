"""ZTF light curves from the IRSA light-curve API, cached per field."""
import io
import time

import pandas as pd
import requests

from hos.paths import DATA, ensure

API = "https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves"
KEEP = ["oid", "mjd", "mag", "magerr", "catflags", "filtercode", "ra", "dec", "limitmag"]
CACHE = DATA / "ztf"
NOBS_MIN = 40  # server-side: skip objects too sparse for the period search


def cone(ra: float, dec: float, radius_deg: float, field: str, retries=4,
         timeout=900) -> pd.DataFrame:
    """All ZTF light-curve points inside a cone, good-quality epochs only (catflags == 0).

    Cached as data/ztf/<field>.csv.gz; an empty result is cached as an empty frame with
    the expected columns so a field with no ZTF objects is distinguishable from a failure.
    """
    path = ensure(CACHE) / f"{field}.csv.gz"
    if path.exists():
        return pd.read_csv(path)
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
        raise RuntimeError(f"IRSA error for {field}: {text[:300]}")
    df = pd.read_csv(io.StringIO(text)) if text.strip() else pd.DataFrame(columns=KEEP)
    df = df[KEEP]
    df = df[df["catflags"] == 0].drop(columns="catflags")
    df.to_csv(path, index=False, compression="gzip")
    return df
