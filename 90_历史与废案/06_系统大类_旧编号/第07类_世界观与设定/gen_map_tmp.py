g=[['. 'for _ in range(9)]for _ in range(9)]

n1=[(1,0),(2,0),(3,0),(1,1),(2,1),(3,1)]
n2=[(0,2),(1,2),(2,2),(3,2),(0,3)]
n3=[(4,1),(5,1),(4,2),(5,2),(4,3),(5,3)]
n4=[(0,4),(1,4),(2,4),(3,4),(4,4)]
n5=[(5,4),(6,4),(7,4),(6,5),(5,5)]
n6=[(0,5),(1,5),(2,5),(0,6),(1,6)]
n7=[(3,5),(3,6),(4,6),(5,6),(3,7)]
n8=[(6,6),(7,6),(6,7),(7,7),(5,7)]
n9=[(6,8),(7,8),(8,8),(8,7),(5,8)]

all_cells={'N1':n1,'N2':n2,'N3':n3,'N4':n4,'N5':n5,'N6':n6,'N7':n7,'N8':n8,'N9':n9}

from collections import Counter
all_coords=[]
for lab,cs in all_cells.items():
    for y,x in cs:
        all_coords.append((y,x))
dupes=[(y,x) for (y,x),n in Counter(all_coords).items() if n>1]
print('重叠:'+('OK'if not dupes else'BAD '+str(dupes)))

for lab in ['N1','N2','N3','N4','N5','N6','N7','N8','N9']:
    cs=all_cells[lab]
    s,q={cs[0]},{cs[0]}
    while q:
        y,x=q.pop()
        for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
            if(y+dy,x+dx)in cs and(y+dy,x+dx)not in s:
                s.add((y+dy,x+dx));q.add((y+dy,x+dx))
    ok='OK'if len(s)==len(cs)else'BAD'
    cols=[x for _,x in cs]
    print(f'{lab} {ok} {len(cs)}格 列{min(cols)}-{max(cols)}')

for lab,cs in all_cells.items():
    for y,x in cs:
        g[y][x]=lab

print()
print('  0 1 2 3 4 5 6 7 8')
for y in range(9):
    print(f'{y} '+' '.join(g[y]))

empty=sum(1 for y in range(9) for x in range(9) if g[y][x]=='. ')
print(f'空格: {empty}/81')

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
