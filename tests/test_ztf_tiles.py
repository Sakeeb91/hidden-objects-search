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
