import numpy as np

from hos import ztf


def covered(pt, centres, tile):
    return any(np.hypot((pt[0] - c[0]) * np.cos(np.radians(pt[1])), pt[1] - c[1]) <= tile
               for c in centres)


def test_small_cone_is_one_tile():
    assert ztf.tile_centres(10.0, 20.0, 0.02) == [(10.0, 20.0)]


def test_tiles_cover_every_point_of_a_large_cone():
    ra0, dec0, R = 150.0, 40.0, 0.19
    centres = ztf.tile_centres(ra0, dec0, R)
    rng = np.random.default_rng(0)
    for _ in range(2000):
        r, th = R * np.sqrt(rng.uniform()), rng.uniform(0, 2 * np.pi)
        pt = (ra0 + r * np.cos(th) / np.cos(np.radians(dec0)), dec0 + r * np.sin(th))
        assert covered(pt, centres, ztf.TILE_DEG)


def test_good_epochs_filter_counts_only_good_epochs():
    import pandas as pd
    rows = []
    for oid, n_good, n_bad in [(1, 45, 0), (2, 35, 20), (3, 40, 5)]:
        for k in range(n_good + n_bad):
            rows.append({"oid": oid, "mjd": float(k), "mag": 18.0, "magerr": 0.02,
                         "catflags": 0 if k < n_good else 4, "filtercode": "zr",
                         "ra": 1.0, "dec": 1.0, "limitmag": 21.0})
    out = ztf.good_epochs_filter(pd.DataFrame(rows))
    # object 2 has 55 epochs in total but only 35 good ones: it must be dropped
    assert sorted(out["oid"].unique()) == [1, 3]
    assert len(out) == 45 + 40
