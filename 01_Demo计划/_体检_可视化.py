# -*- coding: utf-8 -*-
"""生成新版400地图PNG + 含驿站的补给覆盖分析（纯标准库PNG）"""
import zlib, struct
from collections import deque, defaultdict

W = H = 400
SRC = "地图坐标_400新版_20260911.txt"

blocked = set()
locs = []
kind = {}          # (x,y) -> type
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    t, rest = line.split("|", 1)
    xs, ys = rest.split("|")
    x = int(xs)
    for seg in ys.split(","):
        if "-" in seg:
            a, b = (int(v) for v in seg.split("-"))
        else:
            a = b = int(seg)
        if t in ("block", "blk_wt", "blk_ru", "blk_mt"):
            for yy in range(a, b + 1):
                blocked.add((x, yy))
                kind[(x, yy)] = t
        elif t == "blk_fr":
            for yy in range(a, b + 1):
                kind[(x, yy)] = t
        else:
            for yy in range(a, b + 1):
                locs.append((t, x, yy))
                kind[(x, yy)] = t

def passable(x, y):
    return 0 <= x < W and 0 <= y < H and (x, y) not in blocked

# ---------- PNG 绘制 ----------
SC = 2  # 每格2px -> 800x800
COL = {
    "grass": (222, 232, 205), "blk_wt": (61, 111, 168), "blk_mt": (110, 98, 87),
    "blk_ru": (138, 114, 86), "block": (52, 73, 94), "blk_fr": (79, 122, 58),
    "big": (192, 57, 43), "small": (230, 126, 34), "town": (241, 196, 15),
    "inn1": (39, 174, 96), "inn0": (149, 165, 166), "village": (93, 173, 226),
    "ruinL": (142, 68, 173), "ruinS": (72, 201, 176),
}
img = [[COL["grass"]] * (W * SC) for _ in range(H * SC)]
LOC_TYPES = {"big", "small", "town", "inn1", "inn0", "village", "ruinL", "ruinS"}
for y in range(H):
    for x in range(W):
        c = COL.get(kind.get((x, y)))
        if c:
            for dy in range(SC):
                for dx in range(SC):
                    img[y * SC + dy][x * SC + dx] = c
# 地点画大标记（居中 7x7 px），便于肉眼看清
MK = {"big": 14, "small": 11, "town": 9, "inn1": 9, "inn0": 7, "village": 5, "ruinL": 11, "ruinS": 8}
for t, x, y in locs:
    cx, cy = x * SC + SC // 2, y * SC + SC // 2
    h = MK[t] // 2
    c = COL[t]
    for py in range(cy - h, cy - h + MK[t]):
        for px in range(cx - h, cx - h + MK[t]):
            if 0 <= py < H * SC and 0 <= px < W * SC:
                img[py][px] = c

raw = bytearray()
for row in img:
    raw.append(0)
    for px in row:
        raw += bytes(px)

def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W * SC, H * SC, 8, 2, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
png += chunk(b"IEND", b"")
open("地图预览_400新版.png", "wb").write(png)
print("PNG 已生成: 地图预览_400新版.png  (800x800)")

# ---------- 含驿站的补给覆盖 ----------
supply = [(x, y) for t, x, y in locs if t in ("big", "small", "town", "village", "inn1", "inn0")]
dist = {}
q = deque()
for s in supply:
    dist[s] = 0; q.append(s)
while q:
    x, y = q.popleft(); d = dist[(x, y)]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x + dx, y + dy
        if passable(nx, ny) and (nx, ny) not in dist:
            dist[(nx, ny)] = d + 1; q.append((nx, ny))
vals = list(dist.values())
print()
print("【补给覆盖 · 含驿站】")
print(f"  补给点(含驿站): {len(supply)}")
print(f"  通行格到最近补给: 最大 {max(vals)} 格 ≈ {max(vals)/2:.0f} 天, 中位 {sorted(vals)[len(vals)//2]} 格")
# 每格>90格(45天)的通行格占比 = 补给荒漠
far = sum(1 for v in vals if v > 90)
print(f"  距补给 >90格(45天) 的通行格: {far} ({far/len(vals)*100:.1f}%)")

# 驿站服务半径
st = [(x, y) for t, x, y in locs if t in ("inn1", "inn0")]
sd = {}; q = deque()
for s in st:
    sd[s] = 0; q.append(s)
while q:
    x, y = q.popleft(); d = sd[(x, y)]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x + dx, y + dy
        if passable(nx, ny) and (nx, ny) not in sd:
            sd[(nx, ny)] = d + 1; q.append((nx, ny))
nv = list(sd.values())
print()
print("【驿站服务半径】(最近驿站距离)")
print(f"  最大 {max(nv)} 格 ≈ {max(nv)/2:.0f} 天, 中位 {sorted(nv)[len(nv)//2]} 格")
for th in (60, 80, 100, 120):
    c = sum(1 for v in nv if v > th)
    print(f"  距最近驿站 >{th}格({th//2}天) 的通行格: {c} ({c/len(nv)*100:.1f}%)")

# 每个遗迹到最近驿站/村庄
print()
print("【遗迹获取难度】到最近驿站 & 最近补给")
NAME = {"ruinL": "大遗迹", "ruinS": "小遗迹"}
for t, x, y in locs:
    if t in ("ruinL", "ruinS"):
        print(f"  {NAME[t]}({x:>3},{y:>3}) 最近驿站 {sd.get((x,y))} 格({sd.get((x,y))/2:.0f}天) | 最近补给 {dist.get((x,y))} 格({dist.get((x,y))/2:.0f}天)")
