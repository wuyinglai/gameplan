# Aggressive organic growth on 15x15
import random
random.seed(777)

W,H = 15,15
g = [['. ' for _ in range(W)] for _ in range(H)]

# Seeds spread across the map with irregular pattern
regions = [
    ('N1', 8, 1, 5),   # bottom-left-ish
    ('N2', 2, 2, 4),   # top-left
    ('N3', 5, 4, 6),   # center-left
    ('N4', 1, 7, 4),   # top
    ('N5', 6, 7, 5),   # center
    ('N6', 10, 6, 4),  # bottom
    ('N7', 2, 11, 5),  # top-right
    ('N8', 6, 12, 6),  # center-right
    ('N9', 9, 13, 5),  # bottom-right
]

# Place seeds
placed = {}
for label, sy, sx, target in regions:
    g[sy][sx] = label
    placed[label] = {(sy,sx)}

# Aggressive growth: 50 rounds
for _ in range(50):
    for label, sy, sx, target in regions:
        cells = placed[label]
        if len(cells) >= target:
            continue
        
        # Get all adjacent empty cells
        border = set()
        for cy, cx in cells:
            for dy, dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                ny, nx = cy+dy, cx+dx
                if 0 <= ny < H and 0 <= nx < W and g[ny][nx] == '. ':
                    # Check not claimed by other region
                    claimed = False
                    for other_label, other_cells in placed.items():
                        if other_label != label and (ny,nx) in other_cells:
                            claimed = True
                            break
                    if not claimed:
                        border.add((ny,nx))
        
        if not border:
            continue
        
        # Take ALL border cells up to target
        need = target - len(cells)
        border_list = sorted(border, key=lambda c: (abs(c[1]-sx) + abs(c[0]-sy)))
        # Take a mix: some close to center, some random for organic shape
        take_first = min(int(need * 0.6), len(border_list))
        taken = set(border_list[:take_first])
        remaining = [c for c in border_list if c not in taken]
        random.shuffle(remaining)
        need_second = need - len(taken)
        for i in range(min(need_second, len(remaining))):
            taken.add(remaining[i])
        
        for ny, nx in taken:
            if len(placed[label]) < target:
                # Check still free
                all_placed = set()
                for other_cs in placed.values():
                    all_placed.update(other_cs)
                if (ny,nx) not in all_placed:
                    g[ny][nx] = label
                    placed[label].add((ny,nx))

# Verify
from collections import Counter
all_cs = []
for cs in placed.values():
    all_cs.extend(cs)
dupes = [c for c,n in Counter(all_cs).items() if n>1]
print('重叠:'+('BAD '+str(dupes) if dupes else 'OK'))

all_ok = True
for label in ['N1','N2','N3','N4','N5','N6','N7','N8','N9']:
    cs = placed[label]
    sz = len(cs)
    if sz < 3 or sz > 6:
        print(f'{label}大小: {sz} ❌')
        all_ok = False
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

# Print map
if all_ok:
    print()
    print('地图 (15x15):')
    header = '   '
    for x in range(W): header += str(x%10) + ' '
    print(header)
    for y in range(H):
        row = f'{y:2d} '
        for x in range(W):
            row += g[y][x]
        print(row)
    
    empty = sum(1 for y in range(H) for x in range(W) if g[y][x]=='. ')
    print(f'\n空格: {empty}/{W*H}')
    
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
