# -*- coding: utf-8 -*-
import os

base = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base, "地图编辑器_200x200.html")
out_html = os.path.join(base, "地图编辑器_400x400_空白.html")

# 干净 400x400：只改网格尺寸与文案，不注入任何旧坐标（让用户从零重画）
html = open(html_path, encoding="utf-8").read()

assert "const W = 200, H = 200;" in html
html = html.replace("const W = 200, H = 200;", "const W = 400, H = 400;")
html = html.replace("余烬商队 · 200×200 地图编辑器", "余烬商队 · 400×400 地图编辑器（空白）")
html = html.replace("范围 0–199。", "范围 0–399。")
html = html.replace('<input type="range" id="zoom" min="3" max="14" value="6">',
                    '<input type="range" id="zoom" min="3" max="14" value="4">')
html = html.replace('<b id="zoomV">6</b>', '<b id="zoomV">4</b>')
html = html.replace("测试版地图坐标（200×200，用户手工指定）",
                    "测试版地图坐标（400×400，用户手工指定）")
html = html.replace("「地图编辑器_200x200.html」导出", "「地图编辑器_400x400_空白.html」导出")
# 独立存档 key，避免载入上一张 ×2 预载版的 localStorage
html = html.replace("'ember_caravan_map_200'", "'ember_caravan_map_400_blank'")

open(out_html, "w", encoding="utf-8").write(html)
print("已生成:", os.path.basename(out_html))
