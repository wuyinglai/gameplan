# -*- coding: utf-8 -*-
"""
路径修复器 —— 把「语义简写路径」补成「从仓库根能解出来的完整路径」
==================================================================
用法：python 工具/路径修复.py [--dry]

背景（2026-10-24）：
  我写的路径是「语义简写」—— `正文\\第0B类.md` 其实是 `A类文件\\正文\\第0B类.md`。
  🔴 人能看懂，🔴 **但机器解不出来，Hermes 照着找也找不到** —— 这是真错。

修法：
  对每条断链，在仓库里按**文件名**找所有同名文件：
    · 只有 1 个匹配  → 唯一解，自动补成完整路径
    · 有多个匹配    → 不动，列出来交给人判断
    · 0 个匹配      → 真断链（指向已删除/已归档），单独报告

只改活文件区；历史区不碰。
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

DRY = "--dry" in sys.argv

PAT_QUOTE = re.compile(r"`([^`\n]{2,120})`")
PAT_BARE = re.compile(
    r"(?<![\w`])((?:[\w\u4e00-\u9fff.\-]+[\\/])+[\w\u4e00-\u9fff.\-]+\.(?:md|ts|tsx|js|mjs|json|csv|txt|html|py|png|jpg|xlsx|bat))"
)
EXT_DIRS = (".md", ".ts", ".tsx", ".js", ".mjs", ".json", ".csv", ".txt",
            ".html", ".py", ".png", ".jpg", ".xlsx", ".bat")

# 明显不是路径的（命令前缀）
CMD_PREFIX = ("python ", "node ", "npx ", "cd ", "git ", "npm ")


def is_external(s):
    s = s.strip()
    if not s:
        return True
    return s.startswith(("http://", "https://", "www.", "mailto:", "~"))


def looks_like_path(s):
    s = s.strip().strip("`")
    if not s or is_external(s):
        return False
    if len(s) > 110:
        return False
    if "*" in s or "?" in s or "..." in s:
        return False
    for p in CMD_PREFIX:
        if s.startswith(p):
            return False
    if not s.lower().endswith(EXT_DIRS):
        return False
    if "/" not in s and "\\" not in s:
        return False
    return True


def collect_candidates(text):
    no_fence = re.sub(r"```.*?```", "", text, flags=re.S)
    no_indent = re.sub(r"(?m)^(?:    |\t).*$", "", no_fence)
    cands = set()
    for m in PAT_QUOTE.finditer(no_indent):
        for piece in re.split(r"[·、，；,;（）()]", m.group(1)):
            piece = piece.strip()
            if looks_like_path(piece):
                cands.add(piece)
    for m in PAT_BARE.finditer(no_indent):
        s = m.group(1)
        if looks_like_path(s):
            cands.add(s)
    return cands


def try_all_prefixes(cand, from_file):
    """先按原样试（含 .. 前缀），再试逐级上溯，再试仓库根"""
    raw = cand.replace("/", os.sep).replace("\\", os.sep)

    # ① 原样（保留 .. / . 前缀）—— 从当前文件目录解
    p = os.path.normpath(os.path.join(os.path.dirname(from_file), raw))
    if os.path.isfile(p):
        return p

    # ② 砍掉前缀后逐级上溯
    c = raw.lstrip("." + os.sep)
    parts = c.split(os.sep)
    d = os.path.dirname(from_file)
    for _ in range(8):
        p = os.path.normpath(os.path.join(d, *parts))
        if os.path.isfile(p):
            return p
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd

    # ③ 从仓库根
    p = os.path.normpath(os.path.join(BASE, *parts))
    if os.path.isfile(p):
        return p
    return None


def build_index():
    """文件名 -> [完整相对路径, ...]"""
    idx = {}
    for dp, dns, fns in os.walk(BASE):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), BASE).replace("\\", "/")
            idx.setdefault(fn, []).append(rel)
    return idx


def live_md_files():
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


INDEX = build_index()
FIXED = []      # (文件, 原串, 新串)
AMBIG = []      # (文件, 原串, [候选...])
TRULY = []      # (文件, 原串)

files = live_md_files()

# 第一遍：收集所有断链
broken_by_file = {}
for f in files:
    rel = os.path.relpath(f, BASE).replace("\\", "/")
    try:
        with io.open(f, "r", encoding="utf-8") as fh:
            text = fh.read()
    except Exception:
        continue
    bad = []
    for cand in collect_candidates(text):
        if try_all_prefixes(cand, f) is None:
            bad.append(cand)
    if bad:
        broken_by_file[f] = bad

# 第二遍：对每条断链找唯一匹配
for f, cands in broken_by_file.items():
    rel = os.path.relpath(f, BASE).replace("\\", "/")
    for cand in cands:
        bn = os.path.basename(cand.replace("\\", "/"))
        matches = INDEX.get(bn, [])
        # 只保留真的存在的完整相对路径
        matches = [m for m in matches if os.path.isfile(os.path.join(BASE, m))]
        # 🔴 归档区的副本不算候选 —— 要指向「活的那份」
        live = [m for m in matches
                if not m.startswith(("90_历史与废案/", "01_Demo计划/", "00_废弃清单/"))]
        if len(live) == 1:
            # 保留原分隔符风格
            new = live[0].replace("/", "\\") if "\\" in cand else live[0]
            FIXED.append((rel, cand, new))
        elif len(live) > 1:
            AMBIG.append((rel, cand, live))
        elif len(matches) == 1:
            # 只有归档区有 —— 指向它（说明原引用指的是历史文件）
            new = matches[0].replace("/", "\\") if "\\" in cand else matches[0]
            FIXED.append((rel, cand, new))
        else:
            TRULY.append((rel, cand))

# 第三遍：实际替换（只替换完整反引号包裹的整串，避免误伤）
if FIXED and not DRY:
    by_file = {}
    for rel, old, new in FIXED:
        by_file.setdefault(rel, []).append((old, new))
    for rel, pairs in by_file.items():
        p = os.path.join(BASE, rel)
        with io.open(p, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
        nl = "\r\n" if "\r\n" in text else "\n"
        orig = text
        for old, new in pairs:
            # 🔴 关键：新路径必须「从引用方文件算起也能解出来」
            #    —— 仓库根相对路径对根目录文件有效，对子目录文件就要带 ..\
            new_try = new
            src_dir = os.path.dirname(os.path.join(BASE, rel))
            depth = len([x for x in src_dir.split(os.sep) if x]) - len(
                [x for x in BASE.split(os.sep) if x])
            prefix = ".." + os.sep * 0
            prefix = (".." + os.sep) * depth if depth > 0 else ""
            if depth > 0:
                cand_rel = prefix + new.replace("/", os.sep)
                if os.path.isfile(os.path.normpath(os.path.join(BASE, cand_rel))):
                    new_try = cand_rel
                    if "\\" in old:
                        new_try = new_try.replace("/", "\\")
                    else:
                        new_try = new_try.replace(os.sep, "/")
            # 只替换被反引号完整包裹的
            text = text.replace("`" + old + "`", "`" + new_try + "`")
        if text != orig:
            with io.open(p, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)

lines = []
lines.append("")
lines.append("=" * 78)
lines.append("  路径修复  ——  把「语义简写」补成「机器能解出来」")
lines.append("=" * 78)
lines.append("  模式：%s" % ("DRY（只报告不改）" if DRY else "实际修改"))
lines.append("")
lines.append("  ✅ 唯一匹配可自动补全：%d 条" % len(FIXED))
for rel, old, new in FIXED[:40]:
    lines.append("    %-44s %s" % (rel, old))
    lines.append("    %-44s → %s" % ("", new))
if len(FIXED) > 40:
    lines.append("    ... 还有 %d 条" % (len(FIXED) - 40))
lines.append("")
lines.append("  ⚠️  多个同名候选（需人工判断）：%d 条" % len(AMBIG))
for rel, old, matches in AMBIG[:25]:
    lines.append("    %-40s → %s" % (rel, old))
    lines.append("        候选: %s" % " | ".join(matches[:5]))
if len(AMBIG) > 25:
    lines.append("    ... 还有 %d 条" % (len(AMBIG) - 25))
lines.append("")
lines.append("  🔴 真断链（仓库里根本没有同名文件）：%d 条" % len(TRULY))
for rel, old in TRULY[:40]:
    lines.append("    %-44s → %s" % (rel, old))
if len(TRULY) > 40:
    lines.append("    ... 还有 %d 条" % (len(TRULY) - 40))
lines.append("")
lines.append("-" * 78)
lines.append("  自动修 %d · 需判断 %d · 真断 %d" % (len(FIXED), len(AMBIG), len(TRULY)))
lines.append("=" * 78)
lines.append("")

report = "\n".join(lines)
with io.open(os.path.join(BASE, "工具", "_pathfix_out.txt"), "w",
             encoding="utf-8", newline="\n") as fh:
    fh.write(report)
print(report)
sys.exit(0)
