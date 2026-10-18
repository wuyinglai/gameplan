#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《余烬商队》单元01 · 测试夹具地图生成（最小版）
-----------------------------------------------------
🔴 用途：**项目主正式地图还没画好之前的占位地图**
   - 400×400 纯空地，只有三座城 + 一条河 + 几座山
   - 🔴 只保证「能走、能测时间/体力/跨日/不可通行」，🔴 **不保证路线平衡**
   - 项目主画完真地图后，直接换 src/b01/地图.json 即可，代码不用改

🔴 坐标约定：(0,0) 在左下，x 向右、y 向上 —— 与施工图 §3.5.2 一致
输出：地图.json（格式与地图编辑器导出完全一致）
"""
import json, os, random

W = H = 400
SEED = 20261018          # 🔴 固定种子 = 每次生成结果一样，测试可复现

CITY_A = (60, 60)        # 大城（起点）
CITY_B = (180, 150)      # 小城甲 —— 直线约 150 格
CITY_C = (330, 300)      # 小城乙 —— B→C 约 250 格，A→C 约 380 格

grid = [[None] * W for _ in range(H)]
L = []


def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def put(x, y, t):
    grid[y][x] = t
    L.append({'t': t, 'x': x, 'y': y})


# ---------------- 地形 ----------------
def gen_mountains():
    """少量山簇 —— 够 TC-01-015（不可通行）用就行"""
    random.seed(SEED)
    for _ in range(30):
        cx = random.randint(20, W - 21)
        cy = random.randint(20, H - 21)
        r = random.randint(3, 9)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = cx + dx, cy + dy
                if not inb(x, y) or grid[y][x] is not None:
                    continue
                d = (dx * dx + dy * dy) ** 0.5
                if d <= r and random.random() < 0.85 - 0.35 * d / r:
                    put(x, y, 'block')


def gen_river(bridge_xs):
    """一条斜河 + 5 个桥"""
    random.seed(SEED + 1)
    for x in range(0, W):
        base = int(H * 0.16 + H * 0.60 * (x / (W - 1)))
        wob = int(8 * (random.random() - 0.5))
        for dy in range(-1, 2):
            y = base + wob + dy
            if inb(x, y) and grid[y][x] is None:
                put(x, y, 'blk_wt')
    for x in bridge_xs:
        for y in range(H):
            if grid[y][x] == 'blk_wt':
                grid[y][x] = 'blk_fr'
                L[:] = [c for c in L if not (c['x'] == x and c['y'] == y and c['t'] == 'blk_wt')]
                L.append({'t': 'blk_fr', 'x': x, 'y': y})


# ---------------- BFS（只用于量距离 / 铺路） ----------------
BLOCK = {'block', 'blk_wt'}


def blocked(x, y):
    return grid[y][x] in BLOCK


def bfs(src):
    from collections import deque
    dist = [[-1] * W for _ in range(H)]
    prev = [[None] * W for _ in range(H)]
    sx, sy = src
    dist[sy][sx] = 0
    q = deque([(sx, sy)])
    while q:
        x, y = q.popleft()
        d = dist[y][x]
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if not inb(nx, ny) or blocked(nx, ny) or dist[ny][nx] >= 0:
                continue
            dist[ny][nx] = d + 1
            prev[ny][nx] = (x, y)
            q.append((nx, ny))
    return dist, prev


def path_of(prev, dst):
    x, y = dst
    out = []
    while True:
        out.append((x, y))
        nxt = prev[y][x]
        if nxt is None:
            break
        x, y = nxt
    return out


# ---------------- 主流程 ----------------
def main():
    outdir = os.path.dirname(os.path.abspath(__file__))
    gen_mountains()
    gen_river([70, 150, 230, 310, 380])

    # 城周围清空（别被山围死）
    for (cx, cy) in (CITY_A, CITY_B, CITY_C):
        for dy in range(-16, 17):
            for dx in range(-16, 17):
                x, y = cx + dx, cy + dy
                if inb(x, y):
                    grid[y][x] = None

    put(CITY_A[0], CITY_A[1], 'big')
    put(CITY_B[0], CITY_B[1], 'small')
    put(CITY_C[0], CITY_C[1], 'small')

    cities = {'AB': (CITY_A, CITY_B), 'BC': (CITY_B, CITY_C), 'AC': (CITY_A, CITY_C)}

    print('=== 距离实测 ===')
    for key, (a, b) in cities.items():
        d, p = bfs(a)
        dist = d[b[1]][b[0]]
        pth = path_of(p, b)
        for i, (x, y) in enumerate(pth):
            if i and grid[y][x] is None:
                put(x, y, 'road')
        for i in range(70, len(pth) - 30, 70):
            x, y = pth[len(pth) - 1 - i]
            if grid[y][x] in ('road', None):
                put(x, y, 'inn1')
        print('  %-3s %4d 格  (15/格 = %d 点· %.0f 天)' % (key, dist, dist * 15, dist / 3.0))

    # 输出
    order = ['big', 'small', 'inn1', 'road', 'blk_fr', 'block', 'blk_wt']
    L.sort(key=lambda c: (order.index(c['t']) if c['t'] in order else 99, c['x'], c['y']))

    obj = {
        'map': {'width': W, 'height': H},
        'note': ('🔴 占位测试地图（项目主正式地图未交付前的临时夹具）。'
                 'big=大城 small=小城 inn1=驿站 road=商路 blk_fr=桥/林地(可通行) '
                 'block=山(不可通行) blk_wt=水(不可通行)。'
                 '🔴 不保证路线平衡，只保证能测时间/体力/跨日/不可通行。'
                 '换正式地图时直接替换本文件，代码不用改。'),
        'locations': L,
    }
    p = os.path.join(outdir, '地图.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

    from collections import Counter
    c = Counter(q['t'] for q in L)
    print('=== 统计 ===')
    for k in order:
        if c[k]:
            print('  %-8s %d' % (k, c[k]))
    print('输出: %s' % p)


if __name__ == '__main__':
    main()