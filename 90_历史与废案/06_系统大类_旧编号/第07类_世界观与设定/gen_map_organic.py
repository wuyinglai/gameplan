# 15x15 organic map - irregular shapes, not square
# Grow each region from seeds using flood-fill with controlled randomness

import random
random.seed(777)

W,H = 15,15
g = [['. ' for _ in range(W)] for _ in range(H)]

# Region definitions: label, seed_y, seed_x, target_cells
regions_def = [
    ('N1', 8, 1, 5),   # left side
    ('N2', 3, 2, 4),   # upper-left
    ('N3', 7, 4, 6),   # center-left
    ('N4', 3, 6, 4),   # top-center
    ('N5', 7, 7, 5),   # center
    ('N6', 11, 8, 4),  # bottom-center
    ('N7', 2, 10, 5),  # top-right
    ('N8', 7, 11, 6),  # center-right
    ('N9', 9, 13, 5),  # far right
]

# Also define preferred growth direction for each region
# (dx, dy) weight - to avoid regions growing into each other too much
preferred_dir = {
    'N1': [(-1,-2), (0,-1), (1,0), (2,1)],  # grow down-right
    'N2': [(-1,-1), (0,1), (1,1), (2,0)],   # grow down
    'N3': [(-1,0), (0,-1), (1,-1), (2,0)],  # grow down-left 
    'N4': [(-1,-1), (0,-1), (1,0), (1,1)],   # grow down-right
    'N5': [(-1,0), (0,-1), (0,1), (1,0)],    # grow all directions
    'N6': [(1,0), (0,-1), (-1,0), (0,1)],    # grow up
    'N7': [(-1,0), (0,-1), (1,-1), (2,0)],   # grow down-left
    'N8': [(-1,0), (0,1), (1,0), (0,-1)],    # grow wide
    'N9': [(-1,-1), (0,-1), (1,-1), (2,-1)], # grow left
}

# Place seeds first
placed = set()
region_cells = {}
for label, sy, sx, target in regions_def:
    g[sy][sx] = label
    placed.add((sy,sx))
    region_cells[label] = {(sy,sx)}

# Grow regions alternately
for _ in range(20):  # multiple rounds
    for label, sy, sx, target in regions_def:
        cells = region_cells[label]
        if len(cells) >= target:
            continue
        
        # Find border cells (empty cells adjacent to this region)
        border = set()
        for cy, cx in cells:
            for dy, dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == '. ' and (ny,nx) not in placed:
                    border.add((ny,nx))
        
        if not border:
            continue
        
        # Score border cells - prefer the growth direction
        scored = []
        for by, bx in border:
            score = random.uniform(0, 1)
            # Bonus for cells closer to the seed's "zone"
            # Left regions should go left, right regions right
            zone_center = sx
            if abs(bx - zone_center) < 3:
                score += 0.3
            scored.append((score, by, bx))
        
        scored.sort(reverse=True)
        # Take top 1-2 cells
        take = min(random.randint(1, 2), target - len(cells))
        for i in range(take):
            if i < len(scored):
                _, by, bx = scored[i]
                if len(cells) < target:
                    g[by][bx] = label
                    placed.add((by,bx))
                    cells.add((by,bx))

# After all growth, verify and report
from collections import Counter
all_cells_list = []
for label, cs in region_cells.items():
    for c in cs:
        all_cells_list.append(c)
dupes = [c for c,n in Counter(all_cells_list).items() if n>1]
print('重叠:'+('BAD '+str(dupes) if dupes else 'OK'))

all_ok = True
for label in ['N1','N2','N3','N4','N5','N6','N7','N8','N9']:
    cs = region_cells[label]
    sz = len(cs)
    if sz < 3 or sz > 6:
        print(f'{label}大小: {sz}(需3-6) ❌')
        all_ok = False
    # BFS continuity
    s,q = {next(iter(cs))}, {next(iter(cs))}
    while q:
        y,x = q.pop()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            if (y+dy,x+dx) in cs and (y+dy,x+dx) not in s:
                s.add((y+dy,x+dx))
                q.add((y+dy,x+dx))
    ok = 'OK' if len(s)==sz else '❌'
    if ok != 'OK': all_ok = False
    cols = [x for _,x in cs]
    print(f'{label} {ok} {sz}格 列{min(cols)}-{max(cols)}')

if all_ok:
    print()
    print('地图:')
    print('   0 1 2 3 4 5 6 7 8 9 0 1 2 3 4')
    print('   ' + '-'*30)
    for y in range(H):
        row = [str(y).rjust(2)]
        row.append('|')
        for x in range(W):
            row.append(g[y][x])
        print(' '.join(row))
    
    empty = sum(1 for y in range(H) for x in range(W) if g[y][x]=='. ')
    print(f'空格: {empty}/{W*H}')
    
    # Internal gaps
    ints = 0
    for y in range(H):
        for x in range(W):
            if g[y][x]=='. ':
                nb = sum(1 for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)] 
                        if 0<=y+dy<H and 0<=x+dx<W and g[y+dy][x+dx]!='. ')
                if nb >= 2:
                    ints += 1
    print(f'内部空格(2+相邻): {ints}')
    
    # Adjacency
    conns = set()
    for y in range(H):
        for x in range(W):
            if g[y][x] != '. ':
                for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                    ny,nx = y+dy, x+dx
                    if 0<=ny<H and 0<=nx<W and g[ny][nx]!='. ' and g[ny][nx]!=g[y][x]:
                        a,b = sorted([g[y][x].strip(), g[ny][nx].strip()])
                        conns.add(f'{a}-{b}')
    for c in sorted(conns):
        print(f'  {c}')
