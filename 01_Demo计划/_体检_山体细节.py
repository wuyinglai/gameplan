# -*- coding: utf-8 -*-
"""放大底部山体区域 + 找"缺口/卡口"，并测有/无缺口的路程差"""
import zlib, struct
from collections import deque

W = H = 400
SRC = "地图坐标_400新版_20260911.txt"
blocked = set(); kind = {}; locs = []
for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line: continue
    t, rest = line.split("|", 1); xs, ys = rest.split("|"); x = int(xs)
    for seg in ys.split(","):
        a, b = (int(v) for v in seg.split("-")) if "-" in seg else (int(seg), int(seg))
        if t in ("block", "blk_wt", "blk_ru", "blk_mt"):
            for yy in range(a, b + 1): blocked.add((x, yy)); kind[(x, yy)] = t
        elif t == "blk_fr":
            for yy in range(a, b + 1): kind[(x, yy)] = t
        else:
            for yy in range(a, b + 1): locs.append((t, x, yy)); kind[(x, yy)] = t

def pf(x, y, extra=None):
    if not (0 <= x < W and 0 <= y < H): return False
    if (x, y) in blocked: return False
    if extra and (x, y) in extra: return False
    return True

def bfs(a, b, extra=None):
    if not pf(*a, extra) or not pf(*b, extra): return None
    dist = {a: 0}; q = deque([a])
    while q:
        c = q.popleft()
        if c == b: return dist[c]
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            n = (c[0]+dx, c[1]+dy)
            if pf(*n, extra) and n not in dist:
                dist[n] = dist[c]+1; q.append(n)
    return None

# ---- 放大底部山体区域 x:110-300, y:285-399 ----
x0, x1, y0, y1 = 110, 300, 285, 399
SC = 5
COL = {"blk_wt":(61,111,168),"blk_mt":(96,86,76),"blk_fr":(79,122,58),
       "big":(192,57,43),"small":(230,126,34),"town":(241,196,15),"inn1":(39,174,96),
       "inn0":(149,165,166),"village":(93,173,226),"ruinL":(142,68,173),"ruinS":(72,201,176)}
cw, ch = (x1-x0+1)*SC, (y1-y0+1)*SC
img = [[(226,235,210)]*cw for _ in range(ch)]
for y in range(y0, y1+1):
    for x in range(x0, x1+1):
        k = kind.get((x, y))
        c = COL.get(k)
        if c:
            for dy in range(SC):
                for dx in range(SC):
                    img[(y-y0)*SC+dy][(x-x0)*SC+dx] = c
# 地点放大标记
MK = {"big":16,"small":13,"town":11,"inn1":13,"inn0":11,"village":7,"ruinL":11,"ruinS":9}
for t, x, y in locs:
    if x0 <= x <= x1 and y0 <= y <= y1:
        cx, cy = (x-x0)*SC+SC//2, (y-y0)*SC+SC//2; h = MK[t]//2
        for py in range(cy-h, cy-h+MK[t]):
            for px in range(cx-h, cx-h+MK[t]):
                if 0 <= py < ch and 0 <= px < cw: img[py][px] = COL[t]
raw = bytearray()
for row in img:
    raw.append(0)
    for px in row: raw += bytes(px)
def chunk(tag, d): return struct.pack(">I", len(d)) + tag + d + struct.pack(">I", zlib.crc32(tag+d) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", cw, ch, 8, 2, 0, 0, 0)) \
      + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
open("地图_底部山体放大.png", "wb").write(png)
print(f"已生成 地图_底部山体放大.png  区域 x{x0}-{x1} y{y0}-{y1} ({cw}x{ch})")

# ---- 找山体卡口（可通行格，左右都是山 或 上下都是山）----
MT = {"blk_mt"}
def is_mt(x, y): return kind.get((x, y)) in MT
chokes = []
for y in range(y0, y1+1):
    for x in range(x0, x1+1):
        if (x, y) in blocked: continue
        hz = is_mt(x-1, y) and is_mt(x+1, y)
        vt = is_mt(x, y-1) and is_mt(x, y+1)
        if hz or vt: chokes.append((x, y, "横" if hz else "纵"))
print()
print(f"【山体卡口/缝隙】 共 {len(chokes)} 个:")
for x, y, d in chokes:
    print(f"  ({x},{y}) {d}向缝隙")

# ---- 有/无缝隙的路程差 ----
south = None
for t, x, y in locs:
    if t == "small" and y > 300: south = (x, y)
big = (200, 200)
d0 = bfs(big, south)
# 把缝隙堵上一半再测
extra = set((x, y) for x, y, _ in chokes)
d1 = bfs(big, south, extra)
print()
print(f"【大城{big} → 小城南{south}】")
print(f"  现状(有缝隙): {d0} 格 ≈ {d0/2:.0f} 天")
print(f"  若封死所有缝隙: {d1} 格 ≈ {d1/2:.0f} 天")
if d1 and d0:
    print(f"  缝隙带来的捷径收益: {d1-d0} 格 ≈ {(d1-d0)/2:.0f} 天")
