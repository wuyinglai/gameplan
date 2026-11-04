# -*- coding: utf-8 -*-
# 4A 攻防重排（项目主 2026-10-28 裁定）：攻击类型移出防御章，内容零改动纯搬位置+节号更新
# 新结构：§3 伤害与攻击类型（3.1 内伤外伤 / 3.2 攻击类型与倍率表 / 3.3 防护构成 / 3.4 结算顺序）
#         §4 防御手段（4.1 三层总览 / 4.2 护盾 / 4.3 护甲）
import io, os
P = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                 "A类文件", "正文", "第4A类_战斗系统_权威口径.md")
lines = io.open(P, encoding="utf-8").read().split("\n")

def pos(prefix, start=0):
    return next(i for i in range(start, len(lines)) if lines[i].startswith(prefix))

p3   = pos("## 3. ")
p4   = pos("## 4. ")
p41  = pos("### 4.1 ")
p42  = pos("### 4.2 ")
p43  = pos("### 4.3 ")
p44  = pos("### 4.4 ")
p45  = pos("### 4.5 ")
p5   = pos("## 5. ")

head  = lines[:p3]
b3    = lines[p3:p4]        # §3 内伤外伤
b4in  = lines[p4:p41]       # §4 章头（三层防御表）
b41   = lines[p41:p42]      # 4.1 防护构成
b42   = lines[p42:p43]      # 4.2 攻击类型与倍率表
b43   = lines[p43:p44]      # 4.3 结算顺序
b44   = lines[p44:p45]      # 4.4 护盾
b45   = lines[p45:p5]       # 4.5 护甲
tail  = lines[p5:]

def ret(block, subs):
    out = list(block)
    for old, new in subs:
        for i, l in enumerate(out):
            if old in l:
                out[i] = l.replace(old, new)
                break
    return out

# —— 新 §3 伤害与攻击类型 ——
n3 = ret(b3, [("## 3. 伤害类型：内伤与外伤", "## 3. 伤害类型与攻击类型")])
n32 = ret(b42, [
    ("### 4.2 攻击类型与倍率表", "### 3.2 攻击类型与倍率表"),
    ("混合防护构成按 **§4.1 加权公式**", "混合防护构成按 **§3.3 加权公式**"),
])
n33 = ret(b41, [
    ("### 4.1 防护构成", "### 3.3 防护构成"),
    ("（§4.2 表的值即各类型的基础倍率）", "（§3.2 表的值即各类型的基础倍率）"),
])
n34 = ret(b43, [("### 4.3 伤害结算顺序", "### 3.4 伤害结算顺序")])

# —— 新 §4 防御手段 ——
n4in = ret(b4in, [("## 4. 防御系统", "## 4. 防御手段（护盾 / 护甲 / 屏障）")])
n42 = ret(b44, [("### 4.4 护盾（只由盾牌提供）", "### 4.2 护盾（只由盾牌提供）")])
n43 = ret(b45, [("### 4.5 护甲（只由防具提供）", "### 4.3 护甲（只由防具提供）")])

new = head + n3 + n32 + n33 + n34 + n4in + n42 + n43 + tail
with io.open(P, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(new))
print("重排完成：新行数", len(new), "（原", len(lines), "）")
