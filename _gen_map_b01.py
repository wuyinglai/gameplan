#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
《余烬商队》单元01 · 测试地图生成器
------------------------------------
1 座大城（灰原城）+ 2 座小城，三城两两连通 → 3 条商路
3 条路分别落在 短途 / 中途 / 长途 三档（🔴 允许小幅超出档位边界）

输出：地图编辑器可导入的 JSON（400×400）
"""
import json, os, random
from collections import deque, Counter

W = H = 400
SEED = 20261018

BLOCK_TYPES = {'block', 'blk_wt'}          # 不可通行
TYPE_NAME = {
    'big': '大城', 'small': '小城', 'town': '城镇', 'village': '村庄',
    'inn1': '驿站', 'special': '特殊建筑', 'road': '商路',
    'blk_fr': '桥/林地(可通行)', 'block': '山(不可通行)', 'blk_wt': '水(不可通行)',
}

# ---------- 三档目标（🔴 用户定：允许小幅超出边界，别离谱）----------
# 正式档：短途 ≤180 · 中途 181~360 · 长途 361~600
# 允许范围：短途 ≤205（+25） · 中途 ≤410（+50） · 长途 ≤650（+50）
ROUTES = [
    ('AB', 'short', 100, 205),
    ('BC', 'mid',   200, 410),
    ('AC', 'long',  380, 650),
]

CITY_A = (60, 60)          # 大城 · 灰原城（玩家起点）

grid = [[None] * W for _ in range(H)]
L = []


def inb(x, y):
    return 0 <= x < W and 0 <= y < H


def put(x, y, t):
    grid[y][x] = t
    L.append({'t': t, 'x': x, 'y': y})


def blocked(x, y):
    return grid[y][x] in BLOCK_TYPES


def clear_radius(cx, cy, r):
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            x, y = cx + dx, cy + dy
            if inb(x, y):
                grid[y][x] = None


# ---------------- 地形 ----------------
def gen_mountains():
    random.seed(SEED)
    for _ in range(80):
        cx = random.randint(6, W - 7)
        cy = random.randint(6, H - 7)
        r = random.randint(3, 13)
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                x, y = cx + dx, cy + dy
                if not inb(x, y) or grid[y][x] is not None:
                    continue
                d = (dx * dx + dy * dy) ** 0.5
                if d <= r and random.random() < 0.85 - 0.35 * d / r:
                    put(x, y, 'block')


def gen_river(bridge_xs):
    random.seed(SEED + 1)
    for x in range(0, W):
        base = int(H * 0.16 + H * 0.60 * (x / (W - 1)))
        wob = int(9 * (random.random() - 0.5))
        for dy in range(-2, 3):
            y = base + wob + dy
            if inb(x, y) and grid[y][x] is None and abs(dy) <= 1:
                put(x, y, 'blk_wt')
    # 桥：把指定列的河水换成可通行格
    for x in bridge_xs:
        for y in range(H):
            if grid[y][x] == 'blk_wt':
                grid[y][x] = 'blk_fr'
                L[:] = [c for c in L if not (c['x'] == x and c['y'] == y and c['t'] == 'blk_wt')]
                L.append({'t': 'blk_fr', 'x': x, 'y': y})


# ---------------- BFS ----------------
def bfs(src):
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


def measure(a, b):
    d, p = bfs(a)
    return d[b[1]][b[0]], p


# ---------------- 找城位 ----------------
def find_cities():
    """固定 A。只跑两次全图 BFS（A 一次、B 一次），其余全是查表。"""
    distA, _ = bfs(CITY_A)                      # A 到全图的距离

    # --- B：让 A-B 落在 short 档 ---
    lo, hi = ROUTES[0][2], ROUTES[0][3]
    mid = (lo + hi) // 2
    best_b, best_score = None, None
    for by in range(90, H - 90, 5):
        for bx in range(90, W - 90, 5):
            if abs(bx - CITY_A[0]) < 70 and abs(by - CITY_A[1]) < 70:
                continue
            d = distA[by][bx]
            if lo <= d <= hi:
                score = abs(d - mid)
                if best_score is None or score < best_score:
                    best_b, best_score = (bx, by), score
    if not best_b:
        return None
    city_b = best_b

    # --- C：让 B-C 落 mid、A-C 落 long ---
    distB, _ = bfs(city_b)
    m_lo, m_hi = ROUTES[1][2], ROUTES[1][3]
    l_lo, l_hi = ROUTES[2][2], ROUTES[2][3]
    m_mid = (m_lo + m_hi) // 2
    l_mid = (l_lo + l_hi) // 2
    best_c, best_score = None, None
    for cy in range(90, H - 90, 5):
        for cx in range(90, W - 90, 5):
            d1 = distB[cy][cx]
            if not (m_lo <= d1 <= m_hi):
                continue
            d2 = distA[cy][cx]
            if not (l_lo <= d2 <= l_hi):
                continue
            score = abs(d1 - m_mid) + abs(d2 - l_mid)
            if best_score is None or score < best_score:
                best_c, best_score = (cx, cy), score
    return city_b, best_c


# ---------------- 主流程 ----------------
def main():
    outdir = os.path.dirname(os.path.abspath(__file__))

    gen_mountains()
    gen_river([70, 140, 210, 280, 350])

    found = find_cities()
    if not found:
        print('FAIL: 找不到合法的 B/C 坐标')
        return
    city_b, city_c = found

    print('=== 城位 ===')
    print('  A 大城 灰原城 : %s' % (CITY_A,))
    print('  B 小城 甲     : %s' % (city_b,))
    print('  C 小城 乙     : %s' % (city_c,))

    # 城周围清空
    for c in (CITY_A, city_b, city_c):
        clear_radius(c[0], c[1], 14)

    put(CITY_A[0], CITY_A[1], 'big')
    put(city_b[0], city_b[1], 'small')
    put(city_c[0], city_c[1], 'small')

    cities = {'A': CITY_A, 'B': city_b, 'C': city_c}
    print('=== 三条商路 ===')
    all_ok = True
    for key, tier, lo, hi in ROUTES:
        a, b = cities[key[0]], cities[key[1]]
        d, p = measure(a, b)
        ok = lo <= d <= hi
        all_ok = all_ok and ok
        days = d / 3.0
        print('  %-3s %-6s %4d 格  (允许 %d~%d)  ≈%.0f 天  %s'
              % (key, tier, d, lo, hi, days, 'OK' if ok else '<<< 超范围'))

    # ---- 铺商路 + 沿途地点 ----
    for key, tier, lo, hi in ROUTES:
        a, b = cities[key[0]], cities[key[1]]
        d, p = measure(a, b)
        pth = path_of(p, b)          # 从 b 回到 a
        for i, (x, y) in enumerate(pth):
            if i == 0:
                continue
            if grid[y][x] is None:
                put(x, y, 'road')
        # 沿途每隔 45~60 格放一个歇脚点
        step = 55
        for i in range(step, len(pth) - step // 2, step):
            x, y = pth[len(pth) - 1 - i]
            if grid[y][x] in ('road', None):
                put(x, y, 'inn1')

    # ---- 额外撒一些村庄 / 城镇 / 特殊建筑（不在商路上）----
    random.seed(SEED + 7)
    distA, _ = bfs(CITY_A)

    def free_near(x, y, r=3):
        for dy in range(-r, r + 1):
            for dx in range(-r, r + 1):
                if grid[y + dy][x + dx] not in (None, 'road'):
                    return False
        return True

    placed = 0
    tries = 0
    while placed < 60 and tries < 20000:
        tries += 1
        x = random.randint(10, W - 11)
        y = random.randint(10, H - 11)
        if not free_near(x, y):
            continue
        dA = distA[y][x]
        if dA <= 0:
            continue
        r = random.random()
        if r < 0.62:
            t = 'village'
        elif r < 0.85:
            t = 'town'
        else:
            t = 'special'
        put(x, y, t)
        placed += 1

    # ---- 输出 ----
    order = ['big', 'small', 'town', 'village', 'inn1', 'special',
             'road', 'blk_fr', 'block', 'blk_wt']
    L.sort(key=lambda c: (order.index(c['t']) if c['t'] in order else 99, c['x'], c['y']))

    obj = {
        'map': {'width': W, 'height': H},
        'note': ('单元01 测试地图 · 1 大城(灰原城) + 2 小城，三城两两连通。'
                 '类型键：big=大城 small=小城 town=城镇 village=村庄 inn1=驿站 '
                 'special=特殊建筑 road=商路 blk_fr=桥/林地(可通行) '
                 'block=山(不可通行) blk_wt=水(不可通行)。'
                 '🔴 不可通行仅 block 与 blk_wt。数量不限。'),
        'locations': L,
    }
    p = os.path.join(outdir, '地图坐标_400_测试地图.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)

    c = Counter(q['t'] for q in L)
    print('=== 格子统计 ===')
    for k in order:
        if c[k]:
            print('  %-9s %-16s %5d' % (k, TYPE_NAME[k], c[k]))
    print('总格子数: %d' % len(L))
    print('输出: %s' % p)


if __name__ == '__main__':
    main()