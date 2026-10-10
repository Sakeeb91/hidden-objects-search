"""Track A stage 4: period search on every source in every fetched field.

Identical code for targets, nulls and controls. Per-source tables are large and go to
data/trackA/periods/<field>.csv; a small per-field summary is committed.

Usage: uv run python pipeline/a04_period_search.py [WORKERS] [FIELD ...]
"""
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from hos import period as P
from hos import ztf
from hos.paths import DATA, RESULTS, ensure

OUT = DATA / "trackA" / "periods"


def run_field(field: str) -> dict:
    t0 = time.time()
    path = ensure(OUT) / f"{field}.csv"
    if path.exists():
        res = pd.read_csv(path)
        return {"field": field, "n_sources": len(res), "status": "cached", "seconds": 0}
    raw_path = ztf.CACHE / f"{field}.csv.gz"
    if not raw_path.exists():
        return {"field": field, "n_sources": 0, "status": "no_ztf_file", "seconds": 0}
    lc = pd.read_csv(raw_path)
    if lc.empty:
        pd.DataFrame().to_csv(path, index=False)
        return {"field": field, "n_sources": 0, "status": "empty_field", "seconds": 0}
    lc = P.group_sources(lc)
    freq = P.frequency_grid(float(np.ptp(lc["mjd"])))
    rows = []
    for src, g in lc.groupby("src"):
        r = P.search_source(g, freq)
        if r is not None:
            r["src"] = int(src)
            rows.append(r)
    res = pd.DataFrame(rows)
    res.insert(0, "field", field)
    res.to_csv(path, index=False, float_format="%.7g")
    return {"field": field, "n_sources": len(res), "status": "ok",
            "seconds": round(time.time() - t0, 1)}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    fields = sys.argv[2:] or pd.read_csv(RESULTS / "trackA" / "a02_fields.csv")["field"].tolist()
    with Pool(workers) as pool:
        log = []
        for rec in pool.imap_unordered(run_field, fields):
            log.append(rec)
            print(rec, flush=True)
    if len(sys.argv) <= 2:
        pd.DataFrame(log).sort_values("field").to_csv(
            RESULTS / "trackA" / "a04_search_log.csv", index=False)


if __name__ == "__main__":
    main()
