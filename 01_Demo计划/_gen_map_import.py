# -*- coding: utf-8 -*-
import json, os

base = os.path.dirname(os.path.abspath(__file__))
txt_path = os.path.join(base, "地图坐标.txt")
html_path = os.path.join(base, "地图编辑器_200x200.html")
out_json = os.path.join(base, "地图坐标_导入用.json")
out_html = os.path.join(base, "地图编辑器_200x200_当前布局.html")

# ---- 1. 解析 compact 文本 -> locations ----
locs = []
with open(txt_path, encoding="utf-8") as f:
    for ln in f:
        ln = ln.strip()
        if not ln or "|" not in ln:
            continue
        t, xs, ys = ln.split("|")
        x = int(xs)
        for tok in ys.split(","):
            tok = tok.strip()
            if "-" in tok:
                a, b = map(int, tok.split("-"))
                for y in range(a, b + 1):
                    locs.append({"t": t, "x": x, "y": y})
            else:
                locs.append({"t": t, "x": x, "y": int(tok)})

print("解析到地点/地形格数:", len(locs))

# ---- 2. 导出编辑器可导入的 JSON ----
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"width": 200, "height": 200, "locations": locs}, f,
              ensure_ascii=False, separators=(",", ":"))

# ---- 3. 生成"已载入当前布局"的编辑器副本 ----
html = open(html_path, encoding="utf-8").read()

seed_json = json.dumps(locs, ensure_ascii=False, separators=(",", ":"))
seed_const = (
    "\n/* 预载：localStorage 为空时，用当前地图坐标.txt 数据填充（原工具不变，此副本便于直接改） */\n"
    "const SEED = " + seed_json + ";\n"
    "function seedFromData(){\n"
    "  grid.clear();\n"
    "  SEED.forEach(o=>{ if(TMAP[o.t]) grid.set(o.x+','+o.y, o.t); });\n"
    "}\n"
)
anchor = "const TMAP = {}; TYPES.forEach(t=>TMAP[t.k]=t);"
assert anchor in html, "找不到注入锚点"
html = html.replace(anchor, anchor + seed_const, 1)

# load() 在 localStorage 为空时改用 SEED
old_load = (
    "function load(){\n"
    "  try{\n"
    "    const s=localStorage.getItem(LSK); if(!s) return;"
)
new_load = (
    "function load(){\n"
    "  try{\n"
    "    const s=localStorage.getItem(LSK); if(!s){ seedFromData(); return; }"
)
assert old_load in html, "找不到 load() 锚点"
html = html.replace(old_load, new_load, 1)

open(out_html, "w", encoding="utf-8").write(html)
print("已生成:", os.path.basename(out_html))
print("已生成:", os.path.basename(out_json))
