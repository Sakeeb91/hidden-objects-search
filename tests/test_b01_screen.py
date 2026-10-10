"""Every kill in the Track B screen must be able to fire, and must not fire wrongly."""
from types import SimpleNamespace

import numpy as np
import pytest

b01 = pytest.importorskip("b01_selflens_quicklook")


def row(dur_ratio=1.0, gaia_id=1.0):
    return SimpleNamespace(tic=1, signal=1, period=5.0, depth_ppm=200.0, depth_err_ppm=20.0,
                           sde=8.0, duration_hr=2.0, dur_ratio=dur_ratio, rho=2.0, rstar=0.7,
                           GAIA=gaia_id)


def gaia(amp, n=20):
    return {1: {"ruwe": 1.0, "rv_nb_transits": n, "rv_amplitude_robust": amp,
                "rv_chisq_pvalue": 0.5, "non_single_star": 0}}


def test_quiet_gaia_rv_excludes():
    assert "K2" in b01.screen(row(), gaia(amp=0.5))["kills"]


def test_loud_gaia_rv_does_not_exclude():
    out = b01.screen(row(), gaia(amp=500.0))
    assert out["verdict"] == "not_excluded"


def test_too_few_rv_epochs_is_insufficient_not_a_pass_or_kill():
    out = b01.screen(row(), gaia(amp=0.5, n=2))
    assert out["gaia"] == "rv_insufficient" and out["verdict"] == "not_excluded"


@pytest.mark.parametrize("missing", [np.nan, None])
def test_missing_gaia_match_is_recorded(missing):
    out = b01.screen(row(gaia_id=missing), {})
    assert out["gaia"] == "no_match"


def test_too_long_pulse_excludes():
    r = row()
    r.duration_hr = 20.0   # far longer than a central crossing at P = 5 d
    assert "K1" in b01.screen(r, gaia(amp=500.0))["kills"]


def test_duration_uses_companion_mass():
    # Review 2: a heavier companion widens the orbit and shortens the allowed pulse, so
    # the mass-aware ratio must exceed the planet-mass ratio for the same observation.
    from hos import selflens as sl
    r = row()
    out = b01.screen(r, gaia(amp=500.0))
    planet_hr = sl.central_duration_hr(r.period, r.rho * r.rstar**3, r.rstar)
    assert out["dur_expected_hr"] < planet_hr


def test_marginal_rv_range_is_not_excluded_with_few_epochs():
    # range = 0.9 K at 5 epochs happens ~8% of the time for a real companion: no kill
    out = b01.screen(row(), {1: {**gaia(amp=1.0)[1], "rv_nb_transits": 5,
                                 "rv_amplitude_robust": 0.9 * b01.screen(row(), {})["K_kms"]}},
                     n_tests=17)
    assert "K2" not in out["kills"]
    assert out["p_false_excl_familywise"] > 0.05


def test_inverted_dip_cannot_become_a_pulse():
    r = row()
    r.depth_ppm = -50.0
    with pytest.raises(ValueError):
        b01.screen(r, gaia(amp=500.0))
