# -*- coding: utf-8 -*-
"""
自验脚本 —— 每次交付前跑一遍
================================
用法：python 工具/自验.py

它回答一个问题：**「这份产出哪些是我自己就能保证的？」**
凡是它能查的，都不该占用项目主的注意力。

它查的东西全是机械可判的：
  1  目录结构对不对
  2  路径引用有没有漏改（🔴 最容易出事的地方）
  3  A 类文件的只读锁有没有上
  4  编码 / 行尾有没有乱
  5  历史快照有没有被误改（🔴 git 一查就知道）
  6  关键文件在不在
  7  入口文件指向的目录是不是都真实存在

退出码：0 = 全过；1 = 有 FAIL
"""
import io
import os
import subprocess
import sys

# Windows 控制台默认 GBK，中文+符号会渲染成乱码 -> 强制 UTF-8
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 活文件区 = 需要保持最新的 ──────────────────────────────
ACTIVE_DIRS = [
    "A类文件",
    "B类_开发文档",
    "AI交流",
    "项目管理",
    "工具",
    "游戏本体",
]
# ── 历史区 = 快照原样，不该被改 ────────────────────────────
FROZEN_DIRS = ["90_历史与废案", "01_Demo计划", "00_废弃清单", ".workbuddy", "其他"]

results = []


def add(name, ok, detail=""):
    results.append((name, "PASS" if ok else "FAIL", detail))


def read_text(path):
    try:
        with io.open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


def all_md(roots):
    out = []
    for r in roots:
        p = os.path.join(BASE, r)
        if not os.path.isdir(p):
            continue
        for dp, dns, fns in os.walk(p):
            dns[:] = [d for d in dns if d not in ("node_modules", ".git", "dist")]
            for fn in fns:
                if fn.endswith(".md"):
                    out.append(os.path.join(dp, fn))
    return out


def git_status():
    """返回三类文件列表：修改 / 新增 / 删除"""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=BASE, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except Exception as e:
        return None, None, None
    mod, new, dele = [], [], []
    for line in r.stdout.splitlines():
        if len(line) < 4:
            continue
        code = line[:2]
        path = line[3:].strip().strip('"')
        if "->" in path:
            path = path.split("->")[-1].strip().strip('"')
        if code.strip() == "??":
            new.append(path)
        elif "D" in code:
            dele.append(path)
        else:
            mod.append(path)
    return mod, new, dele


# ═══════════════════════════════════════════════════════════
# 1 · 目录结构
# ═══════════════════════════════════════════════════════════
root_files = sorted(f for f in os.listdir(BASE) if os.path.isfile(os.path.join(BASE, f)))
expected_root = sorted([".gitignore", "README.md", "开发规划.md"])
add("根目录只留 3 个文件", root_files == expected_root,
    "实际: " + (", ".join(root_files) if root_files else "(空)"))

for d in ["A类文件/正文", "A类文件/附件", "B类_开发文档", "AI交流", "项目管理", "工具", "游戏本体"]:
    add("目录存在: " + d, os.path.isdir(os.path.join(BASE, d)))

# ═══════════════════════════════════════════════════════════
# 2 · 路径引用漏改（🔴 最容易出事）
# ═══════════════════════════════════════════════════════════
STALE = ["0A_权威系统文档", "A类文件附件"]
# 允许出现旧路径的地方：目录重组说明段落（含箭头）
ALLOW_FILES = {
    os.path.join(BASE, "README.md"),
    os.path.join(BASE, "A类文件", "README.md"),
    os.path.join(BASE, "开发规划.md"),
}

stale_hits = []
for f in all_md(ACTIVE_DIRS):
    if os.path.abspath(f) in {os.path.abspath(x) for x in ALLOW_FILES}:
        continue
    t = read_text(f)
    if t is None:
        continue
    for i, line in enumerate(t.splitlines(), 1):
        for s in STALE:
            if s in line:
                stale_hits.append("%s:%d  [%s]" % (os.path.relpath(f, BASE), i, s))
add("活文件区无旧路径残留", not stale_hits,
    ("%d 处: " % len(stale_hits)) + " | ".join(stale_hits[:5]) if stale_hits else "")

# 入口文件指向的目录要真实存在
entry = read_text(os.path.join(BASE, "开发规划.md")) or ""
missing_ref = []
for m in ("A类文件", "B类_开发文档", "项目管理", "AI交流", "工具", "游戏本体",
          "90_历史与废案", "00_废弃清单", "01_Demo计划"):
    if m in entry and not os.path.isdir(os.path.join(BASE, m)):
        missing_ref.append(m)
add("入口文件指向的目录都存在", not missing_ref, ", ".join(missing_ref))

# ═══════════════════════════════════════════════════════════
# 3 · A 类只读锁
# ═══════════════════════════════════════════════════════════
not_locked = []
for dp, dns, fns in os.walk(os.path.join(BASE, "A类文件")):
    for fn in fns:
        p = os.path.join(dp, fn)
        # Windows 上用 attrib 判断只读属性（os.stat 的 st_mode 位在 Windows 上不可靠）
        try:
            readonly = bool(os.stat(p).st_file_attributes & 0x1)  # FILE_ATTRIBUTE_READONLY
        except AttributeError:
            readonly = not (os.stat(p).st_mode & 0o200)
        if not readonly:
            not_locked.append(os.path.relpath(p, BASE))
