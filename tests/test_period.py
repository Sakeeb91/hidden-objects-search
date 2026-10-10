import numpy as np
import pandas as pd

from hos import period as P


def synth(period_d=0.3, amp=0.2, n=300, seed=1, noise=0.03, bands=("zg", "zr"), ra=10.0):
    rng = np.random.default_rng(seed)
    rows = []
    for k, band in enumerate(bands):
        t = np.sort(rng.uniform(58200, 60600, n))
        y = 18 + amp * np.sin(2 * np.pi * t / period_d) + rng.normal(0, noise, n)
        rows.append(pd.DataFrame({"oid": 100 + k, "mjd": t, "mag": y, "magerr": noise,
                                  "filtercode": band, "ra": ra, "dec": 5.0}))
    return pd.concat(rows, ignore_index=True)


def test_recovers_injected_period_in_both_bands():
    g = synth()
    freq = P.frequency_grid(2400)
    out = P.search_source(g, freq)
    assert abs(out["period_d"] - 0.3) / 0.3 < 1e-3
    assert out["bands_agree"] and out["n_bands"] == 2
    assert 0.35 < out["g_amp"] < 0.45          # fitted peak-to-peak = 2 x 0.2
    assert out["g_amp_snr"] > 20


def test_pure_noise_has_low_power():
    g = synth(amp=0.0)
    out = P.search_source(g, P.frequency_grid(2400))
    assert out["power"] < 0.2


def test_too_few_points_returns_none_not_a_detection():
    assert P.search_source(synth(n=10), P.frequency_grid(2400)) is None


def test_alias_frequencies_are_masked():
    f = P.frequency_grid(2400)
    ok = P.alias_mask(f)
    assert not ok[np.argmin(np.abs(f - 1.0))]
    assert not ok[np.argmin(np.abs(f - 2.0054758))]
    assert ok.mean() > 0.9


def test_signal_at_exactly_one_day_is_not_reported_there():
    out = P.search_source(synth(period_d=1.0), P.frequency_grid(2400))
    assert abs(1 / out["period_d"] - 1.0) > P.ALIAS_HALFWIDTH


def test_grouping_merges_close_ids_and_separates_far_ones():
    a = synth(ra=10.0)                 # oids 100, 101 at the same position
    b = synth(ra=10.01, seed=2)        # 36 arcsec away
    b["oid"] += 10
    out = P.group_sources(pd.concat([a, b]))
    assert out.groupby("src")["oid"].nunique().sort_values().tolist() == [2, 2]


def test_fitted_amplitude_is_not_noise_biased_for_faint_noise():
    # Review 1 M5: binned max-min gave ~0.14 mag on pure noise; the fit must not.
    g = synth(amp=0.0, noise=0.15, n=200)
    out = P.search_source(g, P.frequency_grid(2400))
    assert out["g_amp_snr"] < 5


def test_coherent_sinusoid_is_significant_in_both_halves():
    out = P.search_source(synth(amp=0.1), P.frequency_grid(2400))
    assert out["coherence"] > 5


def test_signal_present_in_only_one_half_is_not_coherent():
    g = synth(amp=0.0, noise=0.03)
    late = g["mjd"] > g["mjd"].median()
    g.loc[late, "mag"] += 0.15 * np.sin(2 * np.pi * g.loc[late, "mjd"] / 0.3)
    out = P.search_source(g, P.frequency_grid(2400))
    assert out["coherence"] < 2


def test_band_whose_argmax_is_a_daily_alias_still_agrees():
    # g peaks on the daily alias but still shows the true period significantly
    g = synth(period_d=0.3, amp=0.2)
    out = P.search_source(g, P.frequency_grid(2400))
    assert out["bands_agree"]


def test_period_absent_from_one_band_does_not_agree():
    g = synth(period_d=0.3, amp=0.2)
    g.loc[g.filtercode == "zg", "mag"] = 18 + np.random.default_rng(5).normal(0, 0.03, (g.filtercode == "zg").sum())
    out = P.search_source(g, P.frequency_grid(2400))
    assert not out["bands_agree"]
