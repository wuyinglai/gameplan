# -*- coding: utf-8 -*-
"""A2~A10 迁移脚本：按节切行复制（原文一字不改）。多源/多段支持。"""
import io, os
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(HERE)
SRC = {
    "2A": os.path.join(BASE, "A类文件", "正文", "第2A类_地点系统_权威口径.md"),
    "3A": os.path.join(BASE, "A类文件", "正文", "第3A类_商队资源与失败系统_权威口径.md"),
    "4A": os.path.join(BASE, "A类文件", "正文", "第4A类_战斗系统_权威口径.md"),
    "5A": os.path.join(BASE, "A类文件", "正文", "第5A类_天气与事件系统_权威口径.md"),
    "6A": os.path.join(BASE, "A类文件", "正文", "第6A类_角色技能与成长系统_权威口径.md"),
}
L = {k: io.open(p, encoding="utf-8").read().split("\n") for k, p in SRC.items()}

# 每个 (源, 起, 止, 编号, 标题)；多段的编连续写在同一个 FILE 里
SYSTEMS = [
    ("A2_地点与经济", "2A", [
        (1, 22, "A2.0", "总定位"),
        (23, 110, "A2.1", "地点分类总览"),
        (111, 136, "A2.2", "大城九城"),
        (137, 153, "A2.3", "小城"),
        (154, 165, "A2.4", "城镇"),
        (166, 178, "A2.5", "驿站"),
        (179, 185, "A2.6", "村庄"),
        (186, 261, "A2.7", "经济系统"),
        (281, 289, "A2.8", "等待费用"),
        (290, 307, "A2.9", "收入结构"),
        (308, 339, "A2.10", "不做内容与待补数据"),
    ]),
    ("A3_商队资源与消耗", "3A", [
        (1, 28, "A3.0", "总定位"),
        (29, 162, "A3.1", "核心资源与消耗（含补给耗尽与恢复·脏水）"),
        ((163, 192), (318, 345), "A3.2", "耐久与修理（基础/分级 + 修理规则/修车逃生战）"),
        (346, 450, "A3.3", "车厢容量"),
    ]),
    ("A4_车辆与车损", "3A", [
        (193, 276, "A4.1", "车损·弃车·回收（四部位四档）"),
        (277, 317, "A4.2", "耐久损耗渠道（地形/战斗）"),
    ]),
    ("A5_士气", None, [
        ("3A", 451, 473, "A5.1", "基础数值与状态"),
        ("3A", 474, 504, "A5.2", "士气下降与扣减上限"),
        ("3A", 505, 520, "A5.3", "士气消费"),
        ("3A", 521, 557, "A5.4", "自然恢复与金币额外恢复"),
        ("3A", 558, 575, "A5.5", "正面士气事件"),
        ("2A", 262, 280, "A5.6", "地点侧：在哪里买、在哪里恢复"),
    ]),
    ("A6_撤退与失败", None, [
        ("3A", 699, 739, "A6.1", "失败条件与三种失败"),
        ("3A", 740, 800, "A6.2", "撤退去哪（三硬规则）"),
        ("3A", 801, 818, "A6.3", "撤退代价（三者不同）"),
        ("3A", 819, 836, "A6.4", "强制撤退（严重重伤+零件耗尽）"),
        ("3A", 837, 876, "A6.5", "待补数据与不做内容"),
        ("4A", 620, 751, "A6.6", "撤退系统总节（战斗撤退/敌方逃跑/地图撤退/总表）"),
    ]),
    ("A7_战斗", "4A", [
        (1, 54, "A7.0", "总定位与战斗定位红线"),
        (55, 261, "A7.2", "体力系统（含知识强化§2.5·机动§2.6）"),
        (262, 399, "A7.3", "伤害类型与防御系统（倍率表/防护构成）"),
        (400, 510, "A7.4", "状态系统"),
        (511, 555, "A7.5", "旧文明武器系统"),
        (556, 595, "A7.6", "角色技能概览"),
        (596, 619, "A7.7", "战斗难度"),
        (768, 794, "A7.8", "不做内容与关联边界"),
    ]),
    ("A8_重伤与恢复", None, [
        ("4A", 752, 767, "A8.1", "重伤系统（4A §10）"),
        ("6A", 325, 375, "A8.2", "重伤分级与恢复方式（6A §7）"),
    ]),
    ("A9_天气", "5A", [
        (78, 221, "A9.1", "天气系统（5.1）"),
    ]),
    ("A10_事件", "5A", [
        (24, 77, "A10.0", "总定位与时间结算系统"),
        (222, 568, "A10.1", "外部事件系统（9类35小类·含阶段轴）"),
        (569, 588, "A10.2", "覆盖影响预留"),
        (589, 772, "A10.3", "内部事件系统"),
        (773, 812, "A10.4", "事件冷却系统"),
        (813, 831, "A10.5", "最终覆盖口径"),
    ]),
]

def ranges_of(item):
    """规整成 [(src, start, end)] 列表。default_src 取自外层当前系统。"""
    first = item[0]
    if isinstance(first, str):  # 显式带源 ("3A", s1, e1, [s2, e2, ...], num, title)
        nums = item[1:-2]
        src = first
    else:                        # 默认源 (s1, e1, [s2, e2, ...], num, title)
        nums = item[:-2]
        src = default_src
    pairs = []
    for i in range(0, len(nums), 2):
        x, y = nums[i], nums[i + 1]
        if isinstance(x, tuple):      # ((s,e),(s,e)) 嵌套形式
            for (a, b) in ((x, y) if isinstance(y, tuple) else [(x, y)]):
                pairs.append((a, b))
                if isinstance(y, tuple):
                    break
        else:
            pairs.append((x, y))
    return [(src, s, e) for (s, e) in pairs], item[-2], item[-1]

for folder, default_src, items in SYSTEMS:
    outdir = os.path.join(HERE, folder)
    os.makedirs(outdir, exist_ok=True)
    # 按 (编号,标题) 聚合
    grouped = {}
    order = []
    for item in items:
        rs, num, title = ranges_of(item)
        key = (num, title)
        if key not in grouped:
            grouped[key] = []
            order.append(key)
        grouped[key].extend(rs)
    for (num, title) in order:
        rs = grouped[(num, title)]
        parts, notes = [], []
        for (src, s, e) in rs:
            parts.append("\n".join(L[src][s - 1:e]))
            notes.append("`%s` 第 %d–%d 行" % (src, s, e))
        header = ("# %s %s\n\n> **来源**：%s · 复制迁移 2026-10-28（🔴 迁移只搬不修，原文一字未动）\n"
                  "> **系统**：%s · **迁移期权威源仍为旧 A 类**\n\n") % (
              num, title, " + ".join(notes), folder.split("_")[0])
        if len(rs) > 1:
            body = ("\n\n---\n\n（多段来源，以下按原文件顺序拼接）\n\n---\n\n").join(parts)
        else:
            body = parts[0]
        with io.open(os.path.join(outdir, "%s_%s.md" % (num, title.replace("/", "·"))), "w",
                     encoding="utf-8", newline="\n") as f:
            f.write(header + body + "\n")
        total = sum(e - s + 1 for _, s, e in rs)
        print("OK", num, title, total, "行")
print("ALL DONE")
