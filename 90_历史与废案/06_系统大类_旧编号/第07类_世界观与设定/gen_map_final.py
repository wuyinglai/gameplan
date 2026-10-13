# Compact landmass design - all regions form a single connected blob
# Max 1 empty cell gap between regions internally
# Each region 3-6 cells, contiguous, left-to-right difficulty

g=[['. 'for _ in range(10)]for _ in range(10)]

# Think of it as one landmass with regions packed tightly
# N1 left, N9 right, difficulty increases left to right

# Carefully hand-designed to avoid gaps >1 cell internally
n1=[(1,0),(2,0),(3,0),(1,1),(2,1),(3,1)]  # 6格 - 左下
n2=[(0,2),(1,2),(2,2),(0,3)]              # 4格 - 左中上
n3=[(3,2),(4,2),(3,3),(4,3),(3,4)]        # 5格 - 中左
n4=[(0,4),(1,4),(2,4),(1,5)]              # 4格 - 中上
n5=[(4,4),(5,4),(5,5),(4,6)]              # 4格 - 中
n6=[(2,5),(3,5),(2,6),(3,6),(0,6)]        # 5格 - 中下
n7=[(5,6),(6,5),(6,6),(6,7),(7,6)]        # 5格 - 右上
n8=[(4,7),(5,7),(4,8),(5,8),(3,8)]        # 5格 - 右中
n9=[(6,8),(7,7),(7,8),(8,8),(8,9),(7,9)]  # 6格 - 最右

all_cells={'N1':n1,'N2':n2,'N3':n3,'N4':n4,'N5':n5,'N6':n6,'N7':n7,'N8':n8,'N9':n9}

# Check overlap
from collections import Counter
all_coords=[]
for lab,cs in all_cells.items():
    for y,x in cs:
        all_coords.append((y,x))
dupes=[(y,x) for (y,x),n in Counter(all_coords).items() if n>1]
print('重叠: '+'OK' if not dupes else 'BAD:'+str(dupes))

# Check continuity
all_ok=True
for lab in ['N1','N2','N3','N4','N5','N6','N7','N8','N9']:
    cs=all_cells[lab]
    s,q={cs[0]},{cs[0]}
    while q:
        y,x=q.pop()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            if(y+dy,x+dx)in cs and(y+dy,x+dx)not in s:
                s.add((y+dy,x+dx));q.add((y+dy,x+dx))
    ok='OK'if len(s)==len(cs)else'BAD'
    if ok=='BAD':all_ok=False
    cols=[x for _,x in cs]
    print(f'{lab} {ok} {len(cs)}格 列{min(cols)}-{max(cols)}')

# Place
for lab,cs in all_cells.items():
    for y,x in cs:
        g[y][x]=lab

print()
print('   0 1 2 3 4 5 6 7 8 9')
for y in range(10):
    print(f'{y}  '+' '.join(g[y]))

# Check gaps between regions
print()
empty_cells=[(y,x)for y in range(10)for x in range(10)if g[y][x]=='. ']
# Find internal empty cells that are surrounded by regions
internal=0
for y,x in empty_cells:
    nbors=0
    for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
        ny,nx=y+dy,x+dx
        if 0<=ny<10 and 0<=nx<10 and g[ny][nx]!='. ':
            nbors+=1
    if nbors>=2:
        internal+=1
        print(f'内部空格 at ({y},{x}) - 相邻{nbors}个区域')
print(f'总空格: {len(empty_cells)}/100, 内部空格: {internal}')

# Adjacency
conns=set()
for y in range(10):
    for x in range(10):
        if g[y][x]!='. ':
            for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                ny,nx=y+dy,x+dx
                if 0<=ny<10 and 0<=nx<10 and g[ny][nx]!='. 'and g[ny][nx]!=g[y][x]:
                    a,b=sorted([g[y][x].strip(),g[ny][nx].strip()])
                    conns.add(f'{a}-{b}')
for c in sorted(conns):print(f'  {c}')
