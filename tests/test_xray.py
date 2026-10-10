import pytest

from hos import xray


def test_erass1_coverage_is_the_western_galactic_half():
    assert xray.erass1_covers(243.0) and not xray.erass1_covers(90.0)
    assert not xray.erass1_covers(359.99)


@pytest.mark.network
def test_known_redback_has_xray_counterparts():
    # PSR J1023+0038 (l = 243.5 deg) is a bright X-ray source in eRASS1 and 2SXPS
    m = xray.matches(155.94870, 0.64475, 243.49)
    assert m["erass1"] >= 1 and m["2sxps"] >= 1 and m["uniform_match"]


@pytest.mark.network
def test_no_coverage_is_none_not_zero():
    m = xray.matches(270.0, 66.56, 96.38)   # north ecliptic pole, l ~ 96 (eROSITA-RU half)
    assert m["erass1"] is None
