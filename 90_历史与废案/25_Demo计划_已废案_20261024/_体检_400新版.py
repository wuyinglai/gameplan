# -*- coding: utf-8 -*-
"""400x400 新版地图体检：连通性 / 地形分流 / 驿站间距 / 补给覆盖 / 城市距离"""
import math
from collections import deque, defaultdict

W = H = 400
SRC = "地图坐标_400新版_20260911.txt"

blocked = set()
locs = []          # (type, x, y)
raw_terrain = defaultdict(list)

for line in open(SRC, encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    t, rest = line.split("|", 1)
    xs, ys = rest.split("|")
    x = int(xs)
    segs = ys.split(",")
    if t in ("block", "blk_wt", "blk_ru", "blk_mt"):
        for seg in segs:
            a, b = (seg.split("-") + [seg])[:2] if "-" in seg else (seg, seg)
            a, b = int(a), int(b)
            for yy in range(a, b + 1):
                blocked.add((x, yy))
            raw_terrain[t].append((x, a, b))
    elif t == "blk_fr":
        for seg in segs:
            a, b = (seg.split("-") + [seg])[:2] if "-" in seg else (seg, seg)
            raw_terrain["blk_fr"].append((x, int(a), int(b)))
    else:
        for seg in segs:
            if "-" in seg:
                a, b = seg.split("-")
                for yy in range(int(a), int(b) + 1):
                    locs.append((t, x, yy))
            else:
                locs.append((t, x, int(seg)))

# ---------- 基础统计 ----------
by_type = defaultdict(list)
for t, x, y in locs:
    by_type[t].append((x, y))

print("=" * 60)
print("【1】地点统计（对照编辑器上限）")
LIM = {"big": 1, "small": 2, "town": 12, "inn1": 4, "inn0": 8, "village": 50, "ruinL": 5, "ruinS": 10}
NAME = {"big": "大城", "small": "小城", "town": "城镇", "inn1": "驿站(有节点)",
        "inn0": "驿站(损坏)", "village": "村庄", "ruinL": "大遗迹", "ruinS": "小遗迹"}
for k in ["big", "small", "town", "inn1", "inn0", "village", "ruinL", "ruinS"]:
    n = len(by_type[k]); lim = LIM[k]
    flag = "OK" if n <= lim else "⚠️超限!"
    print(f"  {NAME[k]:<12} {n:>3} / 上限 {lim:<3} {flag}")
total_loc = sum(len(v) for v in by_type.values())
print(f"  地点合计: {total_loc}")

# ---------- 地形占比 ----------
terr_cells = len(blocked)
print()
print("=" * 60)
print("【2】地形占比（不可通行格 / 全图）")
print(f"  不可通行: {terr_cells} 格 = {terr_cells/(W*H)*100:.2f}%")
for k in ["blk_wt", "blk_mt", "blk_ru", "block", "blk_fr"]:
    c = sum(b - a + 1 for _, a, b in raw_terrain[k])
    if c:
        print(f"    {k:<8}: {c} 格 ({c/(W*H)*100:.2f}%)")

# ---------- 连通性 BFS ----------
def passable(x, y):
    return 0 <= x < W and 0 <= y < H and (x, y) not in blocked

def bfs(start):
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        d = dist[(x, y)]
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if passable(nx, ny) and (nx, ny) not in dist:
                dist[(nx, ny)] = d+1
                q.append((nx, ny))
    return dist

big = by_type["big"][0]
D = bfs(big)
print()
print("=" * 60)
print("【3】连通性（从大城 200,200 出发）")
unreach = []
for t, x, y in locs:
    if (x, y) not in D:
        unreach.append((NAME[t], x, y))
if unreach:
    print(f"  ⚠️ 有 {len(unreach)} 个地点不可达:")
    for n, x, y in unreach:
        print(f"     {n} ({x},{y})")
else:
    print("  ✅ 全部地点可达，无孤岛")
print(f"  可达格总数: {len(D)} / 可通过格 {W*H-terr_cells}")

# ---------- 驿站间距 ----------
print()
print("=" * 60)
print("【4】驿站间距（用户基准：正常 ~30天 ≈ 60格）")
inns = [(t, x, y) for t, x, y in locs if t in ("inn1", "inn0")]
def bfs_to(sx, sy, targets):
    # 单源 BFS，遇到 target 记录
    dist = {(sx, sy): 0}
    q = deque([(sx, sy)])
    res = {}
    tset = set(targets)
    while q:
        x, y = q.popleft()
        if (x, y) in tset and (x, y) != (sx, sy):
            res[(x, y)] = dist[(x, y)]
        d = dist[(x, y)]
        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nx, ny = x+dx, y+dy
            if passable(nx, ny) and (nx, ny) not in dist:
                dist[(nx, ny)] = d+1
                q.append((nx, ny))
    return res
pts = [(x, y) for _, x, y in inns]
print("  每个驿站到最近驿站的步数（格）:")
rows = []
for i, (t, x, y) in enumerate(inns):
    others = [p for j, p in enumerate(pts) if j != i]
    dd = bfs_to(x, y, others)
    near = min(dd.values()) if dd else None
    rows.append((NAME[t], x, y, near))
    tag = ""
    if near is None:
        tag = " ⚠️无其他驿站可达"
    elif near > 80:
        tag = " ⚠️偏远(>40天)"
    print(f"    {NAME[t]:<12}({x:>3},{y:>3}) 最近驿站 {near} 格 ≈ {near/2:.0f} 天{tag}")
vals = [r[3] for r in rows if r[3] is not None]
if vals:
    print(f"  最近邻间距: 最小 {min(vals)} / 中位 {sorted(vals)[len(vals)//2]} / 最大 {max(vals)} 格")
    print(f"  最大间距 ≈ {max(vals)/2:.0f} 天")

# ---------- 城市间距离 & 订单档 ----------
print()
print("=" * 60)
print("【5】城市距离（4向BFS步数；移动=1格/次）")
cities = [("big", "大城")] + [("small", "小城") for _ in by_type["small"]]
cpts = [by_type["big"][0]] + by_type["small"]
for i in range(len(cpts)):
    for j in range(i + 1, len(cpts)):
        a, b = cpts[i], cpts[j]
        d = bfs_to(a[0], a[1], [b]).get(b)
        man = abs(a[0]-b[0]) + abs(a[1]-b[1])
        if d:
            print(f"  ({a[0]},{a[1]}) → ({b[0]},{b[1]}): {d} 格 ≈ {d/2:.0f} 天  (直线曼哈顿 {man}, 绕路系数 {d/man:.3f})")
        else:
            print(f"  ({a[0]},{a[1]}) → ({b[0]},{b[1]}): ⚠️不可达! (直线曼哈顿 {man})")

# ---------- 补给覆盖 ----------
print()
print("=" * 60)
print("【6】补给点覆盖（村庄/城镇/城市 视为补给点）")
supply = [(x, y) for t, x, y in locs if t in ("big", "small", "town", "village")]
dist = {}
q = deque()
for s in supply:
    dist[s] = 0
    q.append(s)
while q:
    x, y = q.popleft()
    d = dist[(x, y)]
    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
        nx, ny = x+dx, y+dy
        if passable(nx, ny) and (nx, ny) not in dist:
            dist[(nx, ny)] = d+1
            q.append((nx, ny))
reach_vals = [v for k, v in dist.items()]
uncovered = (W*H-terr_cells) - len(dist)
print(f"  补给点数量: {len(supply)}")
print(f"  到最近补给: 最大 {max(reach_vals)} 格 ≈ {max(reach_vals)/2:.0f} 天 (中位 {sorted(reach_vals)[len(reach_vals)//2]})")
print(f"  无补给可达的通行格: {uncovered} ({uncovered/(W*H-terr_cells)*100:.1f}%)")
# 每个非补给地点到最近补给的距离
print("  各非补给地点到最近补给距离（>30格≈15天 提示）:")
for t, x, y in locs:
    if t in ("big", "small", "town", "village"):
        continue
    d = dist.get((x, y))
    tag = " ⚠️" if d and d > 30 else ""
    print(f"    {NAME[t]:<12}({x:>3},{y:>3}) 距离 {d} 格 ≈ {d/2:.0f} 天{tag}" if d is not None else f"    {NAME[t]:<12}({x:>3},{y:>3}) ⚠️不可达")

# ---------- 大城周边 ----------
print()
print("=" * 60)
print("【7】大城周边情况")
bx, by = big
print(f"  大城 ({bx},{by}) 到大城最近补给距离:", dist.get((bx, by)))
# 大城周围 12 格内有无障碍
sur = 0
for dx in range(-12, 13):
    for dy in range(-12, 13):
        if (bx+dx, by+dy) in blocked:
            sur += 1
print(f"  大城周围 ±12 格内障碍格: {sur}")
