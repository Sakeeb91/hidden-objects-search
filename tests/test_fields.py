"""Review 1 C1: the field table must survive a CSV round trip with every kind intact."""
import pandas as pd
import pytest

from hos import fields as F


def test_committed_table_has_all_three_kinds():
    df = F.read_fields()
    c = F.counts(df)
    assert c["offsource"] > 0 and c["target"] > 0 and c["control"] > 0


def test_round_trip_keeps_kinds(tmp_path):
    df = pd.DataFrame({"field": ["a", "b", "c"], "kind": ["target", "offsource", "control"],
                       "parent": ["x", "y", "z"], "ra": [1.0, 2, 3], "dec": [0.0, 0, 0],
                       "a95": [0.1] * 3, "b95": [0.1] * 3, "pa95": [0.0] * 3})
    p = tmp_path / "f.csv"
    df.to_csv(p, index=False)
    assert F.read_fields(p)["kind"].tolist() == ["target", "offsource", "control"]


@pytest.mark.parametrize("kind", ["null", "", "NaN"])
def test_unknown_or_missing_kind_is_refused(tmp_path, kind):
    p = tmp_path / "f.csv"
    pd.DataFrame({"field": ["a"], "kind": [kind], "ra": [1.0], "dec": [0.0], "a95": [0.1],
                  "b95": [0.1], "pa95": [0.0]}).to_csv(p, index=False)
    with pytest.raises(ValueError):
        F.read_fields(p)


def test_plain_pandas_would_have_lost_the_old_null_kind(tmp_path):
    # Documents the trap: this is exactly what happened before the fix.
    p = tmp_path / "f.csv"
    pd.DataFrame({"kind": ["null"]}).to_csv(p, index=False)
    assert pd.read_csv(p)["kind"].isna().all()


def test_cached_empty_answer_round_trips(tmp_path, monkeypatch):
    from hos import archives as A
    monkeypatch.setattr(A, "CACHE", tmp_path)
    first = A.cached_frame("t", ["k"], lambda: pd.DataFrame())
    second = A.cached_frame("t", ["k"], lambda: (_ for _ in ()).throw(AssertionError("refetched")))
    assert first.empty and second.empty
