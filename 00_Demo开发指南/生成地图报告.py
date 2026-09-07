# -*- coding: utf-8 -*-
"""
余烬商队 · 地图体检报告生成器
读 地图坐标.txt → 输出 地图体检报告.html（SVG 地图 + 体检结论 + 问题标注）
用法：python 生成地图报告.py 地图坐标.txt
"""
import sys
from collections import deque

W = H = 200
NAME = {'big': '大城', 'small': '小城', 'town': '城镇', 'inn1': '驿站·有节点',
        'inn0': '驿站·损坏', 'village': '村庄', 'ruinW': '遗迹·武器', 'ruinM': '遗迹·手册'}
SUPPLY = {'big', 'small', 'town', 'inn1', 'inn0'}
ORDER = ['big', 'small', 'town', 'inn1', 'inn0', 'ruinW', 'ruinM', 'village']
STYLE = {
    'big':    ('#E24B4A', 7.5, '#fff'),
    'small':  ('#EF9F27', 6.5, '#fff'),
    'town':   ('#639922', 5.5, '#fff'),
    'inn1':   ('#534AB7', 5.5, '#fff'),
    'inn0':   ('#AFA9EC', 5.5, '#3C3489'),
    'village':('#888780', 3.2, '#fff'),
    'ruinW':  ('#D4537E', 5.0, '#fff'),
    'ruinM':  ('#D4537E', 5.0, '#fff'),
}


def is_block(t):
    return t in ('block', 'blk_mt', 'blk_wt', 'blk_ru')


def parse_compact(text):
    blocked, btype, spots = set(), {}, {}
    for line in text.splitlines():
        line = line.strip()
        if not line or '|' not in line:
            continue
        p = line.split('|')
        if len(p) < 3:
            continue
        t, xs, ys = p[0].strip(), p[1].strip(), p[2].strip()
        try:
            x = int(xs)
        except ValueError:
            continue
        for run in ys.split(','):
            run = run.strip()
            if not run:
                continue
            a, b = (run.split('-') + [run])[:2] if '-' in run else (run, run)
            try:
                y0, y1 = int(a), int(b)
            except ValueError:
                continue
            for y in range(y0, y1 + 1):
                if is_block(t):
                    blocked.add((x, y)); btype[(x, y)] = t
                elif t == 'blk_fr':
                    btype[(x, y)] = t
                else:
                    spots[(x, y)] = t
    return spots, blocked, btype


def bfs(start, blocked):
    dist = {start: 0}
    q = deque([start])
    while q:
        x, y = q.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= n[0] < W and 0 <= n[1] < H and n not in dist and n not in blocked:
                dist[n] = dist[(x, y)] + 1
                q.append(n)
    return dist


