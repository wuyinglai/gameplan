# Systematic approach: define a single landmass blob, then partition left-to-right
g=[['. 'for _ in range(9)]for _ in range(9)]

# Define the landmass: one connected irregular blob
blob = set()
for y in range(9):
    if y == 0:    cols = range(2, 8)  # 2-7 = 6 cells
    elif y == 1:  cols = range(1, 8)  # 1-7 = 7
    elif y == 2:  cols = range(0, 8)  # 0-7 = 8
    elif y == 3:  cols = range(0, 9)  # 0-8 = 9
    elif y == 4:  cols = range(0, 9)  # 0-8 = 9
    elif y == 5:  cols = range(0, 9)  # 0-8 = 9
    elif y == 6:  cols = range(1, 9)  # 1-8 = 8
    elif y == 7:  cols = range(2, 8)  # 2-7 = 6
    elif y == 8:  cols = range(3, 7)  # 3-6 = 4
    for x in cols:
        blob.add((y,x))

print(f'Blob size: {len(blob)} cells')

# Verify blob is contiguous
y0,x0 = next(iter(blob))
s,q={(y0,x0)},{(y0,x0)}
while q:
    y,x=q.pop()
    for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
        if(y+dy,x+dx)in blob and(y+dy,x+dx)not in s:
            s.add((y+dy,x+dx));q.add((y+dy,x+dx))
assert len(s)==len(blob), "Blob is disconnected!"
print('Blob is contiguous OK')

# Sort blob cells by x then y
sorted_cells = sorted(blob, key=lambda c: (c[1], c[0]))

# Greedily assign to 9 regions, each 3-6 cells
# Target: roughly equal, but allow 3-6 range
# 66 cells / 9 = 7.3... too many for 6 max!
# Need fewer cells. Let me trim the blob.

# Actually with 66 cells and max 6 per region = 54 max. So I need -12 cells.
# Let me remove some edge cells.

# Remove cells from edges to get ~54 cells
# Remove bottom-right corner cells
to_remove = [(8,3),(8,6),(7,2),(7,7),(0,2),(0,7),(6,8),(5,8),(4,8),(3,8),(6,0),(5,0)]
for c in to_remove:
    if c in blob:
        blob.remove(c)

print(f'Trimmed blob size: {len(blob)}')

# Verify still contiguous  
if len(blob) > 0:
    y0,x0 = next(iter(blob))
    s,q={(y0,x0)},{(y0,x0)}
    while q:
        y,x=q.pop()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            if(y+dy,x+dx)in blob and(y+dy,x+dx)not in s:
                s.add((y+dy,x+dx));q.add((y+dy,x+dx))
    if len(s)!=len(blob):
        print('WARNING: blob became disconnected after trim!')
        # Find the main component
        print(f'Main component: {len(s)}/{len(blob)}')
        blob = s  # Use only main component
    else:
        print('Blob contiguous after trim OK')

print(f'Final blob: {len(blob)} cells')
print(f'Target: 27-54 cells for 9 regions of 3-6 each')

# Sort by x then y
sorted_cells = sorted(blob, key=lambda c: (c[1], c[0]))

# Now partition into 9 regions
# Strategy: sweep left to right, assign contiguous groups
regions = {}
target_avg = len(blob) // 9
remaining = list(sorted_cells)
region_labels = ['N1','N2','N3','N4','N5','N6','N7','N8','N9']

for i, label in enumerate(region_labels):
    is_last = (i == 8)
    if is_last:
        # Last region gets all remaining
        cells = list(remaining)
    else:
        # Take 3-6 cells, preferring target_avg
        take = min(max(3, target_avg), 6)
        # But also leave enough for remaining regions
        remaining_regions = 9 - i - 1
        min_needed = remaining_regions * 3
        max_available = len(remaining) - min_needed
        take = min(take, max_available)
        take = max(3, take)
        cells = remaining[:take]
    
    # Verify these cells form a contiguous group
    if len(cells) > 0:
        s,q={cells[0]},{cells[0]}
        while q:
            y,x=q.pop()
            for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                if(y+dy,x+dx)in cells and(y+dy,x+dx)not in s:
                    s.add((y+dy,x+dx));q.add((y+dy,x+dx))
        if len(s) != len(cells):
            print(f'{label}: NOT contiguous! {len(s)}/{len(cells)}')
            # Find contiguous groups within the cells
            # Just assign whatever we can
            pass
    
    regions[label] = cells
    remaining = remaining[take:]
    if not is_last and len(remaining) < (9-i-1)*3:
        print(f'{label}: WARNING - not enough remaining cells!')

# Place on grid
for label, cells in regions.items():
    for y,x in cells:
        g[y][x] = label

print()
print('   0 1 2 3 4 5 6 7 8')
for y in range(9):
    print(f'{y}  '+' '.join(g[y]))

print()
for label in region_labels:
    cells = regions[label]
    if cells:
        cols = [x for _,x in cells]
        print(f'{label}: {len(cells)}格 列{min(cols)}-{max(cols)}')
    else:
        print(f'{label}: 0格 !!!')

# Adjacency
conns=set()
for y in range(9):
    for x in range(9):
        if g[y][x]!='. ':
            for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<9 and 0<=nx<9 and g[ny][nx]!='. 'and g[ny][nx]!=g[y][x]:
                    a,b=sorted([g[y][x].strip(),g[ny][nx].strip()])
                    conns.add(f'{a}-{b}')
for c in sorted(conns):print(f'  {c}')

empty=sum(1 for y in range(9) for x in range(9) if g[y][x]=='. ')
print(f'\n空格: {empty}/81')
