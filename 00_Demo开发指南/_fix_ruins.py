# -*- coding: utf-8 -*-
import os

base = os.path.dirname(os.path.abspath(__file__))
files = [
    "地图编辑器_200x200.html",       # 源模板
    "地图编辑器_400x400_空白.html",   # 当前返工工具
    "地图编辑器_400x400.html",        # ×2 预载版（备份）
]

old = (
    "  {k:'ruinW',  n:'遗迹（产武器）',     c:'#8e44ad', lim:2,  key:'7'},\n"
    "  {k:'ruinM',  n:'遗迹（产记忆手册）', c:'#16a085', lim:2,  key:'8'},"
)
new = (
    "  {k:'ruinL',  n:'大遗迹',     c:'#8e44ad', lim:5,  key:'7'},\n"
    "  {k:'ruinS',  n:'小遗迹',     c:'#48c9b0', lim:10, key:'8'}"
)

for fn in files:
    p = os.path.join(base, fn)
    if not os.path.exists(p):
        print("跳过(不存在):", fn); continue
    s = open(p, encoding="utf-8").read()
    if old in s:
        s = s.replace(old, new, 1)
        # 顺手把提示里的"废墟"措辞无关，不动；仅确保新类型生效
        open(p, "w", encoding="utf-8").write(s)
        print("已更新:", fn)
    else:
        print("未找到旧遗迹类型(可能已是新):", fn)
