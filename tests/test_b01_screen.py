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
    assert "K1" in b01.screen(row(dur_ratio=2.0), gaia(amp=500.0))["kills"]


def test_inverted_dip_cannot_become_a_pulse():
    r = row()
    r.depth_ppm = -50.0
    with pytest.raises(ValueError):
        b01.screen(r, gaia(amp=500.0))
