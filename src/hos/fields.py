"""The Track A field table: one validated reader for every stage.

Lesson from review 1 (C1): pandas parses the string "null" as missing, which silently
erased every null field. Kinds are now 'target', 'offsource', 'control', and the reader
disables NA parsing for text columns and refuses unknown or missing kinds.
"""
import pandas as pd

from hos.paths import RESULTS

FIELDS_CSV = RESULTS / "trackA" / "a02_fields.csv"
KINDS = {"target", "offsource", "control"}


def read_fields(path=FIELDS_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, keep_default_na=False, na_values={"ra": [""], "dec": [""]})
    bad = set(df["kind"]) - KINDS
    if bad or df["kind"].eq("").any():
        raise ValueError(f"unexpected field kinds: {sorted(bad)}")
    for col in ("ra", "dec", "a95", "b95", "pa95"):
        df[col] = pd.to_numeric(df[col], errors="raise")
    for col in ("true_ra", "true_dec", "true_pb_h", "true_gmag", "gaia_density"):
        if col in df:
            df[col] = pd.to_numeric(df[col].replace("", None), errors="coerce")
    return df


def counts(df: pd.DataFrame) -> dict:
    return {k: int((df["kind"] == k).sum()) for k in sorted(KINDS)}