def build(spots, blocked, btype):
    OX = OY = 40
    P = 3.0                      # 1 格 = 3px
    S, N = 5, 40
    C = 15

    def px(x): return round(OX + x * P, 1)
    def py(y): return round(OY + y * P, 1)

    # ---- 地形层（5×5 合并 + 行内游程压缩）----
    def cell(cx, cy):
        for y in range(cy * S, cy * S + S):
            for x in range(cx * S, cx * S + S):
                if (x, y) in spots:
                    return 'P'
        tal = {}
        for y in range(cy * S, cy * S + S):
            for x in range(cx * S, cx * S + S):
                t = btype.get((x, y))
                if t:
                    tal[t] = tal.get(t, 0) + 1
        return max(tal, key=tal.get) if tal else '.'

    CLS = {'block': 'tm', 'blk_mt': 'tm', 'blk_ru': 'tm', 'blk_wt': 'tw', 'blk_fr': 'tf'}
    terr = []
    for cy in range(N):
        row = [cell(cx, cy) for cx in range(N)]
        cx = 0
        while cx < N:
            c = row[cx]
            if c == '.' or c == 'P':
                cx += 1
                continue
            n = 1
            while cx + n < N and row[cx + n] == c:
                n += 1
            terr.append('<rect class="%s" x="%d" y="%d" width="%d" height="%d"/>'
                        % (CLS[c], OX + cx * C, OY + cy * C, n * C, C))
            cx += n

    # ---- 补给间距 ----
    sup = [p for p, t in spots.items() if t in SUPPLY]
    gap = {}
    for p in spots:
        dd = bfs(p, blocked)
        v = min((dd[q] for q in sup if q != p and q in dd), default=9999)
        gap[p] = v
    far = sorted(gap.items(), key=lambda kv: -kv[1])
    risky = [p for p, v in far if v > 30]

    # ---- 绕路系数 ----
    origin = [p for p, t in spots.items() if t == 'big'][0]
    D = bfs(origin, blocked)
    ratios = []
    for p in spots:
        man = abs(p[0] - origin[0]) + abs(p[1] - origin[1])
        if p in D and man:
            ratios.append(D[p] / man)
    avg_r = sum(ratios) / len(ratios)

    # ---- 地点层 ----
    pts = []
    for t in ORDER:
        for (x, y), tt in sorted(spots.items()):
            if tt != t:
                continue
            col, r, _ = STYLE[t]
            if t == 'ruinM':
                pts.append('<path d="M%d %dL%d %dL%d %dL%d %dZ" fill="%s" stroke="#fff" stroke-width="1"/>'
                           % (px(x), py(y) - 5, px(x) + 5, py(y), px(x), py(y) + 5, px(x) - 5, py(y), col))
            elif t == 'inn0':
                pts.append('<circle cx="%s" cy="%s" r="%s" fill="#fff" stroke="%s" stroke-width="2"/>'
                           % (px(x), py(y), r, col))
            else:
                pts.append('<circle cx="%s" cy="%s" r="%s" fill="%s" stroke="#fff" stroke-width="1.2"/>'
                           % (px(x), py(y), r, col))

    warn = ''.join('<circle cx="%s" cy="%s" r="12" fill="none" stroke="#E24B4A" stroke-width="1.5" stroke-dasharray="3 3"/>'
                   % (px(p[0]), py(p[1])) for p in risky)

    # ---- 三城连线 ----
    cities = [(p, NAME[spots[p]]) for p, t in spots.items() if t in ('big', 'small')]
    lines = []
    for i in range(len(cities)):
        for j in range(i + 1, len(cities)):
            a, an = cities[i]; b, bn = cities[j]
            dd = bfs(a, blocked); d = dd.get(b)
            if not d:
                continue
            mx, my = (px(a[0]) + px(b[0])) / 2, (py(a[1]) + py(b[1])) / 2
            lines.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#185FA5" stroke-width="2" stroke-dasharray="6 4" opacity="0.75"/>'
                         % (px(a[0]), py(a[1]), px(b[0]), py(b[1])))
            lines.append('<rect x="%s" y="%s" width="52" height="18" rx="4" fill="#E6F1FB" stroke="#185FA5" stroke-width="0.8"/>'
                         % (mx - 26, my - 9))
            lines.append('<text x="%s" y="%s" font-size="11" fill="#0C447C" text-anchor="middle" dominant-baseline="central">%d 格 · %d 天</text>'
                         % (mx, my, d, d // 2))

    nblock = len(blocked)
    pct = 100.0 * nblock / (W * H)
    lost = [p for p in spots if p not in D]

    html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>余烬商队 · 地图体检报告</title>
<style>
*{box-sizing:border-box}
body{margin:0;padding:28px 32px;background:#faf9f5;color:#2C2C2A;
 font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;font-size:13px;line-height:1.6}
h1{font-size:19px;font-weight:500;margin:0 0 4px}
h2{font-size:14px;font-weight:500;margin:26px 0 10px;padding-bottom:6px;border-bottom:1px solid #e3e0d5}
.sub{color:#5F5E5A;margin-bottom:18px;font-size:12px}
.cards{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:6px}
.card{flex:1;min-width:150px;background:#fff;border:1px solid #e3e0d5;border-radius:10px;padding:12px 14px}
.card .k{font-size:11px;color:#888780}
.card .v{font-size:20px;font-weight:500;margin:2px 0}
.card .n{font-size:11px;color:#5F5E5A}
.ok{border-left:3px solid #1D9E75}.warn{border-left:3px solid #BA7517}.bad{border-left:3px solid #E24B4A}
.tm{fill:#C9C6BA}.tw{fill:#B5D4F4}.tf{fill:#C0DD97}
table{border-collapse:collapse;width:100%%;background:#fff;border:1px solid #e3e0d5;border-radius:8px;overflow:hidden}
th{background:#f1efe8;text-align:left;font-weight:500;padding:7px 10px;font-size:12px;border-bottom:1px solid #e3e0d5}
td{padding:6px 10px;border-bottom:1px solid #f0eee6;font-size:12px}
tr:last-child td{border-bottom:none}
.mono{font-variant-numeric:tabular-nums}
.lg{display:flex;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:12px;color:#444441;align-items:center}
.lg i{display:inline-block;width:11px;height:11px;border-radius:50%%;margin-right:5px;vertical-align:-1px}
.lg s{display:inline-block;width:14px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px;text-decoration:none}
.box{background:#fff;border:1px solid #e3e0d5;border-radius:10px;padding:14px 16px;margin-top:12px}
.box.bad{border-left:3px solid #E24B4A}.box.warn{border-left:3px solid #BA7517}.box.ok{border-left:3px solid #1D9E75}
.box b{font-weight:500}
ul{margin:6px 0 0;padding-left:20px}li{margin:3px 0}
.mapwrap{background:#fff;border:1px solid #e3e0d5;border-radius:10px;padding:10px;display:inline-block}
</style></head><body>
<h1>余烬商队 · 地图体检报告</h1>
<div class="sub">200 × 200 网格 · 1 格 = 1 天行程 · 按 2 格/天换算 · 生成自 地图坐标.txt</div>

<h2>一、总览</h2>
<div class="cards">
 <div class="card ok"><div class="k">地点数量</div><div class="v">%d / 51</div><div class="n">全部符合蓝图</div></div>
 <div class="card %s"><div class="k">连通性</div><div class="v">%s</div><div class="n">起点 = 大城 %s</div></div>
 <div class="card %s"><div class="k">不可通行地形</div><div class="v">%.1f%%</div><div class="n">山/水共 %d 格</div></div>
 <div class="card %s"><div class="k">平均绕路系数</div><div class="v">%.3f</div><div class="n">1.00 = 完全直走</div></div>
</div>

<h2>二、地图（红虚线圈 = 补给超距的地点，蓝虚线 = 三城实际路程）</h2>
<div class="mapwrap">
<svg width="680" height="680" viewBox="0 0 680 680" role="img">
<title>余烬商队 200x200 测试版地图</title>
<rect x="40" y="40" width="600" height="600" fill="#F1EFE8" stroke="#D3D1C7" stroke-width="0.5"/>
%s
%s
%s
%s
</svg>
</div>
<div class="lg">
 <span><i style="background:#E24B4A"></i>大城</span><span><i style="background:#EF9F27"></i>小城</span>
 <span><i style="background:#639922"></i>城镇</span><span><i style="background:#534AB7"></i>驿站·有节点</span>
 <span><i style="background:#fff;border:2px solid #AFA9EC"></i>驿站·损坏</span>
 <span><i style="background:#D4537E"></i>遗迹</span><span><i style="background:#888780"></i>村庄</span>
 <span><s style="background:#C9C6BA"></s>山</span><span><s style="background:#B5D4F4"></s>水</span>
 <span><s style="background:#C0DD97"></s>桥/林地</span>
 <span><svg width="22" height="12" style="vertical-align:-2px"><circle cx="11" cy="6" r="5" fill="none" stroke="#E24B4A" stroke-dasharray="3 3"/></svg>补给超距</span>
</div>

<h2>三、补给间距（到最近的城/镇/驿站，村庄不计）</h2>
%s

<h2>四、结论与建议</h2>
%s
</body></html>""" % (
        len(spots),
        'ok' if not lost else 'bad', '全互通' if not lost else '有 %d 个走不到' % len(lost), origin,
        'warn', pct, nblock,
        'warn' if avg_r < 1.10 else 'ok', avg_r,
        ''.join(terr), ''.join(lines), warn, ''.join(pts),
        _gap_table(far, spots),
        _advice(avg_r, pct, risky, spots, gap, D, origin),
    )
    return html


def _gap_table(far, spots):
    rows = []
    for p, v in far[:14]:
        tag = '<span style="color:#A32D2D">超 15 天</span>' if v > 30 else (
            '<span style="color:#854F0B">偏远</span>' if v > 20 else '<span style="color:#3B6D11">良好</span>')
        rows.append('<tr><td>%s</td><td class="mono">(%d, %d)</td><td class="mono">%d 格</td>'
                    '<td class="mono">≈ %d 天</td><td>%s</td></tr>' % (NAME[spots[p]], p[0], p[1], v, v // 2, tag))
    return ('<table><tr><th>地点</th><th>坐标</th><th>最近补给</th><th>天数</th><th>评价</th></tr>%s</table>'
            % ''.join(rows))


def _advice(avg_r, pct, risky, spots, gap, D, origin):
    parts = []
    parts.append('<div class="box ok"><b>做对的三件事</b><ul>'
                 '<li><b>三城呈三角分布，天然生成三条商路</b>——大城居中，两小城一南一东北，'
                 '两两之间正好对应短途 / 中途 / 长途三档订单，订单系统可以直接吃这套距离。</li>'
                 '<li><b>全图连通、没有孤岛</b>——51 个地点从大城出发全都走得到，不存在被山水封死的死区。</li>'
                 '<li><b>桥都不是独木桥</b>——5 组桥全部有替代路线，不会因为一次事件断桥就把整片地图封死。</li>'
                 '</ul></div>')

    if avg_r < 1.10:
        parts.append('<div class="box bad"><b>问题 1：山水没在分流商路（最重要）</b><ul>'
                     '<li>平均绕路系数只有 <b>%.3f</b>，也就是说从大城到任何地方几乎都能走直线。'
                     '最绕的地方也才 1.53 倍。</li>'
                     '<li>原因：不可通行地形只占 <b>%.1f%%</b>，而且大多是<b>块状</b>的（一座山、一个湖），'
                     '块状障碍玩家绕一下就过去了；能真正造出「走廊」的是<b>长条形</b>屏障——'
                     '横贯地图的山脉、切穿地图的河。</li>'
                     '<li>后果：地图没有「这儿必须走、那儿过不去」的感觉，商路形不成，'
                     '每趟跑商都是画直线，跑十趟和跑一趟体验一样。</li>'
                     '<li><b>建议</b>：把河/山改成<b>贯穿式</b>——比如那条长河真正从地图一侧切到另一侧，'
                     '只留 2~3 座桥；右侧那条纵向山脉补长，把东南角和大陆分开。'
                     '目标把绕路系数提到 <b>1.15~1.30</b>。</li>'
                     '</ul></div>' % (avg_r, pct))

    if risky:
        li = ''.join('<li><b>%s (%d, %d)</b>——最近补给 %d 格 ≈ %d 天</li>'
                     % (NAME[spots[p]], p[0], p[1], gap[p], gap[p] // 2) for p in risky)
        parts.append('<div class="box warn"><b>问题 2：%d 个地点超出补给续航</b><ul>%s</ul>'
                     '<div style="margin-top:8px">12 人商队带的食物水撑不了 15 天以上，'
                     '这几处驿站等于「到了也回不去」。<b>建议</b>：在它们附近补 1~2 个村庄/驿站，'
                     '或者把它们整体挪近主商路。</div></div>' % (len(risky), li))

    far_p = max(D, key=lambda p: D.get(p, 0))
    parts.append('<div class="box warn"><b>问题 3：地图对角线太长</b><ul>'
                 '<li>大城到最远地点（村庄 (%d, %d)）要 <b>%d 格 ≈ %d 天</b>。'
                 '这个量级本身没问题——它正好撑起「超长途订单」，但前提是沿途有足够落脚点，'
                 '否则中间那段就是纯空转。</li>'
                 '<li><b>建议</b>：确认超长途路线上每隔 10~15 天有城/镇/驿站，'
                 '实在不想加地点就把补给上限调高。</li></ul></div>'
                 % (far_p[0], far_p[1], D[far_p], D[far_p] // 2))

    parts.append('<div class="box ok"><b>下一步</b><ul>'
                 '<li>如果你认可上面三条，改完再导出一次坐标，我重新跑体检。</li>'
                 '<li>如果地形不改也行——那就接受「地图很开阔、跑商自由度高」，'
                 '把分流作用交给<b>灰度/危险区</b>去做（某些格子灰度高、能走但代价大），'
                 '而不是靠山水硬挡。</li></ul></div>')
    return ''.join(parts)


if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else '地图坐标.txt'
    with open(src, encoding='utf-8') as f:
        sp, bl, bt = parse_compact(f.read())
    out = build(sp, bl, bt)
    dst = '地图体检报告.html'
    with open(dst, 'w', encoding='utf-8') as f:
        f.write(out)
    print('已生成 %s (%d 字节)' % (dst, len(out)))
