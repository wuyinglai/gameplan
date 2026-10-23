#!/usr/bin/env node
// ============================================================================
// 🔴 地图同步器 —— 换地图时跑一次，杜绝「假绿」
//
// 🔴 问题（2026-10-19 真的踩过）：
//   换图后没人把新图复制进代码目录，🔴 **43 条测试全绿，跑的却是已经被换掉的图**。
//   🔴 假绿比红更危险 —— 红会被人看见。
//
// 🔴 用法（在 游戏大纲\ 目录下）：
//   node 工具/地图同步.mjs            ← 检查 + 同步（发现不一致就同步并报告）
//   node 工具/地图同步.mjs --check    ← 只检查不改（CI 用）
//
// 🔴 唯一数据源：B类_开发文档\基础文档\测试地图_v0.7\地图.json
// 🔴 副本：      游戏本体\src\bNN\地图.json（每个阶段目录都要）
// ============================================================================

import { readFileSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

const 根 = join(dirname(fileURLToPath(import.meta.url)), '..');
const 源 = join(根, 'B类_开发文档', '基础文档', '测试地图_v0.7', '地图.json');
const 代码根 = join(根, '游戏本体', 'src');
const 只检查 = process.argv.includes('--check');

const md5 = (buf) => createHash('md5').update(buf).digest('hex');

if (!existsSync(源)) {
  console.error(`❌ 找不到数据源：${源}`);
  process.exit(1);
}

const 源buf = readFileSync(源);
const 源hash = md5(源buf);
console.log(`\n🔴 数据源：${源.replace(根 + '\\', '')}`);
console.log(`🔴 md5：${源hash}\n`);

// 找所有阶段目录
// 🔴 2026-10-21 修：重构后阶段目录叫 p1（以前叫 b01）。原来的正则只认 b\d+，
//    重命名之后一个目录都扫不到 → 循环空转 → 明明副本不存在却打印「全部一致」。
//    🔴 一个「扫不到东西就说一切正常」的检查比没有检查更危险，所以这里改两处：
//    ① 正则同时认 pNN / bNN；② 扫不到任何阶段目录 = 直接报错退出，不许报平安。
let 目录 = [];
try {
  目录 = readdirSync(代码根, { withFileTypes: true })
    .filter(d => d.isDirectory() && /^[bp]\d+$/.test(d.name))
    .map(d => d.name)
    .sort();
} catch {
  console.error(`❌ 找不到代码目录：${代码根}`);
  process.exit(1);
}

if (目录.length === 0) {
  console.error(`❌ ${代码根} 下一个阶段目录都没有（形如 p1 / b01）—— 这不正常，不许报平安`);
  process.exit(1);
}

const 副本 = 目录.map(d => ({ 阶段: d, 路径: join(代码根, d, '地图.json') }));
let 不一致 = 0;
let 缺失 = 0;

for (const c of 副本) {
  if (!existsSync(c.路径)) {
    缺失++;
    console.log(`  🔴 ${c.阶段} → 没有地图.json`);
    if (!只检查) {
      writeFileSync(c.路径, 源buf);
      console.log(`     ✅ 已从数据源复制`);
    }
    continue;
  }
  const h = md5(readFileSync(c.路径));
  if (h === 源hash) {
    console.log(`  ✅ ${c.阶段} → 一致`);
  } else {
    不一致++;
    console.log(`  🔴 ${c.阶段} → 🔴 **不一致**（${h.slice(0, 8)}… ≠ ${源hash.slice(0, 8)}…）`);
    if (!只检查) {
      writeFileSync(c.路径, 源buf);
      console.log(`     ✅ 已从数据源同步`);
    }
  }
}

console.log('');
if (不一致 === 0 && 缺失 === 0) {
  console.log('✅ 全部一致 —— 跑的测试用的是当前这张图');
} else if (只检查) {
  console.log(`❌ 有 ${不一致} 处不一致 + ${缺失} 处缺失 —— 🔴 跑测试前先同步`);
  process.exit(1);
} else {
  console.log(`✅ 已同步 ${不一致} 处 + 补了 ${缺失} 处 —— 现在可以跑测试了`);
}
console.log('');
