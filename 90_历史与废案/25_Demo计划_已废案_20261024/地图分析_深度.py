# -*- coding: utf-8 -*-
"""
余烬商队 · 地图深度分析（在 地图校验脚本.py 基础上做三项专项检查）
  1. 绕路系数：实际最短路 / 曼哈顿距离，衡量障碍是否真的在分流商路
  2. 桥梁必要性：每座桥是不是唯一过河通道（割边/割点）
  3. 补给间距全表：每个落脚点到最近的「能补给点」多远
  4. 三城之间的实际路程（决定订单分档是否成立）
用法： python 地图分析_深度.py 地图坐标.txt
"""
import sys
from collections import deque

W = H = 200
NAME = {
    'big': '大城', 'small': '小城', 'town': '城镇',
    'inn1': '驿站·有节点', 'inn0': '驿站·损坏', 'village': '村庄',
    'ruinW': '遗迹·武器', 'ruinM': '遗迹·手册',
}
SUPPLY = {'big', 'small', 'town', 'inn1', 'inn0'}   # 只有这些能真正补给（村庄补给极少）


def is_block(t):
    return t in ('block', 'blk_mt', 'blk_wt', 'blk_ru')


def parse_compact(text):
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


def bfs(start, blocked):
    dist = {start: 0}
    q = deque([start])
    while q:
        cur = q.popleft()
        x, y = cur
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in dist and (nx, ny) not in blocked:
                dist[(nx, ny)] = dist[cur] + 1
                q.append((nx, ny))
    return dist


def main(path):
    with open(path, encoding='utf-8') as f:
        spots, blocked, btype = parse_compact(f.read())

    bigs = [p for p, t in spots.items() if t == 'big']
    origin = bigs[0]
    D = bfs(origin, blocked)

    print('=' * 60)
    print('【A】绕路系数（实际最短路 ÷ 曼哈顿距离，1.0 = 一路直走无阻挡）')
    print('=' * 60)
    rows = []
    for p in sorted(spots):
        if p == origin or p not in D:
            continue
        man = abs(p[0] - origin[0]) + abs(p[1] - origin[1])
        if man == 0:
            continue
        rows.append((D[p] / man, D[p], man, p))
    rows.sort(reverse=True)
    avg = sum(r[0] for r in rows) / len(rows)
    print('  平均绕路系数：%.3f' % avg)
    print('  最绕的 8 个（数值越大 = 被山水逼着绕路）：')
    for k, d, man, p in rows[:8]:
        print('    %-12s @ %-10s  实际 %3d 格 / 直线 %3d  = %.2f  (≈%d 天)'
              % (NAME[spots[p]], str(p), d, man, k, d // 2))
    print('  最顺的 5 个：')
    for k, d, man, p in rows[-5:]:
        print('    %-12s @ %-10s  实际 %3d 格 / 直线 %3d  = %.2f  (≈%d 天)'
              % (NAME[spots[p]], str(p), d, man, k, d // 2))

    print()
    print('=' * 60)
    print('【B】桥梁必要性（blk_fr 桥/林地，检查是否为唯一通道）')
    print('=' * 60)
    bridges = sorted(p for p, t in btype.items() if t == 'blk_fr')
    print('  桥/林地共 %d 格' % len(bridges))
    # 把桥按连通块分组
    seen = set()
    groups = []
    for b in bridges:
        if b in seen:
            continue
        grp = [b]
        seen.add(b)
        q = deque([b])
        while q:
            c = q.popleft()
            for n in ((c[0] + 1, c[1]), (c[0] - 1, c[1]), (c[0], c[1] + 1), (c[0], c[1] - 1)):
                if n in bridges and n not in seen:
                    seen.add(n)
                    grp.append(n)
                    q.append(n)
        groups.append(grp)
    for i, grp in enumerate(groups, 1):
        ys = [g[1] for g in grp]
        xs = [g[0] for g in grp]
        print('  桥组%d：%d 格  x=%d~%d y=%d~%d' % (i, len(grp), min(xs), max(xs), min(ys), max(ys)))
        # 封死这座桥，看连通性有没有变化
        blocked2 = set(blocked) | set(grp)
        D2 = bfs(origin, blocked2)
        lost = [p for p in spots if p not in D2]
        if lost:
            print('    ⚠️ 封死后有 %d 个地点到不了：%s'
                  % (len(lost), ', '.join('%s@%s' % (NAME[spots[p]], p) for p in sorted(lost)[:6])))
        else:
            diff = sum(1 for p in spots if p in D2 and D2[p] > D.get(p, 0) + 15)
            print('    ✅ 有替代路线（封死后 %d 个地点要多绕 >15 格）' % diff)

    print()
    print('=' * 60)
    print('【C】补给间距全表（到最近的「能补给地点」= 城/镇/驿站，不含村庄）')
    print('=' * 60)
    sup = [p for p, t in spots.items() if t in SUPPLY]
    rows = []
    for p in sorted(spots):
        if p not in D:
            continue
        dd = bfs(p, blocked)
        near = min((dd[q] for q in sup if q != p and q in dd), default=None)
        rows.append((near if near is not None else 9999, p))
    rows.sort(reverse=True)
    over = 0
    for near, p in rows:
        tag = ''
        if near > 30:
            tag = '  ⚠️ 超 15 天续航'
            over += 1
        elif near > 20:
            tag = '  · 注意'
        print('    %-12s @ %-10s 最近补给 %3d 格 ≈ %2d 天%s'
              % (NAME[spots[p]], str(p), near, near // 2, tag))
    print('  → 超过 30 格（15 天）的共 %d 个' % over)

    print()
    print('=' * 60)
    print('【D】三城之间的实际路程（订单分档校验）')
    print('=' * 60)
    cities = [(p, NAME[spots[p]]) for p, t in spots.items() if t in ('big', 'small')]
    for i in range(len(cities)):
        for j in range(i + 1, len(cities)):
            a, an = cities[i]
            b, bn = cities[j]
            dd = bfs(a, blocked)
            d = dd.get(b)
            if d is None:
                print('  %s@%s  →  %s@%s  ：❌ 不通' % (an, a, bn, b))
            else:
                print('  %s@%s  →  %s@%s  ：%3d 格 ≈ %3d 天' % (an, a, bn, b, d, d // 2))
    print('=' * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法：python 地图分析_深度.py 地图坐标.txt')
        sys.exit(1)
    main(sys.argv[1])
