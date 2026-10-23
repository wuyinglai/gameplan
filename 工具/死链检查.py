# -*- coding: utf-8 -*-
"""
死链检查 v3 —— 只报「真的解不出来」的引用
===========================================
用法：python 工具/死链检查.py

v3 修掉了 v1/v2 的三个误报源：
  1) 路径必须从「词首」开始 —— 否则长路径被截成片段 → 误报（v1/v2 最大误报源）
  2) 命令前缀（npx vite-node ...）不是路径引用
  3) 分类统计：真断链 / 占位符 / 未来文件 / 根相对写法

「根相对写法」不是错 —— 它能解出来，只是相对路径写得不规范。
判定标准：解不出来 = 错；解出来了 = 只是写法可以更统一。

【踩坑提醒】本文件的 docstring 里不能出现反斜杠 + 字母的组合
            （Python 会当成转义序列，比如 x.md 里的 x 被当十六进制）
            —— 所以下面的说明一律不写具体路径。
"""
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = ("node_modules", ".git", "dist", ".vite", "__pycache__")
LIVE_DIRS = ["A类文件", "B类_开发文档", "AI交流", "项目管理", "工具", "游戏本体"]

PAT_QUOTE = re.compile(r"`([^`\n]{2,140})`")
# 🔴 路径必须从「词首」开始 —— 不能从中间截断
PAT_BARE = re.compile(
    r"(?<![\w一-鿿/\\`.-])((?:[\w一-鿿.\-]+[\\/])+[\w一-鿿.\-]+\.(?:md|ts|tsx|js|mjs|json|csv|txt|html|py|png|jpg|xlsx|bat))"
)

EXT_DIRS = (".md", ".ts", ".tsx", ".js", ".mjs", ".json", ".csv", ".txt",
            ".html", ".py", ".png", ".jpg", ".xlsx", ".bat")

CMD_PREFIX = ("python ", "node ", "npx ", "cd ", "git ", "npm ", "vite-node ",
              "npm run ")

PLACEHOLDER_PAT = ("xxx", "XXX", "PN", "NN", "N.", "NNN")

FUTURE_DIRS = ("src/p2/", "src/p3/", "src/p4/", "src/p5/", "src/p6/", "src/p7/",
               "src/bNN/", "bNN/")


def is_external(s):
    s = s.strip()
    if not s:
        return True
    return s.startswith(("http://", "https://", "www.", "mailto:", "~"))


def looks_like_path(s):
    s = s.strip().strip("`")
    if not s or is_external(s):
        return False
    if len(s) > 130:
        return False
    if "*" in s or "?" in s or "..." in s:
        return False
    for p in CMD_PREFIX:
        if s.startswith(p):
            return False
    # 🔴 代码示例里的相对 import（'./地图.json'）—— 那是代码，不是路径引用
    if s.startswith("./") or s.startswith(".\\"):
        return False
    if not s.lower().endswith(EXT_DIRS):
        return False
    if "/" not in s and "\\" not in s:
        return False
    return True


def is_placeholder(s):
    bn = os.path.basename(s.replace("\\", "/"))
    for pat in PLACEHOLDER_PAT:
        if pat in bn:
            return True
    return False


def is_future(s):
    norm = s.replace("\\", "/")
    for fd in FUTURE_DIRS:
        if fd in norm:
            return True
    return False


def collect_candidates(text):
    no_fence = re.sub(r"```.*?```", "", text, flags=re.S)
    no_indent = re.sub(r"(?m)^(?:    |\t).*$", "", no_fence)
    cands = set()
    for m in PAT_QUOTE.finditer(no_indent):
        piece = m.group(1).strip()
        if looks_like_path(piece):
            cands.add(piece)
    for m in PAT_BARE.finditer(no_indent):
        s = m.group(1)
        if looks_like_path(s):
            cands.add(s)
    return cands


def resolve(cand, from_file):
    """返回 (状态, 解析到的绝对路径或 None)
    状态：'OK'（相对当前文件就能解）/ 'ROOT'（只能按仓库根解）/ 'CMD'（命令里的路径，基准目录由人 cd 决定）/ 'BROKEN'
    """
    raw = cand.replace("/", os.sep).replace("\\", os.sep)
    p = os.path.normpath(os.path.join(os.path.dirname(from_file), raw))
    if os.path.isfile(p):
        return "OK", p
    c = raw.lstrip("." + os.sep)
    parts = c.split(os.sep)
    d = os.path.dirname(from_file)
    for _ in range(8):
        p = os.path.normpath(os.path.join(d, *parts))
        if os.path.isfile(p):
            return "ROOT", p
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    p = os.path.normpath(os.path.join(BASE, *parts))
    if os.path.isfile(p):
        return "ROOT", p
    # 🔴 命令里的路径：基准目录由「人 cd 到哪」决定 —— 不算仓库级断链
    for code_root in (os.path.join(BASE, "游戏本体"),):
        p = os.path.normpath(os.path.join(code_root, *parts))
        if os.path.isfile(p):
            return "CMD", p
    return "BROKEN", None


