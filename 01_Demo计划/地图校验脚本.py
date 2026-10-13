# -*- coding: utf-8 -*-
"""
余烬商队 · 地图校验脚本
--------------------------------
用法：
    python 地图校验脚本.py 地图坐标.json

检查项：
  1. 地点数量是否符合蓝图（大城1/小城2/城镇12/驿站4+8/村庄20/遗迹2+2）
  2. 不可通行（山/水）占比
  3. 连通性：从大城出发，是否每个地点都走得到（BFS）
  4. 距离：各地点到最近补给点距离、大城到最远地点距离
  5. 孤立区域：有没有被山水封死的片区
  6. 输出 40×40 ASCII 缩略图，方便人眼快速看形状
"""
import json
import sys
from collections import deque

W = H = 200
EXPECT = {
    'big': ('大城', 1),
    'small': ('小城', 2),
    'town': ('城镇', 12),
    'inn1': ('驿站(有节点)', 4),
    'inn0': ('驿站(损坏)', 8),
    'village': ('村庄', 20),
    'ruinW': ('遗迹(武器)', 2),
    'ruinM': ('遗迹(手册)', 2),
}
SUPPLY = {'big', 'small', 'town', 'inn1', 'inn0', 'village'}   # 能补给/落脚的地点
MARK = {
    'big': 'A', 'small': 'B', 'town': 'T',
    'inn1': 'N', 'inn0': 'n', 'village': 'v',
    'ruinW': 'W', 'ruinM': 'M',
}


def is_block(t):
    """不可通行：block(山)、blk_mt(山地)、blk_wt(水)、blk_ru(废墟)
       可通行：blk_fr(桥/林地)——专门用来跨河"""
    return t in ('block', 'blk_mt', 'blk_wt', 'blk_ru')


