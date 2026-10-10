import numpy as np
import pytest

from hos import selflens as sl


def test_koi3278_lensing_amplitude_matches_published_order():
    # Kruse & Agol 2014: WD 0.634 Msun, star 1.042 Msun / 0.964 Rsun, P = 88.18 d,
    # observed pulse ~0.1%. Pure lensing should be ~1.1e-3, net (minus occultation) ~1e-3.
    lens = sl.lensing_amplitude(0.634, 1.042, 0.964, 88.18)
    net = sl.net_amplitude(0.634, 1.042, 0.964, 88.18, kind="wd")
    assert 1.0e-3 < lens < 1.3e-3
    assert 0.8e-3 < net < lens


def test_implied_mass_round_trips():
    amp = sl.lensing_amplitude(1.4, 0.7, 0.65, 5.0)
    assert sl.implied_lens_mass(amp, 0.7, 0.65, 5.0) == pytest.approx(1.4, rel=1e-4)


@pytest.mark.parametrize("bad", [0.0, -1e-4, np.nan])
def test_implied_mass_rejects_non_brightening(bad):
    # Guard must go red: a dip or a missing value can never become a lens mass.
    with pytest.raises(ValueError):
        sl.implied_lens_mass(bad, 0.7, 0.65, 5.0)


def test_rv_semi_amplitude_sun_jupiter():
    k = sl.rv_semi_amplitude_kms(4332.59, 1.0, 9.546e-4)
    assert k * 1e3 == pytest.approx(12.5, rel=0.02)


def test_central_duration_earth_sun():
    # Earth transit of the Sun lasts ~13 h.
    assert sl.central_duration_hr(365.25, 1.0, 1.0) == pytest.approx(13.0, rel=0.03)


def test_wd_radius_is_earth_sized_and_shrinks_with_mass():
    assert 0.010 < sl.wd_radius(0.6) < 0.015
    assert sl.wd_radius(1.2) < sl.wd_radius(0.6)


def test_heavier_wd_can_flip_sign_of_net_signal():
    # A light WD at short period should be occultation-dominated (net dip), which the
    # quick look must not treat as a lensing pulse.
    assert sl.net_amplitude(0.3, 0.7, 0.65, 1.0, kind="wd") < 0
    assert sl.net_amplitude(1.4, 0.7, 0.65, 1.0, kind="ns") > 0
