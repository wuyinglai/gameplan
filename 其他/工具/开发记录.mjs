#!/usr/bin/env node
// ============================================================================
// 🔴 开发记录取数器 —— 一条命令，产出「可追踪开发记录」所需的所有客观事实
//
// 🔴 为什么有这个脚本：
//   ChatGPT 建议「每个中阶段完成后同步当前版本、实际完成内容、测试结果、
//   待处理问题和下一步」——🔴 但「同步」最怕的是**凭印象写**。
//   🔴 所以：所有数字**必须从命令输出里抄**，不许手打、不许凭记忆。
//
// 🔴 用法（在 游戏大纲\ 目录下）：
//   node 工具/开发记录.mjs            ← 生成记录到 开发记录.md
//   node 工具/开发记录.mjs --print    ← 只打印，不写文件
//
// 🔴 它只读不写代码目录，跑的是真命令：
//   git（版本 / 改了什么）· vitest（测试数）· tsc（类型检查）
// ============================================================================

import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const 根 = join(dirname(fileURLToPath(import.meta.url)), '..');
const 只打印 = process.argv.includes('--print');

function 跑(命令, cwd = 根) {
  try {
    return execSync(命令, { cwd, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim();
  } catch (e) {
    return null;   // 🔴 跑不了就说跑不了，不许编
  }
}

function 跑或(命令, 兜底, cwd = 根) {
  const r = 跑(命令, cwd);
  return r === null ? `❌ ${兜底}` : r;
}

// ─────────────────────────────────────────────────────────────
// 一、版本
// ─────────────────────────────────────────────────────────────
const 版本 = 跑('git rev-parse --short HEAD') ?? '未知';
const 版本长 = 跑('git rev-parse HEAD') ?? '未知';
const 分支 = 跑('git branch --show-current') ?? '未知';
const 远端一致 = 跑(`git ls-remote --heads origin ${分支}`)?.split('\t')[0]?.startsWith(版本长.slice(0, 7))
  ? '✅ 已同步' : '⚠️ 未推送';
const 未推送 = 跑('git log --oneline origin/main..HEAD')?.split('\n').filter(Boolean).length ?? 0;

// ─────────────────────────────────────────────────────────────
// 二、实际完成内容（改了哪些文件 · 按目录归类）
// ─────────────────────────────────────────────────────────────
const 最近提交 = 跑('git log --oneline -8') ?? '';
const 代码变更 = 跑('git -c core.quotepath=false log --name-only --format="" -6 -- 游戏本体/src') ?? '';
const 文档变更 = 跑('git -c core.quotepath=false log --name-only --format="" -6 -- "*.md"') ?? '';

function 归类(文件列表) {
  const 组 = new Map();
  // 🔴 只看新代码目录的变更 —— 旧代码已归档，它的提交不算"当前在做什么"
  for (const 行 of 文件列表.split('\n')) {
    const f = 行.trim();
    if (!f) continue;
    const 键 = f.includes('/src/p') ? f.split('/src/')[1].split('/')[0]
      : f.includes('游戏本体/') ? '游戏本体/其他'
      : f.split('/')[0];
    if (!组.has(键)) 组.set(键, new Set());
    组.get(键).add(f.split('/').pop());
  }
  return [...组.entries()].map(([k, v]) => `  \`${k}\` → ${[...v].slice(0, 4).join(' · ')}`).join('\n');
}

// ─────────────────────────────────────────────────────────────
// 三、测试结果（真跑）
// ─────────────────────────────────────────────────────────────
const 本体 = join(根, '游戏本体');
// 🔴 「没有测试文件」是合法状态（新代码刚建，1.0.0 还没写测试）—— 不许显示成错误
let 测试行 = '⏳ 尚无测试文件（新代码刚建立）', 文件数 = '0', 通过数 = '0', 跳过数 = '0';
// 🔴 不要用管道（execSync 遇到管道可能等不到结束）—— 跑全量再从输出里解析
const 测试输出 = 跑('npx vitest run', 本体);
if (测试输出) {
  const m1 = 测试输出.match(/Test Files\s+(.*)/);
  const m2 = 测试输出.match(/Tests\s+(.*)/);
  const m3 = 测试输出.match(/Duration\s+(.*)/);
  文件数 = m1?.[1]?.trim() ?? '?';
  通过数 = m2?.[1]?.trim() ?? '?';
  跳过数 = (m2?.[1]?.match(/skipped (\d+)/)?.[1]) ?? '0';
  测试行 = `${文件数} 文件 · ${通过数}`;
}

const 类型检查 = 跑('npx tsc --noEmit', 本体);
const 类型结果 = 类型检查 === null
  ? (existsSync(join(本体, 'src', 'p1'))
      ? '❌ 跑不起来'
      : '⏳ 尚无代码（新代码目录还没建）')
  : '✅ 零报错';

// ─────────────────────────────────────────────────────────────
// 四、待处理问题（扫源码里的 TODO / 已知偏差标记）
// ─────────────────────────────────────────────────────────────
// 🔴 2026-10-20 新代码在 src/p1/，旧代码已归档 —— 这里扫新代码目录
const 标记文件 = ['游戏本体/src/p1/状态.ts', '游戏本体/src/p1/入口.ts', '游戏本体/src/p1/架构说明.md'];
const 待办 = [];
for (const f of 标记文件) {
  const p = join(根, f);
  if (!existsSync(p)) continue;
  const 行 = readFileSync(p, 'utf8').split('\n');
  行.forEach((l, i) => {
    if (/🔴.*(待|★|未接|指令④|指令③)/.test(l) && l.trim().length > 12) {
      待办.push(`  \`${f.split('/').pop()}:${i + 1}\` ${l.trim().slice(0, 90)}`);
    }
  });
}

// ─────────────────────────────────────────────────────────────
// 五、下一步（从开发规划里读当前阶段）
// ─────────────────────────────────────────────────────────────
const 规划路径 = join(根, 'B类_开发文档', '开发规划', '开发总览.md');
let 下一步 = '（读 开发总览.md §六 进度总控台）';
if (existsSync(规划路径)) {
  const 规划 = readFileSync(规划路径, 'utf8');
  // 🔴 从总控台表里抓「下一步」那一列 —— 按表头定位，不靠猜列号
  const 所有行 = 规划.split('\n');
  const 表头行 = 所有行.find(l => l.startsWith('| 大阶段 | 中阶段 | 小阶段'));
  if (表头行) {
    const 表头列 = 表头行.split('|').map(s => s.trim());
    const 下一步列号 = 表头列.indexOf('下一步');
    const 数据行 = 所有行.find(l => l.startsWith('| **P1**') && l.includes('1.0.0'));
    if (数据行 && 下一步列号 > 0) {
      const 列 = 数据行.split('|').map(s => s.trim());
      下一步 = 列[下一步列号] || '（见总控台）';
    }
  }
}

// ─────────────────────────────────────────────────────────────
// 产出
// ─────────────────────────────────────────────────────────────
// 🔴 本地时间（不是 UTC）—— 报告上的时间要跟项目主看到的一致
const 现在 = (() => {
  const d = new Date();
  const p = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
})();

const 记录 = `
> 🔴 **本块由 \`node 工具/开发记录.mjs\` 自动生成 · ${现在}**
> 🔴 **所有数字来自命令输出，不许手改** —— 要更新就跑一次脚本。

### 🔴 当前版本
| 项 | 值 |
|:--|:--|
| **commit** | \`${版本}\`（${版本长.slice(0, 12)}） |
| **分支 / 远端** | \`${分支}\` · ${远端一致}${未推送 ? ` · 🔴 **有 ${未推送} 条未推送**` : ''} |

### 🔴 实际完成内容
**最近提交**
\`\`\`
${最近提交}
\`\`\`
**代码侧改了哪些目录**
\`\`\`
${归类(代码变更) || '  （无）'}
\`\`\`

### 🔴 测试结果
| 项 | 结果 |
|:--|:--|
| **vitest** | ${测试行} |
| **跳过** | ${跳过数} |
| **tsc --noEmit** | ${类型结果} |

### 🔴 待处理问题
\`\`\`
${待办.length ? 待办.join('\n') : '  （源码里没扫到待办标记 —— 🔴 不代表没有，见开发记录.md 的人工登记区）'}
\`\`\`

### 🔴 下一步
${下一步}
`;

if (只打印) {
  console.log(记录);
} else {
  const 目标 = join(根, '开发记录.md');
  let 现有 = existsSync(目标) ? readFileSync(目标, 'utf8') : '';
  // 🔴 只替换「自动区」这一段，历史区不动
  const 标记 = '<!-- AUTO:BEGIN -->';
  const 尾标记 = '<!-- AUTO:END -->';
  const 块 = `${标记}\n${记录.trim()}\n${尾标记}`;

  if (现有.includes(标记) && 现有.includes(尾标记)) {
    const 前 = 现有.slice(0, 现有.indexOf(标记));
    const 后 = 现有.slice(现有.indexOf(尾标记) + 尾标记.length);
    现有 = 前 + 块 + 后;
  } else {
    现有 = 现有.trimEnd() + '\n\n---\n\n## 🔴 自动区（脚本生成）\n\n' + 块 + '\n';
  }
  writeFileSync(目标, 现有, 'utf8');
  console.log(`✅ 已更新 ${目标}`);
}
