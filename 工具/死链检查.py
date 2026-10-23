# -*- coding: utf-8 -*-
"""
死链检查 v2 —— 只报「真断链」
====================================
用法：python 工具/死链检查.py

v1 的问题：把「从当前文件目录算的相对路径」和「代码块里的片段」都当死链，
          误报 201 条。v2 改成：
  · 逐个前缀试 —— `路径` / `..\路径` / `..\..\路径` / `..\..\..\路径` ……
    只要**任何一个前缀能解出来**，就不算死链（因为人就是这么读的）
  · 排除「代码块里举例的路径」和「带 ... 的省略写法」
  · 只查活文件区（历史快照里的路径是历史原样）

真的断链 = 任何前缀都解不出来，且引用方是活文件。
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

PAT_QUOTE = re.compile(r"`([^`\n]{2,120})`")
PAT_BARE = re.compile(
    r"(?<![\w`])((?:[\w\u4e00-\u9fff.\-]+[\\/])+[\w\u4e00-\u9fff.\-]+\.(?:md|ts|tsx|js|mjs|json|csv|txt|html|py|png|jpg|xlsx|bat))"
)

EXT_DIRS = (".md", ".ts", ".tsx", ".js", ".mjs", ".json", ".csv", ".txt",
            ".html", ".py", ".png", ".jpg", ".xlsx", ".bat")


def is_external(s):
    s = s.strip()
    if not s:
        return True
    if s.startswith(("http://", "https://", "www.", "mailto:", "~")):
        return True
    return False


def looks_like_path(s):
    s = s.strip().strip("`")
    if not s or is_external(s):
        return False
    if len(s) > 110:
        return False
    if "*" in s or "?" in s:
        return False
    if "..." in s:            # 省略写法（`基础文档\...\地图.json`）
        return False
    if not s.lower().endswith(EXT_DIRS):
        return False
    if "/" not in s and "\\" not in s:
        return False
    return True


def collect_candidates(text):
    """收集路径候选；同时跳过围栏代码块（``` 之间的内容是举例，不是引用）"""
    # 去掉围栏代码块
    no_fence = re.sub(r"```.*?```", "", text, flags=re.S)
    # 缩进代码块（4 空格起）
    no_indent = re.sub(r"(?m)^(?:    |\t).*$", "", no_fence)

    cands = set()
    for src in (no_fence,):
        for m in PAT_QUOTE.finditer(src):
            for piece in re.split(r"[·、，；,;（）()]", m.group(1)):
                piece = piece.strip()
                if looks_like_path(piece):
                    cands.add(piece)
        for m in PAT_BARE.finditer(src):
            s = m.group(1)
            if looks_like_path(s):
                cands.add(s)
    return cands


def try_all_prefixes(cand, from_file):
    """返回解出来的路径，或 None"""
    c = cand.replace("/", os.sep).replace("\\", os.sep)
    c = c.lstrip("." + os.sep)          # 去掉开头的 .\ 或 ..\
    parts = c.split(os.sep)

    # 从「当前文件所在目录」开始，逐级往上试
    d = os.path.dirname(from_file)
    for _ in range(8):
        p = os.path.normpath(os.path.join(d, *parts))
        if os.path.isfile(p):
            return p
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd

    # 再按「仓库根」试一次（人写 `A类文件\正文\x.md` 就是从根算的）
    p = os.path.normpath(os.path.join(BASE, *parts))
    if os.path.isfile(p):
        return p
    return None


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


BROKEN = []
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
        if try_all_prefixes(cand, f) is None:
            BROKEN.append((rel, cand))

lines = []
lines.append("")
lines.append("=" * 78)
lines.append("  死链检查 v2  ——  只报「真的解不出来」的引用")
lines.append("=" * 78)
lines.append("  扫描活文件区 .md %d 份 · 路径引用 %d 条" % (len(files), TOTAL))
lines.append("")

if BROKEN:
    lines.append("  🔴 断链 %d 条：" % len(BROKEN))
    seen = set()
    for rel, cand in BROKEN:
        k = (rel, cand)
        if k in seen:
            continue
        seen.add(k)
        lines.append("    %-50s → %s" % (rel, cand))
else:
    lines.append("  ✅ 断链 0 条")
lines.append("")
lines.append("-" * 78)
lines.append("  合计 %d 条引用 · 断链 %d" % (TOTAL, len(BROKEN)))
lines.append("=" * 78)
lines.append("")

report = "\n".join(lines)
with io.open(os.path.join(BASE, "工具", "_deadlink_out.txt"), "w",
             encoding="utf-8", newline="\n") as fh:
    fh.write(report)
print(report)
sys.exit(1 if BROKEN else 0)
