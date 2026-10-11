import pytest

a10 = pytest.importorskip("a10_population")


def test_permutation_test_exact_small_case():
    # one quartet with counts (target 3; members 3,0,0,0): P(sum >= 3) = 1/4
    r = a10.permutation_test([(3, [3, 0, 0, 0])])
    assert r["p_excess"] == pytest.approx(0.25)
    assert r["expected"] == pytest.approx(0.75)


def test_permutation_test_identical_members_gives_p_one():
    r = a10.permutation_test([(2, [2, 2, 2, 2]), (1, [1, 1, 1, 1])])
    assert r["p_excess"] == pytest.approx(1.0) and r["p_deficit"] == pytest.approx(1.0)


def test_n95_matches_independent_audit():
    # Review 3: eps = 51/70 and 40/48 with 7 fields containing survivors -> 14 and 11
    assert a10.n95(51 / 70, 7) == 14
    assert a10.n95(40 / 48, 7) == 11
