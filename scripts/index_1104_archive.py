"""给 1104 归档（含嵌套分卷 zip）里的每个文件算 SHA-256，写出索引，供按 SHA 补齐缺失网格。

用法：python index_1104_archive.py <_archive_work 目录> <输出 json>
只读归档，不解压到磁盘。
"""
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

root, out = Path(sys.argv[1]), Path(sys.argv[2])
index = {}   # sha -> [outer, inner, path, bytes]
for outer in sorted(root.glob("Assets_*.zip")) + sorted(root.glob("v55_*.zip")):
    z = zipfile.ZipFile(outer)
    for n in z.namelist():
        data = z.read(n)
        targets = [(n, data)]
        if n.endswith(".zip"):
            try:
                inner = zipfile.ZipFile(io.BytesIO(data))
                targets = [(m, inner.read(m)) for m in inner.namelist() if not m.endswith("/")]
                for m, b in targets:
                    index.setdefault(hashlib.sha256(b).hexdigest(), [outer.name, n, m, len(b)])
                continue
            except zipfile.BadZipFile:
                pass
        for m, b in targets:
            index.setdefault(hashlib.sha256(b).hexdigest(), [outer.name, "", m, len(b)])
    print(outer.name, len(index), flush=True)
out.write_text(json.dumps(index))
print("files", len(index))
