#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 ChatGPT 生成的地图草稿（v0.7 多文件 CSV）转成地图编辑器能导入的单文件 JSON。

🔴 坐标转换：草稿用「左上角 (0,0)、y 向下」，编辑器/游戏用「左下角 (0,0)、y 向上」
   → y_editor = 399 - y_csv
"""
import csv, json, os, sys

SRC = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\Administrator\Downloads\EmberCaravan_MapDraft_v0_7_special_structures_detour_test_only'
DST = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\Administrator\Desktop\map_editor\chatgpt_v07.json'

MAXC = 399
L = []
seen = {}          # (x,y) -> type，用于检测重复

def add(t, x, y, r=None, note=''):
    if not (0 <= x <= MAXC and 0 <= y <= MAXC):
        return
    k = (x, y)
    if k in seen:
        # 重复坐标：地点类优先，其余丢弃
        PRI = {'big': 1, 'small': 1, 'town': 1, 'inn1': 1, 'camp': 1, 'village': 1,
               'special': 2, 'road': 3, 'blk_fr': 3, 'block': 4, 'blk_wt': 4}
        if PRI.get(seen[k], 9) <= PRI.get(t, 9):
            return
        L[:] = [c for c in L if not (c['x'] == x and c['y'] == y)]
    seen[k] = t
    c = {'t': t, 'x': x, 'y': y}
    if r is not None:
        c['r'] = r
    L.append(c)


def flip(y):
    """csv 的 y（向下）→ 编辑器的 y（向上）"""
    return MAXC - y


def read_csv(path):
    with open(os.path.join(SRC, path), encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def read_cells(path):
    """读 (x,y) 格子表，返回 [(x, y), ...]"""
    rows = read_csv(path)
    out = []
    cols = rows[0].keys() if rows else []
    cx = 'x' if 'x' in cols else None
    cy = 'y' if 'y' in cols else None
    for r in rows:
        if cx and cy:
            out.append((int(r[cx]), int(r[cy])))
    return out


# ---------- 1. 地点 ----------
TYPE_MAP = {
    'big_city': 'big', 'small_city': 'small', 'town': 'town',
    'village': 'village', 'station': 'inn1', 'special_structure': 'special',
}
for fn in ('cities', 'towns', 'villages', 'stations', 'special_structures'):
    for r in read_csv('01_locations/%s.csv' % fn):
        t = TYPE_MAP.get(r['type'])
        if not t:
            continue
        add(t, int(r['x']), flip(int(r['y'])))

# ---------- 2. 地形 ----------
# 河流 = 不可通行的水
for (x, y) in read_cells('02_terrain/river_cells.csv'):
    add('blk_wt', x, flip(y))

# 桥梁 = 可通行
for (x, y) in read_cells('02_terrain/bridge_cells.csv'):
    add('blk_fr', x, flip(y))

# 山地 + 裂谷 = 不可通行
for (x, y) in read_cells('02_terrain/mountain_cells.csv'):
    add('block', x, flip(y))
for (x, y) in read_cells('02_terrain/ravine_cells.csv'):
    add('block', x, flip(y))

# 碎石地 = 可通行但路况差（r=2）
for (x, y) in read_cells('02_terrain/rough_ground_cells.csv'):
    add('blk_fr', x, flip(y), r=2)

# ---------- 3. 道路 ----------
# 维护主商路 = 好路况（r=0）
for (x, y) in read_cells('03_roads_and_routes/maintained_road_cells.csv'):
    add('road', x, flip(y), r=0)

# 险路 = 差路况（r=2）
for (x, y) in read_cells('03_roads_and_routes/rough_road_cells.csv'):
    add('road', x, flip(y), r=2)

# ---------- 输出 ----------
order = ['big', 'small', 'town', 'village', 'inn1', 'special',
         'road', 'blk_fr', 'block', 'blk_wt']
L.sort(key=lambda c: (order.index(c['t']) if c['t'] in order else 99, c['x'], c['y']))

# 起终点：从 routes_summary 的第一条路线取
routes = read_csv('03_roads_and_routes/routes_summary.csv')
cities = {r['id']: (int(r['x']), flip(int(r['y']))) for r in read_csv('01_locations/cities.csv')}
start = cities.get(routes[0]['start_id'], (10, 199))
end = cities.get(routes[0]['end_id'], (390, 389))

obj = {
    'map': {'width': 400, 'height': 400},
    'start': [start[0], start[1]],
    'end': [end[0], end[1]],
    'note': ('ChatGPT 生成 v0.7 测试地图（转自 CSV）。'
             '🔴 坐标已翻转成「左下角(0,0)、y向上」。'
             't: big=大城 small=小城 town=城镇 village=村庄 inn1=驿站 '
             'special=特殊建筑 road=商路 blk_fr=可通行(桥/碎石) '
             'block=不可通行(山/裂谷) blk_wt=不可通行(水)。'
             'r: 主商路=0(好) · 碎石地/险路=2(差)，其余不给=普通。'),
    'locations': L,
}
with open(DST, 'w', encoding='utf-8') as f:
    json.dump(obj, f, ensure_ascii=False, indent=1)

from collections import Counter
c = Counter(q['t'] for q in L)
print('=== 转换完成 ===')
for k in order:
    if c[k]:
        print('  %-9s %d' % (k, c[k]))
print('  r=0(好) %d 格 · r=2(差) %d 格' % (
    sum(1 for q in L if q.get('r') == 0), sum(1 for q in L if q.get('r') == 2)))
print('  总计 %d 格' % len(L))
print('  start=%s end=%s' % (start, end))
print('输出: %s' % DST)