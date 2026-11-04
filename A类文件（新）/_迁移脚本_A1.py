# -*- coding: utf-8 -*-
"""A1 迁移脚本：按节切行复制 1A → A类文件（新）/A1_地图与商路/（原文一字不改）"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SRC = os.path.join(BASE, "A类文件", "正文", "第1A类_地图与商路系统_权威口径.md")
OUT = os.path.join(HERE, "A1_地图与商路")
os.makedirs(OUT, exist_ok=True)
lines = io.open(SRC, encoding="utf-8").read().split("\n")
FILES = [
    (1, 22, "A1.0", "总定位", "📌 定位（先看这段）"),
    (32, 99, "A1.2", "时间系统与行进能量", "§2 时间系统与行进能量 · §2.1 野外体力池"),
    (100, 185, "A1.3", "时间与作息", "§2.2 时间与作息"),
    (186, 224, "A1.4", "地图规格与聚居圈", "§3 地图规格 · §3.1 地点分布规律"),
    (225, 264, "A1.5", "地图节点格子类型", "§4 地图节点（格子）类型"),
    (265, 299, "A1.6", "移动消耗与补给惩罚", "§5 移动消耗 · §5.1 每格消耗只会变高 · §5.2 补给耗尽惩罚"),
    (300, 320, "A1.7", "安全点", "§6 安全点（地图休整与撤退）"),
    (321, 408, "A1.8", "路线分类与中继点", "§7 路线分类（7.1~7.6）"),
    (409, 573, "A1.9", "侦察与迷雾", "§9 地图侦察机制（信息等级系统）"),
    (574, 628, "A1.10", "经济参考", "§10 经济参考"),
    (629, 665, "A1.11", "不做内容", "§11 不做内容（含文末指针）"),
]
for start, end, num, title, sec in FILES:
    body = "\n".join(lines[start - 1:end])
    header = ("# %s %s\n\n> **来源**：`A类文件\\正文\\第1A类_地图与商路系统_权威口径.md` %s"
              "（第 %d–%d 行）· 复制迁移 2026-10-28（🔴 迁移只搬不修，原文一字未动）\n"
              "> **系统**：A1 地图与商路 · **迁移期权威源仍为旧 A 类**\n\n") % (num, title, sec, start, end)
    with io.open(os.path.join(OUT, "%s_%s.md" % (num, title)), "w",
                 encoding="utf-8", newline="\n") as f:
        f.write(header + body + "\n")
    print("OK", num, title, end - start + 1, "行")
