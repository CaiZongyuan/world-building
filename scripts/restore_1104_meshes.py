"""按 SHA 补齐 1104 资产 MJCF 引用的缺失网格。

用法：python restore_1104_meshes.py <archive_work> <资产目录> <mjcf 相对路径>... 
步骤：解析 MJCF 引用的网格 → 找出缺失的 → 从资产自带清单查 SHA → 在 INDEX_SHA256.json 里按 SHA 取回；
清单里没有 SHA 的，按路径尾部匹配并标为 name_match（未经 SHA 核对）。结果写 <资产目录>/RESTORE_REPORT.json。
"""
import hashlib, io, json, re, sys, zipfile
from pathlib import Path

work, asset = Path(sys.argv[1]), Path(sys.argv[2])
xmls = [asset / x for x in sys.argv[3:]]
index = json.loads((work / "INDEX_SHA256.json").read_text())
by_tail = {}
for sha, (o, i, p, n) in index.items():
    parts = p.split("/")
    for k in range(1, 4):
        by_tail.setdefault("/".join(parts[-k:]), []).append(sha)

# 资产自带清单里的 路径 → SHA
known = {}
for mf in list(asset.rglob("*.json")):
    try:
        d = json.loads(mf.read_text())
    except Exception:
        continue
    def walk(o):
        if isinstance(o, dict):
            sha = o.get("sha256")
            for key in ("path", "file", "mesh"):
                if isinstance(o.get(key), str) and isinstance(sha, str) and len(sha) == 64:
                    known[Path(o[key]).as_posix()] = sha
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(d)
for sf in list(asset.rglob("*SHA256SUMS*.txt")):
    for line in sf.read_text().splitlines():
        m = re.match(r"([0-9a-f]{64})\s+\*?(.+)", line.strip())
        if m:
            known[m.group(2)] = m.group(1)

cache = {}
def fetch(sha):
    o, i, p, _ = index[sha]
    z = zipfile.ZipFile(work / o)
    if i:
        key = (o, i)
        if key not in cache:
            cache.clear(); cache[key] = zipfile.ZipFile(io.BytesIO(z.read(i)))
        return cache[key].read(p)
    return z.read(p)

report = {"asset": asset.name, "files": {}}
for x in xmls:
    txt = x.read_text()
    md = re.search(r'meshdir="([^"]*)"', txt)
    base = (x.parent / (md.group(1) if md else "")).resolve()
    for f in sorted(set(re.findall(r'file="([^"]+\.(?:obj|stl|msh|OBJ|STL))"', txt))):
        dst = (base / f).resolve()
        rel = dst.relative_to(asset.resolve()).as_posix() if str(dst).startswith(str(asset.resolve())) else str(dst)
        if dst.exists():
            report["files"][rel] = "present"; continue
        sha = None
        for k, v in known.items():
            if k.endswith(Path(f).as_posix().lstrip("./")) or k.endswith(rel):
                sha = v; break
        how = None
        if sha and sha in index:
            how = "sha"
        else:
            tail = "/".join(Path(f).parts[-2:])
            cands = by_tail.get(tail) or by_tail.get(Path(f).name) or []
            if len(set(cands)) == 1:
                sha, how = cands[0], "name_match"
            elif cands:
                how = f"ambiguous({len(set(cands))})"
        if how in ("sha", "name_match"):
            data = fetch(sha)
            assert hashlib.sha256(data).hexdigest() == sha
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(data)
            report["files"][rel] = how
        else:
            report["files"][rel] = how or "missing"
from collections import Counter
report["summary"] = dict(Counter(v if not v.startswith("ambiguous") else "ambiguous" for v in report["files"].values()))
(asset / "RESTORE_REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
print(asset.name, report["summary"])
