# -*- coding: utf-8 -*-
"""6A 指向 4A 旧节号的引用批量更新（4A 重排后：§4.1构成→§3.3 · §4.2倍率表→§3.2 · §4.5护甲→§4.3 · §4.4护盾→§4.1）"""
import io, os, re
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "A类文件", "正文", "第6A类_角色技能与成长系统_权威口径.md")
t = io.open(P, encoding="utf-8").read()
subs = [
    ("第4A类 §4.1", "第4A类 §3.3"),
    ("第4A类 §4.2", "第4A类 §3.2"),
    ("第4A类 §4.5", "第4A类 §4.3"),
    ("第 4A 类 §4.2", "第 4A 类 §3.2"),
    ("第 4A 类 §4.4", "第 4A 类 §4.1"),
    ("4A 类 §4.2", "4A 类 §3.2"),
]
for old, new in subs:
    n = t.count(old)
    if n:
        t = t.replace(old, new)
        print("%d 处：%s → %s" % (n, old, new))
io.open(P, "w", encoding="utf-8", newline="\n").write(t)
# 复查
for i, l in enumerate(t.split("\n"), 1):
    if "4A" in l and re.search(r"§4\.[1-5]", l):
        print("剩余含§4.x的行", i, l.strip()[:100])
