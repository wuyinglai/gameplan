# -*- coding: utf-8 -*-
"""驿站覆盖热力：每格按"到最近驿站的格数"上色，直观暴露空档"""
import zlib, struct
from collections import deque

W = H = 400
SC = 2
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

def pf(x, y): return 0 <= x < W and 0 <= y < H and (x, y) not in blocked

inns = [(x, y) for t, x, y in locs if t in ("inn1", "inn0")]
sd = {}; q = deque()
for s in inns: sd[s] = 0; q.append(s)
while q:
    x, y = q.popleft(); d = sd[(x, y)]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        n = (x+dx, y+dy)
        if pf(*n) and n not in sd: sd[n] = d+1; q.append(n)

def band(d):
    if d <= 60:  return (176, 214, 168)   # ≤30天 绿
    if d <= 100: return (245, 226, 138)   # 30-50天 黄
    if d <= 150: return (238, 172, 105)   # 50-75天 橙
    return (223, 118, 108)                # >75天 红

TERR = {"blk_wt": (61,111,168), "blk_mt": (96,86,76), "blk_ru": (138,114,86), "block": (52,73,94), "blk_fr": (79,122,58)}
img = [[(176,214,168)] * (W*SC) for _ in range(H*SC)]
for y in range(H):
    for x in range(W):
        c = TERR.get(kind.get((x, y))) or band(sd.get((x, y), 999))
        for dy in range(SC):
            for dx in range(SC):
                img[y*SC+dy][x*SC+dx] = c

COL = {"big":(192,57,43),"small":(230,126,34),"town":(241,196,15),"inn1":(39,174,96),
       "inn0":(120,120,120),"village":(93,173,226),"ruinL":(142,68,173),"ruinS":(72,201,176)}
MK = {"big":14,"small":11,"town":9,"inn1":13,"inn0":11,"village":5,"ruinL":11,"ruinS":8}
for t, x, y in locs:
    cx, cy = x*SC+SC//2, y*SC+SC//2; h = MK[t]//2
    for py in range(cy-h, cy-h+MK[t]):
        for px in range(cx-h, cx-h+MK[t]):
            if 0 <= py < H*SC and 0 <= px < W*SC: img[py][px] = COL[t]

raw = bytearray()
for row in img:
    raw.append(0)
    for px in row: raw += bytes(px)
def chunk(tag, data):
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag+data) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W*SC, H*SC, 8, 2, 0, 0, 0)) \
      + chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
open("地图_驿站覆盖热力_400新版.png", "wb").write(png)
print("已生成: 地图_驿站覆盖热力_400新版.png")
print("配色: 绿=≤30天有驿站 / 黄=30-50天 / 橙=50-75天 / 红=>75天无驿站")
