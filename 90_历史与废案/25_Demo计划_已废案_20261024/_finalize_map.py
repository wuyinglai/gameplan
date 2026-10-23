# -*- coding: utf-8 -*-
"""删除山体顶部凸出的4格，并把成品地图保存为正式坐标文件 + 生成导入JSON"""
import json, os, shutil

base = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(base, "地图坐标_400新版_20260911.txt")
official = os.path.join(base, "地图坐标.txt")
backup = os.path.join(base, "地图坐标_200x200_旧.txt")
out_json = os.path.join(base, "地图坐标_400导入用.json")

REMOVE = {  # 类型 -> 要删掉的格
    "blk_mt": {(197, 318), (197, 319), (198, 316), (198, 317)},
}

lines = open(src, encoding="utf-8").read().splitlines()
out_lines = []
removed = 0
for ln in lines:
    s = ln.strip()
    if not s or s.count("|") < 2:
        out_lines.append(ln)
        continue
    t, xs, ys = s.split("|")
    if t not in REMOVE:
        out_lines.append(ln)
        continue
    x = int(xs)
    killed = {(x, y) for (xx, y) in REMOVE[t] if xx == x}
    if not killed:
        out_lines.append(ln)
        continue
    keep = []
    for tok in ys.split(","):
        if "-" in tok:
            a, b = (int(v) for v in tok.split("-"))
        else:
            a = b = int(tok)
        for y in range(a, b + 1):
            if (x, y) in killed:
                removed += 1
            else:
                keep.append(y)
    if not keep:
        continue
    # 重新压成 区间
    keep.sort()
    segs = []
    i = 0
    while i < len(keep):
        j = i
        while j + 1 < len(keep) and keep[j + 1] == keep[j] + 1:
            j += 1
        segs.append(str(keep[i]) if i == j else f"{keep[i]}-{keep[j]}")
        i = j + 1
    out_lines.append(f"{t}|{x}|{','.join(segs)}")

print(f"删除格数: {removed} (应为 4)")
assert removed == 4, "删除数量不对！"

text = "\n".join(out_lines) + "\n"
open(src, "w", encoding="utf-8").write(text)          # 更新工作文件
if not os.path.exists(backup) and os.path.exists(official):
    shutil.copy2(official, backup)
    print("旧 200×200 地图已备份 →", os.path.basename(backup))
open(official, "w", encoding="utf-8").write(text)     # 正式坐标文件
print("正式坐标已写入:", os.path.basename(official))

# ---- 生成编辑器导入 JSON ----
locs = []
for ln in out_lines:
    s = ln.strip()
    if not s or s.count("|") < 2:
        continue
    t, xs, ys = s.split("|")
    x = int(xs)
    for tok in ys.split(","):
        if "-" in tok:
            a, b = (int(v) for v in tok.split("-"))
        else:
            a = b = int(tok)
        for y in range(a, b + 1):
            locs.append({"t": t, "x": x, "y": y})
json.dump({"width": 400, "height": 400, "locations": locs},
          open(out_json, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"导入JSON已生成: {os.path.basename(out_json)}  共 {len(locs)} 格")
