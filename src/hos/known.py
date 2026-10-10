"""Known spider pulsars and candidates: positive controls and the novelty exclusion set."""
import numpy as np
import pandas as pd
from astropy import units as u
from astropy.coordinates import SkyCoord

from hos.archives import cached_frame

SPIDERCAT = "J/ApJ/994/8"  # Koljonen & Linares 2025, ApJ 994, 8


def _vizier(table: str) -> pd.DataFrame:
    def build():
        from astroquery.vizier import Vizier

        return Vizier(columns=["**"], row_limit=-1).get_catalogs(table)[0].to_pandas()

    return cached_frame("vizier", [table], build)


def spidercat() -> pd.DataFrame:
    """SpiderCat systems joined with Fermi association and optical magnitude."""
    base = _vizier(f"{SPIDERCAT}/table2")
    hi = _vizier(f"{SPIDERCAT}/table3")[["Name", "Fermi", "Fermisep"]]
    phot = _vizier(f"{SPIDERCAT}/table5")[["Name", "gmag", "g-r", "d"]]
    opt = _vizier(f"{SPIDERCAT}/table4")[["Name", "GaiaDR3"]]
    df = (base.merge(hi, on="Name", how="left").merge(phot, on="Name", how="left")
          .merge(opt, on="Name", how="left"))
    c = SkyCoord(df["RAJ2000"].astype(str), df["DEJ2000"].astype(str),
                 unit=(u.hourangle, u.deg))
    df["ra"], df["dec"] = c.ra.deg, c.dec.deg
    df = df.rename(columns={"Pb": "pb_h"})  # SpiderCat Pb is in hours
    fermi = df["Fermi"].fillna("").astype(str).str.strip()
    df["fermi_name"] = np.where(fermi != "", "4FGL " + fermi, "")
    df["has_gaia"] = df["GaiaDR3"].notna() & (df["GaiaDR3"].astype(str).str.strip() != "")
    return df


def lu2024() -> pd.DataFrame:
    """Lu et al. 2024 (arXiv:2412.11616) Table 4 spider candidates (DR3 + ZTF search)."""
    from hos.paths import DOCS

    return pd.read_csv(DOCS / "references" / "lu2024_candidates.csv", comment="#")
