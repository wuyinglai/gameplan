// ============================================================================
// 🔴 第一阶段验收演示 ——「跑一趟看看它是什么样」
//
// 🔴 这个文件干什么：43 条测试证明「数字对」，但证明不了「这游戏跑起来像不像游戏」。
//    它从起点走到终点，把每一天实际发生了什么打成中文表，然后**自己报出发现的问题**。
//
// 🔴 项目主怎么用：在 `游戏本体\` 目录跑`npx vitest run src/b01/验收演示.test.ts`
//    屏幕上会出现行程表 + 一份「本次跑出来的问题」清单。
//
// 🔴 只读：不改任何游戏逻辑，只调用已有函数并打印。
// ============================================================================

import { describe, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { 加载地图, 可通行, 查格 } from './地图';
import { 新建游戏状态 } from './状态';
import { 走一格 } from './主循环';
import { 结束当天 } from './结束当天';
import type { 游戏状态 } from './状态';
import type { 坐标, 地图对象 } from './地图';

interface RunResult {
  到达: boolean; 格数: number; 天数: number; 跨日数: number; 休息晚数: number;
  每日格数: number[]; 经过地点: string[]; 剩余体力: number;
  最短路格数: number; 卡死原因: string | null;
}

let 上一次: RunResult | null = null;

describe('🔴 第一阶段验收演示', () => {
  it('A · 默认跑法（走不动就收工）', () => {
    const r = runTrip(() => null, '默认跑法');
    上一次 = r;
    打印报告(r, 'A · 默认跑法（走不动就收工）');
    reportIssues(r);
  });

  it('B · 省力跑法（开局先歇一晚把体力攒满）', () => {
    const r = runTrip(() => {
      const 地图 = loadMap();
      const 状态 = 新建游戏状态(地图);
      结束当天(状态);          // 开局先歇一晚 → 体力满100
      return 状态;
    }, '省力跑法');
    打印报告(r, 'B · 省力跑法（开局先歇一晚）');
    if (上一次) 打印对比(上一次, r);
  });
});

function loadMap(): 地图对象 {
  const 原始 = readFileSync('./src/b01/地图.json', 'utf8');
  return 加载地图(JSON.parse(原始));
}

function runTrip(开局钩: () => 游戏状态 | null, 标签: string): RunResult {
  const 地图 = loadMap();
  const 状态 = 开局钩() ?? 新建游戏状态(地图);
  const 起 = { ...状态.当前坐标 };
  const 终 = 地图.终点;
  const 终点key = `${终.x},${终.y}`;

  const 路径 = BFS(地图, `${起.x},${起.y}`, 终点key);
  const out: RunResult = {
    到达: false, 格数: 0, 天数: 1, 跨日数: 0, 休息晚数: 0,
    每日格数: [], 经过地点: [], 剩余体力: 0,
    最短路格数: 路径 ? 路径.length - 1 : -1, 卡死原因: null,
  };

  console.log('\n' + '═'.repeat(84));
  console.log(`  跑法：${标签}`);
  console.log('═'.repeat(84));
  console.log(`起点（${起.x}, ${起.y}）大城  →  终点（${终.x}, ${终.y}）小城`);
  console.log(`BFS 最短可通行距离：${out.最短路格数} 格`);
  console.log('规则：每格 2 小时 · 07:00→19:00 = 最多 6 格/天 · 每格扣 15 点 · 每天回 50 点\n');

  if (!路径) { out.卡死原因 = '起终点不连通'; return out; }

  const 到过 = new Set<string>();
  let 步 = 1, 今日 = 0;

  while (步 < 路径.length && out.格数 < 900) {
    const 目标 = 路径[步];
    const r = 走一格(状态, 目标);

    if (r.成功) {
      步++; out.格数++; 今日++;
      const 格 = 查格(地图, 状态.当前坐标.x, 状态.当前坐标.y);
      if (格.地点名) 到过.add(`${格.类型}·${格.地点名}`);
      const 点 = 格.地点名 ? `  ← 🔴【${格.类型}·${格.地点名}】` : '';
      const 跨 = r.跨日了 ? `  ══ 第${状态.第几天}天 07:00 体力 ${状态.野外体力} ══` : '';
      console.log(
        `第${String(状态.第几天).padStart(3)}天 ${String(状态.当前小时).padStart(2, '0')}:00` +
        `  (${String(状态.当前坐标.x).padStart(3)},${String(状态.当前坐标.y).padStart(3)})` +
        `  体力 ${String(状态.野外体力).padStart(3)}  ${格.类型}${点}${跨}`
      );
      if (r.跨日了) { out.跨日数++; out.每日格数.push(今日); 今日 = 0; }
      if (`${状态.当前坐标.x},${状态.当前坐标.y}` === 终点key) { out.到达 = true; break; }
    } else if (r.原因?.includes('走不动') || r.原因?.includes('时间不够')) {
      const e = 结束当天(状态);
      if (!e.成功) {
        out.卡死原因 = `「结束当天」失败：${e.原因}`;
        console.log(`\n⚠ ${out.卡死原因}\n🔴🔴🔴 卡死了 —— 该有办法但没有。\n`);
        break;
      }
      out.休息晚数++;
      out.每日格数.push(今日); 今日 = 0;
      console.log(`  ☾ 走不动(${状态.野外体力} 点) → 收工 → 第${状态.第几天}天 07:00 体力 ${状态.野外体力}\n`);
    } else {
      out.卡死原因 = r.原因;
      console.log(`\n⚠ 走不动了：${r.原因}\n`);
      break;
    }
  }
  if (今日 > 0) out.每日格数.push(今日);
  out.天数 = 状态.第几天;
  out.剩余体力 = 状态.野外体力;
  out.经过地点 = [...到过];
  //🔴 走完路径最后一步也算到达
  if (!out.到达 && `${状态.当前坐标.x},${状态.当前坐标.y}` === 终点key) out.到达 = true;
  return out;
}

function 打印报告(r: RunResult, 标签: string) {
  const 最多 = r.每日格数.length ? Math.max(...r.每日格数) : 0;
  const 最少 = r.每日格数.length ? Math.min(...r.每日格数) : 0;
  const 平均 = r.每日格数.length
    ? (r.每日格数.reduce((a, b) => a + b, 0) / r.每日格数.length).toFixed(1) : '—';

  console.log('─'.repeat(84));
  console.log(`【结果】${标签}`);
  console.log('─'.repeat(84));
  console.log(`  到达终点　　${r.到达 ? '✅ 是' : '❌ 否'}${r.卡死原因 ? `　（${r.卡死原因}）` : ''}`);
  console.log(`  走了　　　　${r.格数} 格（BFS 最短 ${r.最短路格数} 格）`);
  console.log(`  用时　　　　${r.天数} 天 · 跨日 ${r.跨日数} 次 · 收工休息 ${r.休息晚数} 晚`);
  console.log(`  每天格数　　最少 ${最少} · 最多 ${最多} · 平均 ${平均}`);
  console.log(`  剩余体力　　${r.剩余体力} / 100`);
  console.log(`  经过地点　　${r.经过地点.length} 个${r.经过地点.length ? ` → ${r.经过地点.join('、')}` : ''}\n`);
}

function 打印对比(a: RunResult, b: RunResult) {
  const 省 = a.天数 - b.天数;
  console.log('═'.repeat(84));
  console.log('  🔴 对比：默认跑法 vs 省力跑法');
  console.log('═'.repeat(84));
  console.log(`  默认跑法　　${a.天数} 天`);
  console.log(`  省力跑法　　${b.天数} 天`);
  console.log(`  差　　　　　${省} 天${省 > 0 ? ' ✅ 攒体力确实更快' : ' ⚠️ 攒体力反而没快'}`);
  console.log('');
}

/// 🔴 把跑出来的问题直接报出来 —— 这些是「数字对但设计可能不对」的地方
function reportIssues(r: RunResult) {
  const 问题: string[] = [];
  const 最多 = r.每日格数.length ? Math.max(...r.每日格数) : 0;
  const 平均 = r.每日格数.length
    ? r.每日格数.reduce((a, b) => a + b, 0) / r.每日格数.length : 0;

  if (r.到达 && r.天数 > 150) {
    问题.push(
      `🔴【太慢】${r.最短路格数} 格要 ${r.天数} 天（平均 ${平均.toFixed(1)} 格/天）。\n` +
      `    A 类说「正常 3 格/天」—— 对得上；超长档锚点是 250 天，这趟只占 ${Math.round(r.天数 / 250 * 100)}%。\n` +
      `    🔴 要确认：这个长度是「有意为之的漫长旅途」，还是「体力池算出来的意外结果」。`
    );
  }
  if (最多 < 6) {
    问题.push(
      `🔴【时间被浪费】一天能做 6 格，但最多只走到 ${最多} 格。\n` +
      `    原因：体力每天只回 50 点，6 格要 90 点 —— 🔴 **时间永远不是瓶颈，体力才是**。\n` +
      `    这意味着「07:00→19:00」这个设定目前不起作用，下午多半在空转。`
    );
  }
  if (r.休息晚数 > r.天数 * 0.5) {
    问题.push(
      `🔴【一半时间在休息】${r.天数} 天里有 ${r.休息晚数} 晚是「走不动了才收工」。\n` +
      `    这不是玩家的选择，是被数值逼的 —— 感觉像「一直在赶路又一直在歇」。`
    );
  }
  if (r.经过地点.length === 0) {
    问题.push(
      `⚠️【路上空荡荡】BFS 最短路一个地点都没经过。\n` +
      `    这是**脚本走法**的问题（BFS 只找最短，不挑风景），不是游戏的问题。\n` +
      `    但它提醒一件事：🔴 正式的「路线选择」机制还没做 —— 现在只会走最短路。`
    );
  }

  console.log('═'.repeat(84));
  console.log('  🔴 本次跑出来的问题（设计问题，不是 bug）');
  console.log('═'.repeat(84));
  if (!问题.length) console.log('  无');
  else 问题.forEach((p, i) => console.log(`\n【${i + 1}】${p}`));
  console.log('\n' + '═'.repeat(84) + '\n');
}

/// BFS 求最短可通行路径
function BFS(地图: 地图对象, 从: string, 到: string): 坐标[] | null {
  const { 宽, 高, 格子表 } = 地图;
  const 前驱 = new Map<string, string>();
  const 队列: string[] = [从];
  const 见过 = new Set<string>([从]);

  while (队列.length) {
    const cur = 队列.shift()!;
    if (cur === 到) break;
    const [x, y] = cur.split(',').map(Number);
    for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]] as const) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || nx >= 宽 || ny < 0 || ny >= 高) continue;
      const k = `${nx},${ny}`;
      if (见过.has(k)) continue;
      const 格 = 格子表.get(k);
      if (!格 || !可通行(格)) continue;
      见过.add(k);
      前驱.set(k, cur);
      队列.push(k);
    }
  }
  if (!见过.has(到)) return null;

  const 路径: 坐标[] = [];
  let cur = 到;
  while (cur !== 从) {
    const [x, y] = cur.split(',').map(Number);
    路径.unshift({ x, y });
    cur = 前驱.get(cur)!;
  }
  路径.unshift({ x: Number(从.split(',')[0]), y: Number(从.split(',')[1]) });
  return 路径;
}
