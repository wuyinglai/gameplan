// ============================================================================
// P2 中阶段 2.A · 判据 13 + 补充断言（日结算02）—— 指令 HERMES_P2_2A §4 / §8
//
// 🔴 本文件只测「P2 自己这条链单独跑对不对」：
//    日结算02() 全程不调 P1 的 结算.跨日()，也没有任何调用方（指令 §0 约束 3）。
// ============================================================================

import { describe, it, expect } from 'vitest';
import { 新建商队 } from './资源';
import { 日结算02 } from './日结算02';
import { 断粮扣血百分比, 断水扣血百分比 } from './消耗补给';
// 🔴 用 vite 的 ?raw 导入读源码 —— 🔴 不用 node:fs
// 🔴 原因：项目 tsconfig 的 types 只有 vitest/globals，🔴 没有 @types/node，
// 🔴 用 node:fs 会让 tsc 报 TS2307（🔴 这条我验收 2.A 时漏了）
import 消耗补给源码 from './消耗补给.ts?raw';
import 日结算02源码 from './日结算02.ts?raw';

describe('判据 13 · 14 份粮 · 14 人 · 连跑三次（指令 §8.1「归零那一刻不罚」）', () => {
  it('第一次扣到 0 不罚 → 第二次起每天 −2（士气 10 → 8 → 6）', () => {
    const 状态 = 新建商队();
    状态.资源.食物 = 14;
    状态.资源.清水 = 14;
    状态.资源.士气 = 10;            // 顶到士气上限（3A:510），新建商队() 默认是 0

    // —— 第 1 天：刚好够吃一天，扣完归零 ——
    const 第一天 = 日结算02(状态);
    expect(第一天.扣了多少食物).toBe(14);
    expect(第一天.扣了多少清水).toBe(14);
    expect(状态.资源.食物).toBe(0);
    expect(状态.资源.清水).toBe(0);
    expect(第一天.食物耗尽).toBe(true);
    expect(第一天.清水耗尽).toBe(true);
    expect(第一天.施加了惩罚).toBe(false);        // 🔴 归零那一刻不罚
    expect(第一天.士气变化).toBe(0);
    expect(状态.资源.士气).toBe(10);

    // —— 第 2 天：昨天就已经是 0 → 双重惩罚叠加 −2 ——
    const 第二天 = 日结算02(状态);
    expect(第二天.扣了多少食物).toBe(0);          // 手上没粮可扣
    expect(第二天.施加了惩罚).toBe(true);
    expect(第二天.士气变化).toBe(2);
    expect(状态.资源.士气).toBe(8);

    // —— 第 3 天：继续 −2 ——
    const 第三天 = 日结算02(状态);
    expect(第三天.施加了惩罚).toBe(true);
    expect(第三天.士气变化).toBe(2);
    expect(状态.资源.士气).toBe(6);

    // 🔴 三条链上不许出现负数
    expect(状态.资源.食物).toBeGreaterThanOrEqual(0);
    expect(状态.资源.清水).toBeGreaterThanOrEqual(0);
    expect(状态.资源.士气).toBeGreaterThanOrEqual(0);
  });
});

describe('补充 · 血上限惩罚本阶段只记数字（指令 §8.3）', () => {
  it('百分比是 10 / 20，而且商队状态里没有偷偷长出血量字段', () => {
    expect(断粮扣血百分比()).toBe(10);            // 3A:105
    expect(断水扣血百分比()).toBe(20);            // 3A:113
    const 状态 = 新建商队();
    日结算02(状态);
    const 野 = 状态 as unknown as Record<string, unknown>;
    expect(野.血量).toBeUndefined();               // 🔴 血量是 P6 的字段
    expect(野.最大生命).toBeUndefined();
    expect(野.角色列表).toBeUndefined();
    // 🔴 断粮只会让已有的三个数变小，不会冒出新字段
    expect(Object.keys(状态).sort()).toEqual(['出战人数', '资源', '车辆数']);
  });
});


// ============================================================================
// 判据 14 · 阶段之间不许互相依赖（指令 §0 约束 2）
// ============================================================================

describe('判据 14 · 阶段之间不许互相依赖', () => {
  it('资源篮 14　`消耗补给.ts` / `日结算02.ts` 里一行 `src/p1` 都不许有', () => {
    for (const 源 of [消耗补给源码, 日结算02源码]) {
      // 🔴 只查**真正的 import 语句**，不看注释 ——
      // 🔴 注释里写「全文不许出现 from '../p1/...'`」是在警告不要写它，
      // 🔴 🔴 那句话本身含有 `../p1/` 字样，🔴 如果全文搜就会把自己判成不合格。
      const 导入行 = 源
        .split('\n')
        .filter((L: string) => /^\s*import\b/.test(L))
        .join('\n');
      expect(导入行).not.toMatch(/\.\.\/p1\//);
      expect(导入行).not.toMatch(/['"][^'"]*p1\//);
      // 🔴 require(...) 同样不行
      const require行 = 源.split('\n').filter((L: string) => /\brequire\s*\(/.test(L)).join('\n');
      expect(require行).not.toMatch(/p1/);
    }
  });
});
