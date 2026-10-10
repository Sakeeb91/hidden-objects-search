"""The phase-curve test may only exclude when it could have seen the signal."""
import numpy as np
import pytest

b02 = pytest.importorskip("b02_survivor_phasecurve")

QUIET_NULL = np.full(200, 20.0)  # null amplitudes ~20 ppm: very sensitive data
LOUD_NULL = np.full(200, 2000.0)  # null amplitudes ~2000 ppm: hopeless data


def test_empty_null_is_never_a_verdict():
    assert b02.harmonic_verdict(400.0, 0.0, 400.0, []) == "insensitive"


def test_absent_signal_in_sensitive_data_excludes():
    assert b02.harmonic_verdict(400.0, 30.0, 410.0, QUIET_NULL) == "excludes"


def test_present_signal_in_sensitive_data_is_consistent():
    assert b02.harmonic_verdict(400.0, 380.0, 410.0, QUIET_NULL) == "consistent"


def test_noisy_data_cannot_exclude_even_with_zero_measurement():
    # This is the bug the first version had: loose recovery let noise "confirm" things.
    assert b02.harmonic_verdict(400.0, 0.0, 450.0, LOUD_NULL) == "insensitive"


def test_failed_injection_blocks_exclusion():
    assert b02.harmonic_verdict(400.0, 0.0, 5.0, QUIET_NULL) == "insensitive"


def test_combine_prefers_exclusion_then_consistency():
    assert b02.combine("excludes", "insensitive").startswith("excluded")
    assert b02.combine("insensitive", "consistent").startswith("not_excluded")
    assert b02.combine("insensitive", "insensitive").startswith("untested")
