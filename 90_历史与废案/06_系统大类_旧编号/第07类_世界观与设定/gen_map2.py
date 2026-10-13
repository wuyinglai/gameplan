import random
random.seed(42)

W, H = 50, 50
grid = [['. ' for _ in range(W)] for _ in range(H)]

# Region centers - left=weak, right=strong
# Bigger target = more cells, organic shape
regions = [
    ('N1', 12, 42, 12),   # 灰原旷野 - start, bottom-left
    ('N2', 10, 10, 10),   # 枯林猎场 - top-left
    ('N3', 28, 25, 12),   # 河谷水源 - center
    ('N4', 22, 12, 10),   # 山地峡道 - center-top, barrier
    ('N5', 6,  30, 8),    # 风蚀沙砾 - far left
    ('N6', 30, 42, 10),   # 灰水湿地 - bottom
    ('N7', 42, 12, 10),   # 残田牧野 - top-right
    ('N8', 38, 32, 10),   # 黑石丘陵 - right-center
    ('N9', 46, 25, 8),    # 灰烬污染区 - far right
]

for label, cx, cy, target in regions:
    cells = []
    attempts = 0
    while len(cells) < target and attempts < 500:
        # Gaussian cluster for organic shape
        dx = int(random.gauss(0, 4))
        dy = int(random.gauss(0, 4))
        # Stretch some regions (mountains = tall, river = wide)
        x = cx + dx
        y = cy + dy
        # Ensure within bounds
        if 0 <= x < W and 0 <= y < H and grid[y][x] == '. ':
            grid[y][x] = label
            cells.append((x,y))
        attempts += 1

# Connect adjacent regions (if only 1-2 cells apart, fill the gap)
for _ in range(2):
    new_grid = [row[:] for row in grid]
    for y in range(H):
        for x in range(W):
            if grid[y][x] == '. ':
                # Count neighbors
                neighbors = {}
                for dy, dx in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(-1,1),(1,-1),(-1,-1)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= nx < W and 0 <= ny < H and grid[ny][nx] != '. ':
                        label = grid[ny][nx]
                        neighbors[label] = neighbors.get(label, 0) + 1
                if neighbors:
                    best = max(neighbors, key=neighbors.get)
                    if neighbors[best] >= 2:
                        new_grid[y][x] = best.lower().replace(' ','')
    grid = new_grid

# Ensure N1 is connected (starting area)
for y in range(H):
    for x in range(W):
        if grid[y][x] == 'n1':
            grid[y][x] = '. '

# Count
counts = {}
for row in grid:
    for c in row:
        c = c.strip()
        if c and c != '.' and c.isupper():
            counts[c] = counts.get(c, 0) + 1

# Output
lines = ['     ' + ''.join(f'{x//10} ' for x in range(W)),
         '     ' + ''.join(f'{x%10} ' for x in range(W))]
for y in range(H):
    line = f'{y:2d}  '
    for x in range(W):
        cell = grid[y][x].strip()
        if not cell or cell == '.':
            line += '. '
        elif cell.isupper():
            line += cell + ' '
        else:
            line += '· '
    lines.append(line)

with open('C:/Users/Administrator/Desktop/游戏大纲/01_系统大类/第07类_世界观与设定/地图_50x50_v2.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print("区域格数:")
for k in sorted(counts):
    print(f"  {k}: {counts[k]}格")
print(f"合计: {sum(counts.values())}格")
