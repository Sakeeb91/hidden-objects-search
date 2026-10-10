"""Self-lensing physics for a compact companion passing in front of a star.

When a white dwarf, neutron star or black hole crosses the stellar disk, its Einstein
radius R_E (much smaller than the star) magnifies the star. For a point lens inside a
uniform disk with R_E << R*, the fractional brightening is 2 (R_E / R*)^2. A white dwarf
also blocks (R_wd / R*)^2 of the light, so the net signal is the difference. Neutron
stars and black holes do not occult measurably.

Units: masses in solar masses, radii in solar radii, periods in days, unless noted.
Reference check: KOI-3278 (Kruse & Agol 2014, Science 344, 275) shows a ~0.1% pulse.
"""
import numpy as np
from astropy import constants as c

G = c.G.value
C = c.c.value
MSUN = c.M_sun.value
RSUN = c.R_sun.value
DAY = 86400.0


def semi_major_axis_m(period_d, m_total):
    """Kepler's third law: separation in metres."""
    return (G * m_total * MSUN * (period_d * DAY) ** 2 / (4 * np.pi**2)) ** (1 / 3)


def einstein_radius_m(m_lens, a_m):
    """Einstein radius at the source for lens-source separation a (source at distance a
    behind the lens, observer at infinity): R_E = sqrt(4 G M a) / c."""
    return np.sqrt(4 * G * m_lens * MSUN * a_m) / C


def lensing_amplitude(m_lens, m_star, r_star, period_d):
    """Fractional brightening 2 (R_E/R*)^2 for a central crossing (uniform source)."""
    a = semi_major_axis_m(period_d, m_lens + m_star)
    return 2 * (einstein_radius_m(m_lens, a) / (r_star * RSUN)) ** 2


def wd_radius(m_wd):
    """Nauenberg (1972) mass-radius relation for a cold white dwarf, in solar radii."""
    m_ch = 1.44
    m = np.clip(m_wd, 1e-3, m_ch - 1e-3)
    return 0.0112 * np.sqrt((m_ch / m) ** (2 / 3) - (m / m_ch) ** (2 / 3))


def net_amplitude(m_lens, m_star, r_star, period_d, kind="wd"):
    """Lensing minus occultation. kind: 'wd' (occults) or 'ns'/'bh' (does not)."""
    amp = lensing_amplitude(m_lens, m_star, r_star, period_d)
    if kind == "wd":
        amp = amp - (wd_radius(m_lens) / r_star) ** 2
    return amp


def implied_lens_mass(amplitude, m_star, r_star, period_d, tol=1e-6, max_iter=200):
    """Invert the pure-lensing amplitude (no occultation) for the lens mass.

    Because a depends weakly on the lens mass, iterate. Raises on non-positive input,
    so an inverted dip can never be silently turned into a mass.
    """
    if not np.isfinite(amplitude) or amplitude <= 0:
        raise ValueError(f"self-lensing needs a positive brightening, got {amplitude}")
    m = 1.0
    for _ in range(max_iter):
        a = semi_major_axis_m(period_d, m + m_star)
        new = amplitude * (r_star * RSUN) ** 2 * C**2 / (8 * G * a * MSUN)
        if abs(new - m) < tol * max(m, 1e-9):
            return float(new)
        m = new
    raise RuntimeError("implied_lens_mass did not converge")


def central_duration_hr(period_d, m_total, r_star, impact=0.0):
    """Full crossing time of a point lens across the stellar disk (circular orbit).

    Same geometry as a transit of a tiny body, so it is set by the stellar density."""
    a = semi_major_axis_m(period_d, m_total)
    chord = 2 * r_star * RSUN * np.sqrt(max(1 - impact**2, 0.0))
    return float(period_d * 24 / np.pi * np.arcsin(min(chord / (2 * a), 1.0)))


def rv_semi_amplitude_kms(period_d, m_star, m_comp, inc_deg=90.0):
    """Radial-velocity semi-amplitude of the star (km/s) for a circular orbit."""
    p = period_d * DAY
    k = (2 * np.pi * G / p) ** (1 / 3) * m_comp * MSUN * np.sin(np.radians(inc_deg))
    return float(k / ((m_star + m_comp) * MSUN) ** (2 / 3) / 1e3)


def ellipsoidal_amplitude(m_star, m_comp, r_star, period_d, alpha=1.0):
    """Approximate ellipsoidal semi-amplitude ~ alpha (M2/M1) (R*/a)^3 at i = 90 deg."""
    a = semi_major_axis_m(period_d, m_star + m_comp)
    return float(alpha * (m_comp / m_star) * (r_star * RSUN / a) ** 3)
