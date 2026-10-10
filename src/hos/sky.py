"""Small sky-geometry helpers."""
import numpy as np


def offsets_arcsec(ra, dec, ra0, dec0):
    """Tangent-plane offsets (east, north) in arcsec of (ra, dec) from (ra0, dec0)."""
    dra = (np.asarray(ra) - ra0 + 180) % 360 - 180
    east = dra * np.cos(np.radians(dec0)) * 3600
    north = (np.asarray(dec) - dec0) * 3600
    return east, north


def in_ellipse(ra, dec, ra0, dec0, a_deg, b_deg, pa_deg):
    """True where (ra, dec) lies inside an ellipse with semi-axes a >= b (deg) and
    position angle pa (deg, east of north) of the major axis, as in the 4FGL catalog."""
    e, n = offsets_arcsec(ra, dec, ra0, dec0)
    pa = np.radians(pa_deg)
    u = e * np.sin(pa) + n * np.cos(pa)     # along major axis
    v = e * np.cos(pa) - n * np.sin(pa)     # along minor axis
    return (u / (a_deg * 3600)) ** 2 + (v / (b_deg * 3600)) ** 2 <= 1.0


def sep_arcsec(ra, dec, ra0, dec0):
    e, n = offsets_arcsec(ra, dec, ra0, dec0)
    return np.hypot(e, n)
