# -*- coding: utf-8 -*-
import json, os

base = os.path.dirname(os.path.abspath(__file__))
txt_path = os.path.join(base, "地图坐标.txt")
html_path = os.path.join(base, "地图编辑器_200x200.html")
out_json = os.path.join(base, "地图坐标_400导入用.json")
out_html = os.path.join(base, "地图编辑器_400x400.html")

S = 2  # 放大倍数：200 -> 400

# 地形类：每格扩成 S×S 实心块，保持山脉/水域不断裂
TERRAIN = {"block", "blk_wt", "blk_mt", "blk_ru", "blk_fr"}

# ---- 1. 解析 compact 文本 -> 放大后的 locations ----
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
                ys_ = range(a, b + 1)
            else:
                ys_ = [int(tok)]
            for y in ys_:
                if t in TERRAIN:
                    for dx in range(S):
                        for dy in range(S):
                            locs.append({"t": t, "x": x * S + dx, "y": y * S + dy})
                else:
                    locs.append({"t": t, "x": x * S, "y": y * S})

print("放大后地点/地形格数:", len(locs))
mx = max(o["x"] for o in locs); my = max(o["y"] for o in locs)
print("坐标最大值 x,y =", mx, my, "(应在 0-399 内)")

# ---- 2. 导出编辑器可导入的 JSON ----
with open(out_json, "w", encoding="utf-8") as f:
    json.dump({"width": 400, "height": 400, "locations": locs}, f,
              ensure_ascii=False, separators=(",", ":"))

# ---- 3. 生成 400×400 编辑器副本（预载放大后的布局）----
html = open(html_path, encoding="utf-8").read()

# 3a. 网格尺寸
assert "const W = 200, H = 200;" in html
html = html.replace("const W = 200, H = 200;", "const W = 400, H = 400;")

# 3b. 标题
html = html.replace("余烬商队 · 200×200 地图编辑器", "余烬商队 · 400×400 地图编辑器")

# 3c. 提示文案（范围）
html = html.replace("范围 0–199。", "范围 0–399。")

# 3d. 默认格子大小：400 宽地图用更小默认值看得更全
html = html.replace('<input type="range" id="zoom" min="3" max="14" value="6">',
                    '<input type="range" id="zoom" min="3" max="14" value="4">')
html = html.replace('<b id="zoomV">6</b>', '<b id="zoomV">4</b>')

# 3e. 导出 Markdown 里的说明
html = html.replace("测试版地图坐标（200×200，用户手工指定）",
                    "测试版地图坐标（400×400，用户手工指定）")
html = html.replace("「地图编辑器_200x200.html」导出", "「地图编辑器_400x400.html」导出")

# 3f. 本地存档 key
html = html.replace("'ember_caravan_map_200'", "'ember_caravan_map_400'")

# 3g. 注入预载 SEED
seed_json = json.dumps(locs, ensure_ascii=False, separators=(",", ":"))
seed_const = (
    "\n/* 预载：localStorage 为空时，用当前地图坐标.txt(×2放大)数据填充 */\n"
    "const SEED = " + seed_json + ";\n"
    "function seedFromData(){\n"
    "  grid.clear();\n"
    "  SEED.forEach(o=>{ if(TMAP[o.t]) grid.set(o.x+','+o.y, o.t); });\n"
    "}\n"
)
anchor = "const TMAP = {}; TYPES.forEach(t=>TMAP[t.k]=t);"
assert anchor in html, "找不到注入锚点"
html = html.replace(anchor, anchor + seed_const, 1)

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
