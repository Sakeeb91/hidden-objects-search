import numpy as np
import pandas as pd
import pytest

a05 = pytest.importorskip("a05_calibrate")


def src(**kw):
    base = dict(inside=True, bands_agree=True, period_d=0.25, g_amp=0.3, r_amp=0.2,
                g_amp_snr=20.0, r_amp_snr=15.0, score=20.0)
    base.update(kw)
    return pd.DataFrame([base])


@pytest.mark.parametrize("kw", [
    dict(inside=False), dict(bands_agree=False), dict(period_d=0.03), dict(period_d=3.0),
    dict(g_amp=0.01, r_amp=0.02), dict(score=1.0), dict(g_amp=np.nan, r_amp=np.nan),
    dict(g_amp_snr=2.0, r_amp_snr=2.0),          # big but insignificant amplitude
    dict(g_amp=0.3, g_amp_snr=2.0, r_amp=0.01),  # significance and size must be in one band
])
def test_each_cut_can_reject(kw):
    assert not a05.spider_like(src(**kw)).iloc[0]


def test_good_source_passes_and_single_band_amp_suffices():
    assert a05.spider_like(src()).iloc[0]
    assert a05.spider_like(src(g_amp=np.nan, r_amp=0.3)).iloc[0]


def test_period_match_accepts_half_and_double():
    assert a05.period_match(0.1, 0.2) and a05.period_match(0.4, 0.2) and a05.period_match(0.2, 0.2)
    assert not a05.period_match(0.3, 0.2)


def test_field_without_g_band_does_not_crash():
    d = src().drop(columns=["g_amp", "g_amp_snr"])
    assert a05.spider_like(d).iloc[0]


def test_ellipsoidal_half_period_of_shortest_spiders_is_kept():
    # J1622-0315: 3.88 h orbit shows up at P/2 = 1.94 h
    assert a05.spider_like(src(period_d=1.94 / 24)).iloc[0]
