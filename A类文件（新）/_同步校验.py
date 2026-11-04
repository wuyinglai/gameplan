# -*- coding: utf-8 -*-
"""新旧 A 类同步校验 v2：按编号数值排序 · 忽略文件边界空行 · 只报非空行差异"""
import io, os, re, difflib
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = os.path.join(os.path.dirname(HERE), "A类文件", "正文")
SYSTEMS = ["第1A类_地图与商路系统_权威口径", "第2A类_地点系统_权威口径",
           "第3A类_商队资源与失败系统_权威口径", "第4A类_战斗系统_权威口径",
           "第5A类_天气与事件系统_权威口径", "第6A类_角色技能与成长系统_权威口径",
           "第7A类_世界观与设定_权威口径", "第8A类_灰烬生态系统_权威口径",
           "第10A类_订单与贸易_权威口径"]
bad = 0
for s in SYSTEMS:
    old = io.open(os.path.join(OLD, s + ".md"), encoding="utf-8").read().rstrip("\n")
    d = os.path.join(HERE, s)
    subs = sorted((f for f in os.listdir(d) if f.endswith(".md")),
                  key=lambda f: int(re.match(r"第.*?\.(\d+)_", f).group(1)))
    bodies = []
    for fn in subs:
        lines = io.open(os.path.join(d, fn), encoding="utf-8").read().split("\n")[5:]  # 去 5 行头
        while lines and lines[-1] == "":
            lines.pop()          # 去文件尾空行（边界空行，属拆分产物）
        bodies.append("\n".join(lines))
    recon = "\n\n".join(bodies)  # 组间恰好一个空行
    if recon == old:
        print("✅ 一致", s, "(%d 字符)" % len(old))
    else:
        diff = [l for l in difflib.unified_diff(old.split("\n"), recon.split("\n"), lineterm="")
                if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))
                and l[1:].strip() != ""]
        print("❌ 非空行差异 %d 处：" % len(diff), s)
        for l in diff[:6]:
            print("   ", l[:90])
        bad += 1
print("结论：", "9 系统全部逐字同步（仅边界空行差异，属拆分产物）" if bad == 0 else "%d 个系统有实质差异" % bad)