def parse_compact(text):
    """解析编辑器生成的紧凑文本：每行  类型|x|y区间
       例： blk_wt|100|0-49,53-117       blk_fr|100|51-52,119-120
            big|10|10                    village|120|90
    """
    blocked, btype, spots = set(), {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or '|' not in line:
            continue
        parts = line.split('|')
        if len(parts) < 3:
            continue
        t, xs, ys = parts[0].strip(), parts[1].strip(), parts[2].strip()
        try:
            x = int(xs)
        except ValueError:
            continue
        for run in ys.split(','):
            run = run.strip()
            if not run:
                continue
            if '-' in run:
                a, b = run.split('-')
            else:
                a, b = run, run
            try:
                y0, y1 = int(a), int(b)
            except ValueError:
                continue
            for y in range(y0, y1 + 1):
                if is_block(t):
                    blocked.add((x, y))
                    btype[(x, y)] = t
                elif t == 'blk_fr':
                    btype[(x, y)] = t
                else:
                    spots[(x, y)] = t
    return spots, blocked, btype


def load(path):
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    locs = d.get('locations', [])
    blocked = set()
    btype = {}
    spots = {}
    for o in locs:
        x, y, t = int(o['x']), int(o['y']), o['t']
        if is_block(t):
            blocked.add((x, y))
            btype[(x, y)] = t
        elif t == 'blk_fr':
            btype[(x, y)] = t          # 桥：可通行，但要画出来
        else:
            spots[(x, y)] = t
    return spots, blocked, btype


def neighbors(p):
    x, y = p
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < W and 0 <= ny < H:
            yield nx, ny


def bfs(start, blocked):
    """返回 dist 字典：start 到每个可达格的步数"""
    dist = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        for nb in neighbors(cur):
            if nb in dist or nb in blocked:
                continue
            dist[nb] = dist[cur] + 1
            q.append(nb)
    return dist


def main(path):
    if path.lower().endswith('.json'):
        spots, blocked, btype = load(path)
    else:
        with open(path, encoding='utf-8') as f:
            spots, blocked, btype = parse_compact(f.read())
    print('=' * 56)
    print('地图校验报告')
    print('=' * 56)

    # 1. 数量核对
    cnt = {}
    for t in spots.values():
        cnt[t] = cnt.get(t, 0) + 1
    print('\n【1】地点数量')
    for k, (name, exp) in EXPECT.items():
        got = cnt.get(k, 0)
        flag = 'OK ' if got == exp else ('⚠️ ' if got else '❌ ')
        print('  %s %-14s %2d / 期望 %2d' % (flag, name, got, exp))
    other = {k: v for k, v in cnt.items() if k not in EXPECT}
    if other:
        print('  其他类型：', other)

    # 2. 地形占比
    total = W * H
    print('\n【2】地形')
    print('  不可通行格：%d / %d  = %.1f%%' % (len(blocked), total, 100.0 * len(blocked) / total))

    # 3. 连通性（以大城为起点）
    bigs = [p for p, t in spots.items() if t == 'big']
    if not bigs:
        print('\n❌ 没有大城，无法做连通性检查')
    else:
        origin = bigs[0]
        dist = bfs(origin, blocked)
        reach = [p for p in spots if p in dist]
        lost = [p for p in spots if p not in dist]
        print('\n【3】连通性（起点 = 大城 %s）' % (origin,))
        print('  可通行区域：%d 格' % len(dist))
        print('  能走到的地点：%d / %d' % (len(reach), len(spots)))
        if lost:
            print('  ❌ 走不到的地点：')
            for p in sorted(lost):
                print('     %s (%s) @ %s' % (MARK.get(spots[p], '?'), spots[p], p))
        else:
            print('  ✅ 所有地点互通')

        # 4. 距离
        print('\n【4】距离（格数；按 2 格/天换算约 ÷2 天）')
        far = max(dist[p] for p in reach)
        farp = max(reach, key=lambda p: dist[p])
        print('  大城 → 最远地点：%d 格（%s @ %s）≈ %d 天' % (far, MARK.get(spots[farp], '?'), farp, far // 2))
        # 每个地点到「最近的其他落脚点」
        print('\n  各地点到最近落脚点的距离（超过补给续航就要挨饿）：')
        worst = []
        for p in sorted(spots):
            others = [q for q in spots if q != p]
            if not others:
                continue
            dd = bfs(p, blocked)
            near = min((dd[q] for q in others if q in dd), default=None)
            if near is None:
                print('     %s@%s  孤立！' % (MARK.get(spots[p], '?'), p))
            else:
                worst.append((near, p))
        worst.sort(reverse=True)
        for near, p in worst[:8]:
            print('     %-2s @ %-10s 最近 %3d 格 ≈ %3d 天' % (
                MARK.get(spots[p], '?'), str(p), near, near // 2))

        # 5. 片区检查
        seen = set(dist)
        if len(seen) < (total - len(blocked)):
            print('\n【5】⚠️ 存在与主地图不相连的片区（%d 格被山水隔开）'
                  % ((total - len(blocked)) - len(seen)))
        else:
            print('\n【5】✅ 没有孤立片区')

    # 6. ASCII 缩略图
    print('\n【6】缩略图（每 5 格 = 1 字符；# 山 ~ 水 · 空地）')
    S = 5
    grid = [['·'] * (W // S) for _ in range(H // S)]
    tally = {}
    for (x, y), t in btype.items():
        c = tally.setdefault((x // S, y // S), {})
        c[t] = c.get(t, 0) + 1
    for (cx, cy), c in tally.items():
        top = max(c, key=c.get)
        grid[cy][cx] = {'blk_wt': '~'}.get(top, '=' if top == 'blk_fr' else '#')
    for (x, y), t in spots.items():
        grid[y // S][x // S] = MARK.get(t, '?')
    print('    ' + ''.join(str((i * S) // 100 % 10) for i in range(0, W // S, 5)))
    for j, row in enumerate(grid):
        print('%-3d %s' % (j * S, ''.join(row)))
    print('\n图例：A大城 B小城 T城镇 N/n驿站 v村庄 W/M遗迹 | #山 ~水 =桥/林地 ·空地')
    print('=' * 56)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法：python 地图校验脚本.py 地图坐标.json')
        sys.exit(1)
    main(sys.argv[1])
