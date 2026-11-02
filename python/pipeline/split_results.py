"""Split a results Parquet into parts under a size limit, with a manifest (rows and SHA256 per part).
python -m python.pipeline.split_results outputs/full/results_python_full.parquet outputs/full/results_parts"""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
import pyarrow.parquet as pq

LIMIT = 90 * 1024 * 1024


def split(src: str, dst: str, limit: int = LIMIT) -> dict:
    f = pq.ParquetFile(src); d = Path(dst); d.mkdir(parents=True, exist_ok=True)
    total = f.metadata.num_rows; size = Path(src).stat().st_size
    nparts = max(1, int(size * 1.3 // limit) + 1)  # 30% margin for compression differences
    per = -(-total // nparts); parts, w, rows, i = [], None, 0, 0
    def close():
        nonlocal w
        if w:
            w.close(); p = d / f"part_{i:05d}.parquet"
            parts.append({"file": p.name, "rows": rows, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
            w = None
    for b in f.iter_batches(batch_size=200_000):
        if w is None:
            w = pq.ParquetWriter(d / f"part_{i:05d}.parquet", f.schema_arrow, compression="zstd", compression_level=9); rows = 0
        w.write_batch(b); rows += b.num_rows
        if rows >= per:
            close(); i += 1
    close()
    m = {"source": Path(src).name, "rows": total, "parts": parts, "note": "SYNTHETIC data. Read the folder as one Parquet dataset."}
    (d / "manifest.json").write_text(json.dumps(m, indent=2))
    assert all(p["bytes"] < limit for p in parts), "a part is over the limit"
    assert sum(p["rows"] for p in parts) == total
    return m


if __name__ == "__main__":
    print(json.dumps(split(sys.argv[1], sys.argv[2]), indent=2))
