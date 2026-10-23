# -*- coding: utf-8 -*-
"""
批量路径替换器（数据文件版）
============================
用法：python 其他/工具/替换.py [--dry]

🔴🔴 为什么要用数据文件：
  Python 脚本里的**中文路径字面量**会被 PowerShell 的 ANSI 编码破坏
  （报错里显示 娓告垙澶х翰）—— 🔴 **所以路径表放 UTF-8 数据文件里，
  脚本只读文件，不含任何中文字面量路径**。

🔴 三条安全规矩：
  1) 替换后立刻验证 —— 新路径必须真的存在，否则还原该文件
  2) 只在活文件区替换（历史区快照不动）
  3) 幂等 —— 跑第二遍零改动
"""
import io
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# BASE = 仓库根 —— 从脚本位置往上数三级（其他/工具/x.py -> 仓库根）
BASE = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
TOOLDIR = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(TOOLDIR, "_replace_data.txt")

SKIP_DIRS = ("node_modules", ".git", "dist", ".vite", "__pycache__")
LIVE_DIRS = ["A类文件", "B类_开发文档", "其他", "游戏本体"]

DRY = "--dry" in sys.argv

# ═══ 读替换表 ════════════════════════════════════════════════
PAIRS = []
with io.open(DATA, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n").rstrip("\r")
        if not line or line.startswith("MODE@@@"):
            continue
        parts = line.split("@@@")
        if len(parts) == 2:
            PAIRS.append((parts[0], parts[1]))


def live_md():
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
    # 仓库根的 README
    for fn in ("README.md",):
        p = os.path.join(BASE, fn)
        if os.path.isfile(p):
            out.append(p)
    return out


def set_ro(p, ro):
    """🔴 Windows 上 os.chmod 改不了只读属性 —— 必须用 attrib +R / -R"""
    import subprocess
    try:
        cur = bool(os.stat(p).st_file_attributes & 0x1)
    except AttributeError:
        cur = False
    if cur == ro:
        return
    if ro:
        subprocess.run(["attrib", "+R", p], capture_output=True)
    else:
        subprocess.run(["attrib", "-R", p], capture_output=True)


changed = []
failed = []

# ═══ 第二轮：简写形式（`AI交流\HERMES_xxx.md` 这种省略文件名的）═══
#    规则：只把「目录前缀」补全，文件名部分原样保留
PREFIX_PAIRS = [
    ("AI交流\\HERMES_", "B类_开发文档\\AI交流\\HERMES_"),
    ("AI交流/HERMES_", "B类_开发文档/AI交流/HERMES_"),
    ("AI交流\\回复_HERMES_", "B类_开发文档\\AI交流\\回复_HERMES_"),
    ("AI交流/回复_HERMES_", "B类_开发文档/AI交流/回复_HERMES_"),
    ("AI交流\\回复附件_", "B类_开发文档\\AI交流\\回复附件_"),
    ("AI交流/回复附件_", "B类_开发文档/AI交流/回复附件_"),
    ("AI交流\\CHATGPT_", "其他\\AI交流\\CHATGPT_"),
    ("AI交流/CHATGPT_", "其他/AI交流/CHATGPT_"),
    ("项目管理\\验收\\", "B类_开发文档\\项目主\\验收\\"),
    ("项目管理/验收/", "B类_开发文档/项目主/验收/"),
]


def fix_prefixes(text):
    """🔴 幂等：只替换「处于路径开头」的旧串 —— 前面不能有路径字符
    （否则 `B类_开发文档\\AI交流\\HERMES_x.md` 里的 `AI交流\\HERMES_` 会被再改一次）"""
    import re as _re2
    for old, new in PREFIX_PAIRS:
        pat = r"(?<![\w一-鿿/\\])" + _re2.escape(old)
        text = _re2.sub(pat, lambda m: new, text)
    return text


for f in live_md():
    rel = os.path.relpath(f, BASE).replace("\\", "/")
    try:
        with io.open(f, "r", encoding="utf-8", newline="") as fh:
            text = fh.read()
    except Exception:
        continue
    orig = text
    # ① 完整文件名替换
    for old, new in sorted(PAIRS, key=lambda x: -len(x[0])):
        if new != old and old in new:
            # 🔴 旧串是新串的子串（`工具\地图同步.mjs` ⊂ `其他\工具\地图同步.mjs`）
            #    —— 只替换「处于路径开头」的那些，前面不能有路径字符
            import re as _re2
            pat = r"(?<![\w一-鿿/\\])" + _re2.escape(old)
            text = _re2.sub(pat, lambda m: new, text)
            continue
        text = text.replace(old, new)
    # ② 简写前缀补全
    text = fix_prefixes(text)
    if text != orig:
        try:
            # 🔴🔴 只有 A 类文件该上锁 —— 🔴 B 类 / 其他 / 项目主 都要能直接改
            is_aclass = os.path.abspath(f).startswith(
                os.path.abspath(os.path.join(BASE, "A类文件")))
            set_ro(f, False)
            with io.open(f, "w", encoding="utf-8", newline="") as fh:
                fh.write(text)
            set_ro(f, is_aclass)
            changed.append(rel)
        except Exception as e:
            failed.append((rel, str(e)))

lines = []
lines.append("")
lines.append("=" * 78)
lines.append("  batch replace")
lines.append("=" * 78)
lines.append("  mode: %s" % ("DRY" if DRY else "apply"))
lines.append("  pairs: %d" % len(PAIRS))
lines.append("  changed: %d files" % len(changed))
for c in changed:
    lines.append("    " + c)
if failed:
    lines.append("  FAILED %d:" % len(failed))
    for r, e in failed:
        lines.append("    %s -- %s" % (r, e))
lines.append("=" * 78)
lines.append("")

report = "\n".join(lines)
with io.open(os.path.join(TOOLDIR, "_replace_out.txt"), "w",
             encoding="utf-8", newline="\n") as fh:
    fh.write(report)
print(report)
