"""X-ray counterparts for optical candidates.

UNIFORM surveys cover the sky without regard to Fermi sources, so their match rate can
be calibrated with off-source null fields: eRASS1 (eROSITA-DE half sky, Galactic
l > 180 deg) and 2RXS (ROSAT, all sky, shallow).
TARGETED catalogs (Swift 2SXPS, XMM 4XMM-DR13) preferentially observe Fermi sources, so
on-source fields get deeper coverage than nulls; they are used for vetting only.
"""
import pandas as pd

from hos.archives import cached_frame

UNIFORM = {"erass1": ("J/A+A/682/A34/erass1-m", 15.0), "2rxs": ("J/A+A/588/A103/cat2rxs", 30.0)}
TARGETED = {"2sxps": ("IX/58/2sxps", 8.0), "4xmm": ("IX/69/xmm4d13s", 5.0)}


def erass1_covers(glon_deg: float) -> bool:
    """eRASS1 DR1 covers the German half of the sky, 179.944 < l < 359.944 deg."""
    return 179.944 < glon_deg % 360 < 359.944


def _cone(cat: str, ra: float, dec: float, radius_arcsec: float) -> int:
    def build():
        import astropy.units as u
        from astropy.coordinates import SkyCoord
        from astroquery.vizier import Vizier

        res = Vizier(row_limit=50).query_region(
            SkyCoord(ra, dec, unit="deg"), radius=radius_arcsec * u.arcsec, catalog=cat)
        return pd.DataFrame({"n": [len(res[0]) if len(res) else 0]})

    return int(cached_frame("xray", [cat, round(ra, 6), round(dec, 6), radius_arcsec],
                            build)["n"].iloc[0])


def matches(ra: float, dec: float, glon: float) -> dict:
    """Counts of X-ray sources within each catalog's match radius; None where a uniform
    survey does not cover the position (so 'no coverage' is never read as 'no source')."""
    out = {}
    for name, (cat, rad) in UNIFORM.items():
        if name == "erass1" and not erass1_covers(glon):
            out[name] = None
        else:
            out[name] = _cone(cat, ra, dec, rad)
    for name, (cat, rad) in TARGETED.items():
        out[name] = _cone(cat, ra, dec, rad)
    covered = [v for k, v in out.items() if k in UNIFORM and v is not None]
    out["uniform_match"] = bool(covered) and any(v > 0 for v in covered)
    out["any_match"] = any((v or 0) > 0 for v in out.values() if not isinstance(v, bool))
    return out
