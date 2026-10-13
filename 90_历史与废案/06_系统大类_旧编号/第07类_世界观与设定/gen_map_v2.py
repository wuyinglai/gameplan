# Complete redesign: pack all 9 regions into a tight landmass
# 9x9 grid (fits better), each region 3-6 cells, contiguous, no internal gaps >1

g=[['. 'for _ in range(9)]for _ in range(9)]

# Design principle: one connected landmass, sub-divided into regions
# Verify EVERY cell touches its neighbors

n1=[(2,0),(3,0),(2,1),(3,1),(4,1),(4,2)]  # 6格 - 左下
n2=[(0,1),(1,1),(1,2),(2,2)]              # 4格 - 左中上
n3=[(3,2),(4,3),(5,3),(5,4),(6,4)]        # 5格 - 中左 - check adjacency
# (3,2)-(4,3) diagonal! NOT contiguous. Let me fix.
# Need all cells adjacent via up/down/left/right

# REDO - check each adjacency:
def verify_contiguous(coords):
    if not coords: return False
    s,q={coords[0]},{coords[0]}
    while q:
        y,x=q.pop()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            if(y+dy,x+dx)in coords and(y+dy,x+dx)not in s:
                s.add((y+dy,x+dx));q.add((y+dy,x+dx))
    return len(s)==len(coords)

def mark(lab, coords):
    for y,x in coords:
        g[y][x]=lab

# N1: 4格, bottom-left - compact square
n1=[(2,0),(3,0),(2,1),(3,1)]
n1_extra=[(4,1),(4,2)]  # if we want 6
# Let's just do: n1 4格 is fine
n1=[(2,0),(3,0),(2,1),(3,1)]

# N2: 4格, above N1
n2=[(0,1),(1,1),(2,2),(3,2)]
# Check: (0,1)-(1,1) horizontal ✓, (1,1)-(2,2) diagonal ❌
# Fix:
n2=[(0,1),(1,1),(2,1),(3,1)]  # horizontal row at y=1
# Now check: (0,1)-(1,1)-(2,1)-(3,1) all connected horizontally ✓
# But n2 and n1 overlap at (2,1),(3,1)! Both claim those cells.

# Problem: n1 has (2,0),(3,0),(2,1),(3,1) and n2 has (0,1),(1,1),(2,1),(3,1)
# (2,1) and (3,1) overlap!

# I keep making this mistake. Let me be MUCH more careful.
# I'll build one cell at a time with a fresh grid and check overlaps immediately.

print("Let me design this more carefully...")
