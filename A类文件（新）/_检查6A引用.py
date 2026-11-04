# -*- coding: utf-8 -*-
"""修复 6A 中指向 4A 旧节号的引用（含被 bash 反引号弄脏的两处）"""
import io, os, re
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "A类文件", "正文", "第6A类_角色技能与成长系统_权威口径.md")
t = io.open(P, encoding="utf-8").read()
lines = t.split("\n")
for i, l in enumerate(lines, 1):
    if "4A" in l and ("§4." in l or "§3." in l):
        print(i, l.strip()[:110])
