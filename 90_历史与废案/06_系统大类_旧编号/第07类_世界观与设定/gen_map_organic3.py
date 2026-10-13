# Define an irregular continent first, then assign cells to regions
W,H = 15,15
g = [['. ' for _ in range(W)] for _ in range(H)]

# Define continent as an irregular cloud/amoeba shape (~42 cells)
# Each row has different start and end columns (irregular outline)
continent = set()
shape = {
    2: (2,6),     # row 2: cols 2-5 (4 cells)
    3: (1,8),     # row 3: cols 1-7 (7 cells)
    4: (0,9),     # row 4: cols 0-8 (9 cells)
    5: (0,9),     # row 5: cols 0-8 (9 cells)  
    6: (1,8),     # row 6: cols 1-7 (7 cells) - shifted right
    7: (2,9),     # row 7: cols 2-8 (7 cells)
    8: (3,9),     # row 8: cols 3-8 (6 cells)
}
# row 2: 4, row 3: 3+4=7... this is 4+7+9+9+7+7+6=49. Too many.

# Let me design more carefully for ~42 cells:
# I'll make a diagonal-ish blob
shape2 = {
    1: (2,4),     # row 1: cols 2-3 (2 cells)
    2: (1,5),     # row 2: cols 1-4 (4 cells)
    3: (0,6),     # row 3: cols 0-5 (6 cells)
    4: (1,7),     # row 4: cols 1-6 (6 cells)
    5: (2,8),     # row 5: cols 2-7 (6 cells)  
    6: (3,8),     # row 6: cols 3-7 (5 cells)
    7: (4,7),     # row 7: cols 4-6 (3 cells)
}
# 2+4+6+6+6+5+3 = 32 cells. Not enough.

shape3 = {
    1: (3,7),     # row 1: 4 cells
    2: (2,8),     # row 2: 6 cells
    3: (1,9),     # row 3: 8 cells
    4: (1,9),     # row 4: 8 cells
    5: (2,10),    # row 5: 8 cells
    6: (3,11),    # row 6: 8 cells
    7: (4,11),    # row 7: 7 cells
    8: (5,12),    # row 8: 7 cells
    9: (6,12),    # row 9: 6 cells
    10: (7,11),   # row 10: 4 cells
    11: (8,10),   # row 11: 2 cells
}
# 4+6+8+8+8+8+7+7+6+4+2 = 68. Way too many.

# OK let me think about this differently.
# With 42 cells over 9 regions at 3-6 each...
# A compact irregular shape: think of it as a cloud with arms

# Simple approach: define cells directly
# Make a diagonal-ish cloud sloping up-right

cells = {}

# N1: bottom-left blob, 5格 (irregular shape)
n1 = {(7,0),(8,0),(9,0),(8,1),(9,1)}  # L-shape

# N2: above N1, 4格 (vertical strip)
n2 = {(3,1),(4,1),(4,2),(5,2)}

# N3: right of N1, 6格 (sprawling)
n3 = {(5,3),(6,3),(7,3),(6,4),(7,4),(8,4)}

# N4: top-left, 3格 (T-shape)
n4 = {(3,4),(3,5),(4,5)}

# N5: center, 6格 (diamond-ish)
n5 = {(5,5),(6,5),(5,6),(6,6),(5,7),(6,7)}

# N6: below N5, 4格 (vertical)
n6 = {(8,6),(9,5),(9,6),(10,5)}

# N7: top-right, 3格
n7 = {(1,8),(1,9),(2,8)}

# N8: right-center, 6格 (fat blob)
n8 = {(4,8),(5,8),(4,9),(5,9),(4,10),(5,10)}

# N9: far right, 5格 (vertical strip)
n9 = {(5,11),(6,11),(5,12),(6,12),(7,12)}

all_n = {'N1':n1,'N2':n2,'N3':n3,'N4':n4,'N5':n5,'N6':n6,'N7':n7,'N8':n8,'N9':n9}

# Verify
from collections import Counter
flat = []
for cs in all_n.values():
    flat.extend(cs)
dupes = [c for c,n in Counter(flat).items() if n>1]
print('重叠:'+('BAD '+str(dupes) if dupes else 'OK'))

all_ok = True
for lab, cs in all_n.items():
    sz = len(cs)
    if sz < 3 or sz > 6:
        print(f'{lab}大小: {sz} ❌')
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
    print(f'{lab} {ok} {sz}格 列{min(cols)}-{max(cols)}')

if all_ok:
    for lab, cs in all_n.items():
        for y,x in cs:
            g[y][x] = lab
    
    print()
    header = '   '
    for x in range(W): header += str(x%10) + ' '
    print(header)
    for y in range(H):
        print(f'{y:2d} ' + ' '.join(g[y]))
    
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
                    print(f'  内部空格: ({y},{x})')
    print(f'内部空格: {ints}')
    
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
