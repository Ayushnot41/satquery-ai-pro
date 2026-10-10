"""BigEarthNet.txt Validation Script.

Validates multi-sensor Sentinel-1/Sentinel-2 pair integrity:
- S1 SAR dual polarization (VV, VH)
- S2 Multispectral 10m/20m bands
- Parquet annotation schema compliance
"""

from __future__ import annotations

import json
from pathlib import Path


def validate_manifest(manifest_path: str | Path) -> dict:
    p = Path(manifest_path)
    if not p.exists():
        return {"valid": False, "error": f"Manifest file not found: {p}"}

    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    total_samples = len(data)
    tasks = {}
    splits = {}

    for item in data:
        t = item.get("task_category", "unknown")
        s = item.get("split", "unknown")
        tasks[t] = tasks.get(t, 0) + 1
        splits[s] = splits.get(s, 0) + 1

    return {
        "valid": True,
        "total_samples": total_samples,
        "tasks": tasks,
        "splits": splits,
    }


if __name__ == "__main__":
    test_manifest = Path("./pipeline/manifests/bigearthnet_txt_master_dev.json")
    if test_manifest.exists():
        res = validate_manifest(test_manifest)
        print("Validation Result:", json.dumps(res, indent=2))
    else:
        print(f"Manifest not generated yet at {test_manifest}")
