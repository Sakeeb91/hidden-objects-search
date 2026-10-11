import pandas as pd
import pytest

from hos.archives import exact_int_column

BIG = 4458877679106027392


def test_plain_pandas_corrupts_big_ids_mixed_with_none():
    # Documents the trap found by review 3
    assert int(pd.Series([BIG, None]).iloc[0]) != BIG


def test_exact_int_column_keeps_19_digit_ids():
    col = exact_int_column([BIG, None, str(BIG)])
    assert col[0] == BIG and pd.isna(col[1]) and col[2] == BIG


def test_float_ids_are_refused():
    with pytest.raises(TypeError):
        exact_int_column([float(BIG)])
