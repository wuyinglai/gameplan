# -*- coding: utf-8 -*-
"""
旧口径残留扫描（自验项用）
=================================
查这些旧写法有没有漏改：
  阶段编号 P1..P7 · 最终整合 INT · 2.A~2.D · 第01B类 · 阶段P1_
  HERMES_P1/P2 · 验收/P1 · 项目主\\ · 旧代码与新代码节 · 中阶段序列

白名单（这些地方出现旧写法是对的）：
  ① A类 5A §3 的事件编号（P1=土匪过路费 …）
  ② 修订记录里的历史描述（记录"以前叫 P1"）
  ③ 开发总览里「为什么不用 P1/P2」的说明文字
  ④ 其他/AI交流/CHATGPT_* —— ChatGPT 规划原件（历史存档，不改）
"""
import io
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LIVE = ["A类文件", "B类_开发文档", "其他", "游戏本体"]

CHECKS = [
    ("阶段编号 P1..P7", r"(?<![0-9A-Za-z.])P[1-7](?![0-9A-Za-z])"),
    ("最终整合 INT", r"(?<![0-9A-Za-z])INT(?![0-9A-Za-z])"),
    ("2.A~2.D 编号", r"(?<![0-9A-Za-z.])2\.[A-D](?![0-9A-Za-z])"),
    ("第01B类/第02B类", r"第0[12]B类"),
    ("阶段P1_", r"阶段P1_"),
    ("HERMES_P1/P2", r"HERMES_P[12]"),
    ("回复_HERMES_P1/P2", r"回复_HERMES_P[12]"),
    ("验收/P1 目录", r"验收[/\\]P1"),
    ("项目主\\ 目录", r"项目主[/\\]"),
    ("旧代码与新代码节", r"旧代码与新代码的处理原则"),
    ("中阶段序列", r"中阶段序列"),
    ("一条指令只做一步", r"一条指令只做一步"),
]

# 🔴 白名单：文件相对路径 → 允许出现旧写法的正则
WHITELIST = [
    (r"^A类文件/正文/第5A类_天气与事件系统_权威口径\.md$",
     r"^\|\s*P[1-7]\s*\|"),           # 事件编号表
    (r"^B类_开发文档/开发规划/修订记录\.md$", None),  # 整份都是历史描述
    (r"^其他/AI交流/CHATGPT_.*\.md$", None),          # ChatGPT 规划原件
]


def whitelisted(rel, line):
    for pat, linepat in WHITELIST:
        if re.match(pat, rel):
            if linepat is None:
                return True
            if re.match(linepat, line.strip()):
                return True
    # 开发总览里的「为什么不用 P1 / P2」说明
    if rel.endswith("开发规划/开发总览.md"):
        if ("不用 P1" in line or "为什么不用 P1" in line
                or "P1 / P2" in line or "P1 / P2）" in line):
            return True
    return False


hits = []
for d in LIVE:
    root = os.path.join(BASE, d)
    for dp, dns, fns in os.walk(root):
        dns[:] = [x for x in dns if x not in
                  ("node_modules", ".git", "dist", ".vite", "__pycache__")]
        for fn in sorted(fns):
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, BASE).replace("\\", "/")
            with io.open(p, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if whitelisted(rel, line):
                        continue
                    for name, pat in CHECKS:
                        if re.search(pat, line):
                            hits.append("%s | %s:%d | %s" % (
                                name, rel, i, line.strip()[:70]))

report = "\n".join(hits) if hits else "（干净）"
with io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "_residual_out.txt"), "w",
              encoding="utf-8", newline="\n") as fh:
    fh.write(report)
print("残留 %d 处" % len(hits))
