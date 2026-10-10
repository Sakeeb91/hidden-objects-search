"""Cached access to public archives (MAST TIC, Gaia DR3, plain URLs).

Every query result is written to data/cache/ so reruns are offline and identical.
"""
import hashlib
import io
import json
from pathlib import Path

import pandas as pd
import requests

from hos.paths import DATA, ensure

CACHE = DATA / "cache"


def _key(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def fetch_url(url: str, dest: Path, timeout=120) -> Path:
    """Download url to dest once; later calls reuse the file."""
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    ensure(dest.parent)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    dest.write_bytes(r.content)
    return dest


def cached_frame(name: str, key_parts, builder, dtype=None) -> pd.DataFrame:
    """Return a cached DataFrame, building it with builder() on first use."""
    path = ensure(CACHE / name) / f"{_key(*key_parts)}.csv"
    if path.exists():
        return pd.read_csv(path, dtype=dtype)
    df = builder()
    df.to_csv(path, index=False)
    return df


def tic_rows(tic_ids) -> pd.DataFrame:
    """TIC v8 rows (ID, ra, dec, GAIA dr2 id, Tmag, mass, rad, Teff) for the given IDs."""
    ids = sorted({int(t) for t in tic_ids})

    def build():
        from astroquery.mast import Catalogs

        tab = Catalogs.query_criteria(catalog="Tic", ID=ids)
        cols = ["ID", "ra", "dec", "GAIA", "Tmag", "mass", "rad", "Teff", "d", "contratio"]
        return tab[cols].to_pandas()

    # Read ids as text: a blank would otherwise make pandas parse 19-digit ids as lossy floats
    df = cached_frame("tic", ids, build, dtype={"ID": str, "GAIA": str})
    df["ID"] = df["ID"].map(int).astype("int64")
    df["GAIA"] = pd.array([int(g) if isinstance(g, str) and g.strip().isdigit() else pd.NA
                           for g in df["GAIA"]], dtype="Int64")
    if len(df) != len(ids):
        missing = set(ids) - set(df["ID"].astype(int))
        raise LookupError(f"TIC query returned {len(df)}/{len(ids)} rows; missing {sorted(missing)[:5]}")
    return df


GAIA_TAP = "https://gea.esac.esa.int/tap-server/tap/sync"


def gaia_query(adql: str, name: str = "gaia", timeout=600) -> pd.DataFrame:
    """Run a synchronous Gaia archive ADQL query, cached by its text.

    Uses the TAP sync endpoint directly; astroquery's async jobs were observed to hang."""

    def build():
        r = requests.post(GAIA_TAP, timeout=timeout, data={
            "REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": "csv", "QUERY": adql})
        r.raise_for_status()
        if r.text.lstrip().startswith("<"):
            raise RuntimeError(f"Gaia TAP error: {r.text[:500]}")
        return pd.read_csv(io.StringIO(r.text))

    return cached_frame(name, [adql], build)


GAIA_BINARITY_COLS = (
    "source_id, ra, dec, phot_g_mean_mag, bp_rp, parallax, ruwe, "
    "radial_velocity, radial_velocity_error, rv_nb_transits, rv_amplitude_robust, "
    "rv_chisq_pvalue, rv_renormalised_gof, non_single_star, phot_variable_flag"
)


def gaia_dr3_from_dr2(dr2_ids) -> pd.DataFrame:
    """Gaia DR3 binarity columns for DR2 source ids, via the official DR2->DR3 neighbourhood.

    Keeps the best (smallest angular distance, then magnitude difference) DR3 match."""
    ids = sorted({int(i) for i in dr2_ids})
    id_list = ",".join(str(i) for i in ids)
    cols = ", ".join(f"g.{c.strip()}" for c in GAIA_BINARITY_COLS.split(","))
    adql = (
        f"SELECT n.dr2_source_id, n.angular_distance, n.magnitude_difference, {cols} "
        "FROM gaiadr3.dr2_neighbourhood AS n "
        "JOIN gaiadr3.gaia_source AS g ON g.source_id = n.dr3_source_id "
        f"WHERE n.dr2_source_id IN ({id_list})"
    )
    df = gaia_query(adql, "gaia_dr2_dr3")
    df["abs_dmag"] = df["magnitude_difference"].abs()
    df = df.sort_values(["dr2_source_id", "angular_distance", "abs_dmag"])
    return df.drop_duplicates("dr2_source_id").drop(columns="abs_dmag")
