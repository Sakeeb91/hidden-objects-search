import numpy as np

from hos.sky import in_ellipse, sep_arcsec


def test_major_axis_north_south():
    # a = 0.1 deg along PA 0 (north), b = 0.02 deg
    assert in_ellipse(10.0, 0.09, 10.0, 0.0, 0.1, 0.02, 0.0)
    assert not in_ellipse(10.09, 0.0, 10.0, 0.0, 0.1, 0.02, 0.0)


def test_major_axis_east_west():
    assert in_ellipse(10.09, 0.0, 10.0, 0.0, 0.1, 0.02, 90.0)
    assert not in_ellipse(10.0, 0.09, 10.0, 0.0, 0.1, 0.02, 90.0)


def test_ra_wraparound_and_cos_dec():
    assert in_ellipse(359.99, 60.0, 0.01, 60.0, 0.02, 0.02, 0.0)
    assert np.isclose(sep_arcsec(1.0, 60.0, 0.0, 60.0), 1800.0, rtol=1e-3)


def test_edge_is_outside_just_beyond():
    assert not in_ellipse(10.0, 0.1001, 10.0, 0.0, 0.1, 0.1, 0.0)
