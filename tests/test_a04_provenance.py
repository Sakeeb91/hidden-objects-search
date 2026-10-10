"""Review 2: cached period tables must be regenerated when their inputs change."""
import numpy as np
import pandas as pd
import pytest

a04 = pytest.importorskip("a04_period_search")


@pytest.fixture
def env(tmp_path, monkeypatch):
    from hos import ztf
    monkeypatch.setattr(a04, "OUT", tmp_path / "periods")
    monkeypatch.setattr(ztf, "CACHE", tmp_path / "ztf")
    (tmp_path / "ztf").mkdir()
    return tmp_path / "ztf" / "f1.csv.gz"


def write_raw(path, amp):
    rng = np.random.default_rng(0)
    t = np.sort(rng.uniform(58200, 60600, 200))
    pd.DataFrame({"oid": 1, "mjd": t, "mag": 18 + amp * np.sin(2 * np.pi * t / 0.3),
                  "magerr": 0.02, "filtercode": "zr", "ra": 10.0, "dec": 5.0,
                  "limitmag": 21.0}).to_csv(path, index=False, compression="gzip")


def test_second_run_is_cached_and_changed_raw_data_is_recomputed(env):
    write_raw(env, 0.2)
    assert a04.run_field("f1")["status"] == "ok"
    assert a04.run_field("f1")["status"] == "cached"
    write_raw(env, 0.0)  # raw light curves changed
    assert a04.run_field("f1")["status"] == "ok"


def test_table_without_provenance_is_recomputed(env):
    write_raw(env, 0.2)
    a04.run_field("f1")
    (a04.OUT / "f1.provenance.json").unlink()
    assert a04.run_field("f1")["status"] == "ok"
