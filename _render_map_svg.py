#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把生成的测试地图渲染成一张 SVG 预览图（每格 2×2 像素）"""
import json, os
from collections import defaultdict

W = H = 400
S = 2                                   # 每格像素
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '地图坐标_400_测试地图.json')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '地图预览_单元01.svg')

COLOR = {
    'big': '#c0392b', 'small': '#e67e22', 'town': '#f1c40f',
    'village': '#5dade2', 'inn1': '#27ae60', 'special': '#8e44ad',
    'road': '#c8a165', 'blk_fr': '#4f7a3a',
    'block': '#5d6d7e', 'blk_wt': '#3d6fa8',
}
DRAW = ['road', 'inn1', 'special', 'village', 'town', 'small', 'big']   # 覆盖层顺序（先铺的在下）

with open(SRC, encoding='utf-8') as f:
    d = json.load(f)

cells = defaultdict(list)
for o in d['locations']:
    cells[o['t']].append((o['x'], o['y']))

parts = []
parts.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">'
             % (W * S, H * S, W * S, H * S))
parts.append('<rect width="100%%" height="100%%" fill="#1a1a1a"/>')

for t in ['block', 'blk_wt', 'blk_fr'] + DRAW:
    for (x, y) in cells.get(t, []):
        parts.append('<rect x="%d" y="%d" width="%d" height="%d" fill="%s"/>'
                     % (x * S, y * S, S, S, COLOR[t]))

# 标注三座城（注意 SVG 的 y 轴向下，地图 y 向上，所以要翻转）
NAMES = {}
for o in d['locations']:
    if o['t'] in ('big', 'small'):
        NAMES[(o['x'], o['y'])] = o['t']
labels = ['A 灰原城(大城)', 'B 小城甲', 'C 小城乙']
pts = sorted(NAMES.keys(), key=lambda p: (p[0], p[1]))
for i, (x, y) in enumerate(pts):
    px = x * S
    py = (H - 1 - y) * S
    name = labels[i] if i < len(labels) else ('大城' if NAMES[(x, y)] == 'big' else '小城')
    parts.append('<circle cx="%d" cy="%d" r="7" fill="none" stroke="#ffffff" stroke-width="2"/>' % (px, py))
    parts.append('<text x="%d" y="%d" fill="#ffffff" font-size="15" font-weight="bold" '
                 'text-anchor="middle" paint-order="stroke" stroke="#000000" stroke-width="3">%s</text>'
                 % (px, py - 12, name))

parts.append('</svg>')

with open(OUT, 'w', encoding='utf-8') as f:
    f.write('\n'.join(parts))

print('输出: %s' % OUT)
print('城市坐标: %s' % pts)