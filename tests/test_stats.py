import numpy as np
import pytest
from scipy.stats import poisson

from hos import stats as S


def test_zero_null_count_never_gives_p_zero():
    # Review 1 C3: plug-in Poisson with lambda = 0 gave p = 0 for a single event
    assert poisson.sf(0, 0.0) == 0.0
    assert S.nb_predictive_p(1, 0, 51) > 0.005
    assert S.matched_binomial_p(1, 0, 3) == pytest.approx(0.25)


def test_nb_predictive_matches_independent_audit_value():
    # Review 2: C = 51 over 51 fields, Jeffreys prior, P(Y >= 5) = 0.00428
    assert S.nb_predictive_p(5, 51, 51) == pytest.approx(0.00428, rel=0.01)


def test_nb_predictive_is_wider_than_plugin_poisson():
    assert S.nb_predictive_p(5, 51, 51) > poisson.sf(4, 1.0)


def test_matched_binomial_exact_values():
    assert S.matched_binomial_p(0, 5, 3) == 1.0
    assert S.matched_binomial_p(3, 0, 3) == pytest.approx(0.25**3)
    # doubling target exposure doubles the odds q/(1-q)
    assert S.matched_binomial_p(1, 0, 3, exposure_ratio=2.0) == pytest.approx(0.4)


def test_holm_controls_and_is_monotone():
    adj = S.holm([0.01, 0.04, 0.03, 0.5])
    assert adj[0] == pytest.approx(0.04)
    assert np.all(adj >= np.array([0.01, 0.04, 0.03, 0.5]))
    assert adj.max() <= 1.0


def test_dispersion_index_poisson_near_one():
    rng = np.random.default_rng(0)
    assert S.dispersion_index(rng.poisson(2.0, 5000)) == pytest.approx(1.0, abs=0.08)