add("A 类文件全部只读上锁", not not_locked,
    ("%d 个没锁: " % len(not_locked)) + ", ".join(not_locked[:5]) if not_locked else "")

# ═══════════════════════════════════════════════════════════
# 4 · 编码 / 行尾
# ═══════════════════════════════════════════════════════════
bom_files, mixed_eol = [], []
for f in all_md(ACTIVE_DIRS):
    raw = open(f, "rb").read()
    if raw.startswith(b"\xef\xbb\xbf"):
        bom_files.append(os.path.relpath(f, BASE))
    if b"\r\n" in raw and b"\n" in raw.replace(b"\r\n", b""):
        mixed_eol.append(os.path.relpath(f, BASE))
add("无 UTF-8 BOM", not bom_files, ", ".join(bom_files[:5]))
add("单文件行尾统一（不混 CRLF/LF）", not mixed_eol,
    ("%d 个: " % len(mixed_eol)) + ", ".join(mixed_eol[:5]) if mixed_eol else "")

# ═══════════════════════════════════════════════════════════
# 5 · 历史快照没被误改
# ═══════════════════════════════════════════════════════════
mod, new, dele = git_status()
if mod is None:
    add("历史快照未被误改", False, "git 不可用")
else:
    touched_frozen = []
    for p in mod:
        norm = p.replace("\\", "/")
        for fd in FROZEN_DIRS:
            if norm.startswith(fd + "/"):
                touched_frozen.append(norm)
    add("历史快照未被误改", not touched_frozen,
        ("%d 份: " % len(touched_frozen)) + ", ".join(touched_frozen[:5]) if touched_frozen else "")

# ═══════════════════════════════════════════════════════════
# 6 · 死链检查（🔴 指向不存在文件的引用 = 错）
# ═══════════════════════════════════════════════════════════
import subprocess
_dl = os.path.join(BASE, "工具", "_deadlink_out.txt")
try:
    r = subprocess.run([sys.executable, os.path.join(BASE, "工具", "死链检查.py")],
                       cwd=BASE, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=120)
    dl_txt = io.open(_dl, "r", encoding="utf-8").read()
    # 取「真断链」那一段的条数
    import re as _re
    m = _re.search(r"真断链（解不出来 = 错）：(\d+) 条", dl_txt)
    n_broken = int(m.group(1)) if m else -1
    add("无死链（引用指向的文件都存在）", n_broken == 0,
        ("%d 条真断链" % n_broken) if n_broken else "")
except Exception as e:
    add("无死链（引用指向的文件都存在）", False, "检查脚本跑失败: %s" % e)

# ═══════════════════════════════════════════════════════════
# 7 · 关键文件在不在
# ═══════════════════════════════════════════════════════════
KEY = [
    "README.md", "开发规划.md",
    "A类文件/README.md",
    "A类文件/正文/README.md",
    "A类文件/正文/铁律总纲.md",
    "A类文件/正文/第0A类_游戏介绍.md",
    "A类文件/正文/第0A类_体验总纲_权威口径.md",
    "A类文件/正文/第0B类_设计思路_权威口径.md",
    "A类文件/正文/第1A类_地图与商路系统_权威口径.md",
    "A类文件/正文/第2A类_地点系统_权威口径.md",
    "A类文件/正文/第3A类_商队资源与失败系统_权威口径.md",
    "A类文件/正文/第4A类_战斗系统_权威口径.md",
    "A类文件/正文/第5A类_天气与事件系统_权威口径.md",
    "A类文件/正文/第6A类_角色技能与成长系统_权威口径.md",
    "A类文件/正文/第7A类_世界观与设定_权威口径.md",
    "A类文件/正文/第8A类_灰烬生态系统_权威口径.md",
    "A类文件/正文/第10A类_订单与贸易_权威口径.md",
    "A类文件/附件/README.md",
    "B类_开发文档/开发规划/开发总览.md",
    "B类_开发文档/基础文档/第01B类_旅行基础.md",
    "B类_开发文档/基础文档/操作归属总表.md",
    "项目管理/项目主待裁定清单.md",
    "项目管理/开发记录.md",
    "项目管理/验收/项目主验收指南_P1.md",
    "AI交流/README.md",
]
miss = [k for k in KEY if not os.path.isfile(os.path.join(BASE, k))]
add("关键文件齐全（%d 项）" % len(KEY), not miss, ", ".join(miss))

# ═══════════════════════════════════════════════════════════
# 输出
# ═══════════════════════════════════════════════════════════
W = 46
lines = []
lines.append("")
lines.append("=" * 78)
lines.append("  自验结果  ——  这些项都不该占用项目主的注意力")
lines.append("=" * 78)
for name, st, detail in results:
    mark = "OK  " if st == "PASS" else "FAIL"
    lines.append("  [%s] %-*s %s" % (mark, W, name, detail))

fails = [r for r in results if r[1] == "FAIL"]
lines.append("-" * 78)
lines.append("  合计 %d 项 · 过 %d · 失败 %d" % (len(results), len(results) - len(fails), len(fails)))
lines.append("=" * 78)
lines.append("")

report = "\n".join(lines)

# 写一份 UTF-8 报告（ASCII 文件名 —— 避免任何编码问题）
out_path = os.path.join(BASE, "工具", "_selfcheck_out.txt")
with io.open(out_path, "w", encoding="utf-8", newline="\n") as f:
    f.write(report)

print(report)
sys.exit(1 if fails else 0)
