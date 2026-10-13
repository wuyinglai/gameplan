import random
random.seed(42)

W, H = 50, 50
grid = [['  ' for _ in range(W)] for _ in range(H)]

# Region definitions: center (x,y), size, label
# Left=weak, Right=strong. Organic shapes.
regions = [
    ('N1', 12, 38, 10),   # 灰原旷野 - start, bottom-left
    ('N2', 10, 10, 9),    # 枯林猎场 - top-left
    ('N3', 28, 25, 10),   # 河谷水源 - center
    ('N4', 22, 12, 8),    # 山地峡道 - center-top
    ('N5', 6,  28, 7),    # 风蚀沙砾 - far left
    ('N6', 30, 40, 8),    # 灰水湿地 - bottom
    ('N7', 40, 12, 8),    # 残田牧野 - top-right
    ('N8', 38, 30, 8),    # 黑石丘陵 - right-center
    ('N9', 46, 22, 7),    # 灰烬污染区 - far right
]

for label, cx, cy, target in regions:
    cells = []
    attempts = 0
    while len(cells) < target and attempts < 300:
        r = 4
        dx = int(random.gauss(0, r))
        dy = int(random.gauss(0, r))
        # Make it more oval
        dx = int(dx * random.uniform(0.4, 1.3))
        dy = int(dy * random.uniform(0.4, 1.6))
        x = cx + dx
        y = cy + dy
        if 0 <= x < W and 0 <= y < H and grid[y][x] == '  ':
            grid[y][x] = label
            cells.append((x,y))
        attempts += 1

# Expand each region slightly for connectivity
for _ in range(3):
    new_grid = [row[:] for row in grid]
    for y in range(H):
        for x in range(W):
            if grid[y][x] != '  ':
                label = grid[y][x]
                for dy, dx in [(0,1),(0,-1),(1,0),(-1,0)]:
                    ny, nx = y+dy, x+dx
                    if 0 <= nx < W and 0 <= ny < H and new_grid[ny][nx] == '  ':
                        # Connect to nearest region neighbor
                        new_grid[ny][nx] = label.lower()
    grid = new_grid

# Write to file
lines = []
lines.append('     ' + ''.join(f'{x//10} ' for x in range(W)))
lines.append('     ' + ''.join(f'{x%10} ' for x in range(W)))
for y in range(H):
    line = f'{y:2d}  '
    for x in range(W):
        cell = grid[y][x]
        if cell == '  ':
            line += '. '
        elif cell.isupper():
            line += cell + ' '
        else:
            line += '· '
    lines.append(line)

result = '\n'.join(lines)

main_cells = sum(1 for row in grid for c in row if c != '  ' and c.isupper())
border_cells = sum(1 for row in grid for c in row if c != '  ' and c.islower())

print(f"主区域格数: {main_cells}")
print(f"连接带格数: {border_cells}")
print(f"每个区域格数:")
counts = {}
for row in grid:
    for c in row:
        if c != '  ' and c.isupper():
            counts[c] = counts.get(c, 0) + 1
for k in sorted(counts):
    print(f"  {k}: {counts[k]}格")

with open('C:/Users/Administrator/Desktop/游戏大纲/01_系统大类/第07类_世界观与设定/地图_50x50.txt', 'w', encoding='utf-8') as f:
    f.write(result)

print("\n地图已生成。大写=主区域，小写=连接带，.=荒野/道路")
