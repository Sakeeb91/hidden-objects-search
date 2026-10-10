import numpy as np
import pandas as pd
import pytest

a05 = pytest.importorskip("a05_calibrate")


def src(**kw):
    base = dict(inside=True, bands_agree=True, period_d=0.25, g_amp=0.3, r_amp=0.2, score=20.0)
    base.update(kw)
    return pd.DataFrame([base])


@pytest.mark.parametrize("kw", [
    dict(inside=False), dict(bands_agree=False), dict(period_d=0.05), dict(period_d=3.0),
    dict(g_amp=0.01, r_amp=0.02), dict(score=1.0), dict(g_amp=np.nan, r_amp=np.nan),
])
def test_each_cut_can_reject(kw):
    assert not a05.spider_like(src(**kw)).iloc[0]


def test_good_source_passes_and_single_band_amp_suffices():
    assert a05.spider_like(src()).iloc[0]
    assert a05.spider_like(src(g_amp=np.nan, r_amp=0.3)).iloc[0]


def test_period_match_accepts_half_and_double():
    assert a05.period_match(0.1, 0.2) and a05.period_match(0.4, 0.2) and a05.period_match(0.2, 0.2)
    assert not a05.period_match(0.3, 0.2)
