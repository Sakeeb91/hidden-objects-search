"""Count statistics for comparing target fields with off-source fields.

Replaces the pooled plug-in Poisson test, which treated the null rate as exactly known,
gave p = 0 whenever the null count was zero, ignored field-to-field variation and did
not correct for 17 targets (review 1 C3/M2; review 2 question 5).
"""
import numpy as np
from scipy.stats import binom, nbinom


def matched_binomial_p(y: int, c: int, n_null: int, exposure_ratio: float = 1.0) -> float:
    """Exact conditional test of one target against its own matched null fields.

    With a common local Poisson rate, Y | (Y + C) ~ Binomial(Y + C, q), where
    q = E_target / (E_target + sum E_null) = 1 / (1 + n_null / exposure_ratio).
    Returns P(Y >= y). y = 0 gives 1."""
    if y <= 0:
        return 1.0
    q = 1.0 / (1.0 + n_null / exposure_ratio)
    return float(binom.sf(y - 1, y + c, q))


def nb_predictive_p(y: int, c_total: int, n_fields: int, a0: float = 0.5, b0: float = 0.0) -> float:
    """Posterior-predictive P(Y >= y) for one new field given C events in n equal fields.

    lambda | C ~ Gamma(a0 + C, b0 + n) (Jeffreys a0 = 1/2, b0 = 0), so
    Y_new ~ NegBin(r = a0 + C, p = (b0 + n) / (b0 + n + 1)). Finite even when C = 0."""
    if y <= 0:
        return 1.0
    r = a0 + c_total
    p = (b0 + n_fields) / (b0 + n_fields + 1.0)
    return float(nbinom.sf(y - 1, r, p))


def holm(pvals) -> np.ndarray:
    """Holm step-down adjusted p-values (family-wise error control)."""
    p = np.asarray(pvals, dtype=float)
    m = p.size
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


def dispersion_index(counts) -> float:
    """Variance / mean of null-field counts (1 for Poisson; > 1 means overdispersed)."""
    c = np.asarray(counts, dtype=float)
    return float(c.var(ddof=1) / c.mean()) if c.size > 1 and c.mean() > 0 else float("nan")
