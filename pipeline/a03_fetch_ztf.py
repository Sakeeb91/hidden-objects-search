"""Track A stage 3: download ZTF light curves for every field (cached, resumable).

Each field is a cone of radius a95 (the 95% ellipse semi-major axis) around its centre.
Order: controls, then nulls, then targets, so the calibration data exist first.

Writes data/ztf/<field>.csv.gz and results/trackA/a03_fetch_log.csv.
Usage: uv run python pipeline/a03_fetch_ztf.py [WORKERS]
"""
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from hos import ztf
from hos.paths import RESULTS

ORDER = {"control": 0, "null": 1, "target": 2}


def fetch(row):
    t = time.time()
    try:
        df = ztf.cone(row.ra, row.dec, row.a95, row.field)
        return {"field": row.field, "kind": row.kind, "status": "ok",
                "n_points": len(df), "n_objects": df["oid"].nunique() if len(df) else 0,
                "seconds": round(time.time() - t, 1)}
    except Exception as e:  # recorded, never silently dropped
        return {"field": row.field, "kind": row.kind, "status": f"error: {e}"[:200],
                "n_points": 0, "n_objects": 0, "seconds": round(time.time() - t, 1)}


def main():
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    fields = pd.read_csv(RESULTS / "trackA" / "a02_fields.csv")
    fields = fields.sort_values("kind", key=lambda s: s.map(ORDER))
    log = []
    with ThreadPoolExecutor(workers) as pool:
        futs = [pool.submit(fetch, r) for r in fields.itertuples()]
        for i, f in enumerate(as_completed(futs), 1):
            rec = f.result()
            log.append(rec)
            print(f"[{i}/{len(futs)}] {rec['field']}: {rec['status']} "
                  f"{rec['n_objects']} obj {rec['seconds']}s", flush=True)
    out = pd.DataFrame(log).sort_values("field")
    out.to_csv(RESULTS / "trackA" / "a03_fetch_log.csv", index=False)
    bad = out[out["status"] != "ok"]
    print(f"done: {len(out) - len(bad)} ok, {len(bad)} failed")
    if len(bad):
        sys.exit(1)


if __name__ == "__main__":
    main()