def all_md():
    out = []
    for d in LIVE_DIRS:
        root = os.path.join(BASE, d)
        if not os.path.isdir(root):
            continue
        for dp, dns, fns in os.walk(root):
            dns[:] = [x for x in dns if x not in SKIP_DIRS]
            for fn in fns:
                if fn.endswith(".md"):
                    out.append(os.path.join(dp, fn))
    for fn in ("README.md", "开发规划.md"):
        p = os.path.join(BASE, fn)
        if os.path.isfile(p):
            out.append(p)
    return out


def is_annotated(text, cand):
    """🔴 同一行里若写了「已不存在 / 已归档 / 已改名 / 尚未写入 / 待回执」等说明，
       那这条引用是**有意指向一个不在的文件**（历史来源 / 尚未产出）—— 语义正确，不算断链。
    """
    markers = ("已不存在", "已归档", "已改名", "尚未写入", "待回执", "已废止",
               "已作废", "不在此", "已移入", "旧目录", "已删", "没了")
    for line in text.splitlines():
        if cand in line:
            for mk in markers:
                if mk in line:
                    return True
    return False


BROKEN, PLACEHOLDERS, FUTURES, ROOTREL, CMDS, ANNOTATED = [], [], [], [], [], []
TOTAL = 0
files = all_md()

for f in files:
    rel = os.path.relpath(f, BASE).replace("\\", "/")
    try:
        with io.open(f, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        continue
    for cand in collect_candidates(text):
        TOTAL += 1
        st, resolved = resolve(cand, f)
        if st == "BROKEN":
            if is_annotated(text, cand):
                ANNOTATED.append((rel, cand))
            elif is_placeholder(cand):
                PLACEHOLDERS.append((rel, cand))
            elif is_future(cand):
                FUTURES.append((rel, cand))
            else:
                BROKEN.append((rel, cand))
        elif st == "ROOT":
            ROOTREL.append((rel, cand, os.path.relpath(resolved, BASE).replace("\\", "/")))
        elif st == "CMD":
            CMDS.append((rel, cand))

lines = []
lines.append("")
lines.append("=" * 78)
lines.append("  死链检查 v3")
lines.append("=" * 78)
lines.append("  扫描活文件区 .md %d 份 · 路径引用 %d 条" % (len(files), TOTAL))
lines.append("")
lines.append("  🔴 真断链（解不出来 = 错）：%d 条" % len(BROKEN))
if BROKEN:
    seen = set()
    for rel, cand in BROKEN:
        k = (rel, cand)
        if k in seen:
            continue
        seen.add(k)
        lines.append("    %-46s → %s" % (rel, cand))
else:
    lines.append("    （无）")
lines.append("")
lines.append("  ○ 占位符（模板，不是错）：%d 条" % len(PLACEHOLDERS))
lines.append("  ○ 未来文件（还没写，正常）：%d 条" % len(FUTURES))
lines.append("  ○ 已标注的历史来源（有意指向不存在的文件）：%d 条" % len(ANNOTATED))
lines.append("  ○ 命令里的路径（cd 到游戏本体后成立）：%d 条" % len(CMDS))
lines.append("  ⚠ 根相对写法（能解，只是不够统一）：%d 条" % len(ROOTREL))
lines.append("")
lines.append("-" * 78)
lines.append("  合计 %d 条 · 要修 %d · 占位 %d · 未来 %d · 已标注 %d · 命令 %d · 根相对 %d"
             % (TOTAL, len(BROKEN), len(PLACEHOLDERS), len(FUTURES),
                len(ANNOTATED), len(CMDS), len(ROOTREL)))
lines.append("=" * 78)
lines.append("")

report = "\n".join(lines)
with io.open(os.path.join(BASE, "工具", "_deadlink_out.txt"), "w",
             encoding="utf-8", newline="\n") as fh:
    fh.write(report)
print(report)
sys.exit(1 if BROKEN else 0)
