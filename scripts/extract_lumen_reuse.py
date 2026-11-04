"""从 lumen-lab-archive 的原样分卷还原薄切片复用资产（#3）。

用法：python3 -I scripts/extract_lumen_reuse.py <modeliing1104 目录> <输出目录>
Panda 另从 Menagerie 上游取（见 REUSE_INVENTORY.md），本脚本不联网。
"""

import hashlib
import io
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

WANT = {
    "Assets_08_imager_waste_pedestals.zip": ["project/plate_imager_p0/", "project/robot_pedestal_lumen_v02/"],
    "Assets_03_small_lab_versions.zip": ["shared/small_lab_lumen_v1/"],
    "Assets_10_integrated_scene_versions_UNVERIFIED.zip": [
        "project/passaging_p3_presettle_fullflow_revision_v3/",
        "project/passaging_p3_visual_pipeline/",
        "project/passaging_p3_verified_visual_v3/",
        "project/passaging_integration_p3/",
    ],
    "Assets_11_third.zip": ["project/robot_transfer_g0_20261103/"],
}
WHOLE_INNER = {  # Assets_13 中整包解出的内层 zip
    "Assets_13_latest_candidates_and_increments.zip": [
        "lumen_incubator_P1_B_candidate_for_review.zip",
        "01_P3_visual_delta_and_keyframe_data.zip",
    ]
}


def reassemble(src: Path, name: str) -> zipfile.ZipFile:
    parts = sorted(src.glob(name + ".part*"))
    return zipfile.ZipFile(io.BytesIO(b"".join(p.read_bytes() for p in parts)))


def write(out: Path, rel: str, data: bytes) -> None:
    assert ".." not in rel.split("/") and not rel.startswith("/"), rel
    dst = out / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)


def main(src: Path, out: Path) -> None:
    for outer, prefixes in WANT.items():
        oz = reassemble(src, outer)
        for inner in oz.namelist():
            iz = zipfile.ZipFile(io.BytesIO(oz.read(inner)))
            for m in iz.namelist():
                if not m.endswith("/") and any(m.startswith(p) for p in prefixes):
                    write(out, m.split("/", 1)[1], iz.read(m))
    for outer, inners in WHOLE_INNER.items():
        oz = reassemble(src, outer)
        for inner in inners:
            iz = zipfile.ZipFile(io.BytesIO(oz.read(inner)))
            for m in iz.namelist():
                if not m.endswith("/"):
                    write(out, m, iz.read(m))
    # 观察站的 culture_plate 子集未随包：按清单 SHA 从 sixwell 补回
    cp = out / "plate_imager_p0/assets/culture_plate"
    sw = out / "small_lab_lumen_v1/sixwell"
    manifest = json.loads((cp / "INTEGRATION_SUBSET_MANIFEST.json").read_text())
    for f in manifest["files"]:
        s, d = sw / f["path"], cp / f["path"]
        if d.exists():
            continue
        if hashlib.sha256(s.read_bytes()).hexdigest() != f["sha256"]:
            sys.exit(f"SHA 不符：{s}")
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(s, d)
    print("完成：", out)


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
