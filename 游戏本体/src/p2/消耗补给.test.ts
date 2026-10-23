// ============================================================================
// P2 中阶段 2.A · 判据 1~12（消耗补给）—— 指令 HERMES_P2_2A §4
//
// 🔴 判据 5 的写法要求：食物与清水**分行断言**，
//    🔴 不许写 expect(食物).toBe(清水) 这种「看着测两样、实际只测一样」的断言（3A:93）。
// ============================================================================

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { 新建商队 } from './资源';
import { 每日消耗, 扣补给, 断粮扣士气, 断粮扣血百分比, 断水扣血百分比 } from './消耗补给';
import type { 商队状态 } from './资源';

/// 造一个商队：给足粮食 / 水，士气默认顶到上限 10（3A:510）
function 商队(份数: { 食物?: number; 清水?: number; 士气?: number; 出战人数?: number }): 商队状态 {
  const 状态 = 新建商队();
  状态.资源.食物 = 份数.食物 ?? 0;
  状态.资源.清水 = 份数.清水 ?? 0;
  状态.资源.士气 = 份数.士气 ?? 10;
  状态.出战人数 = 份数.出战人数 ?? 14;
  return 状态;
}

describe('判据 1~3 · 每日消耗（3A:65 / 3A:85 / 3A:89 / 3A:93）', () => {
  it('资源篮 1　每日消耗(14) = 14 份食物 + 14 份清水', () => {
    expect(每日消耗(14)).toEqual({ 食物: 14, 清水: 14 });
  });

  it('资源篮 2　每日消耗(3) = 3 份食物 + 3 份清水（A 类表里的「3 人初始出战基准」）', () => {
    expect(每日消耗(3)).toEqual({ 食物: 3, 清水: 3 });
  });

  it('判据 3　🔴 返回值正好两个字段，不许冒出第三个 / 不许合并成总数（3A:93）', () => {
    const 键 = Object.keys(每日消耗(14));
    expect(键.length).toBe(2);
    expect(键.sort()).toEqual(['清水', '食物']);
    expect((每日消耗(14) as Record<string, number>).总份数).toBeUndefined();
  });
});

describe('判据 4~8 · 扣补给（扣到 0 为止，不碰士气）', () => {
  it('判据 4　14 人 · 食物 30 → 扣一次剩 16', () => {
    const 状态 = 商队({ 食物: 30, 清水: 30 });
    扣补给(状态);
    expect(状态.资源.食物).toBe(16);            // 🔴 单独断言，不跟清水比
  });

  it('判据 5　同上 · 清水 30 → 扣一次剩 16', () => {
    const 状态 = 商队({ 食物: 30, 清水: 30 });
    扣补给(状态);
    expect(状态.资源.清水).toBe(16);            // 🔴 单独断言
  });

  it('判据 6　🔴 食物只有 10 份 · 14 人 → 剩 exactly 0，不许是负数', () => {
    const 状态 = 商队({ 食物: 10, 清水: 50 });
    const 果 = 扣补给(状态);
    expect(状态.资源.食物).toBe(0);
    expect(状态.资源.食物).toBeGreaterThanOrEqual(0);
    expect(果.扣了多少食物).toBe(10);            // 只扣到了手上有的 10 份
    expect(果.食物耗尽).toBe(true);
  });

  it('判据 7　🔴 清水只有 10 份 · 14 人 → 剩 exactly 0，不许负数', () => {
    const 状态 = 商队({ 食物: 50, 清水: 10 });
    const 果 = 扣补给(状态);
    expect(状态.资源.清水).toBe(0);
    expect(状态.资源.清水).toBeGreaterThanOrEqual(0);
    expect(果.扣了多少清水).toBe(10);
    expect(果.清水耗尽).toBe(true);
  });

  it('判据 8　🔴 扣完为 0 时士气一点不动（扣补给() 不碰士气，惩罚是另一段）', () => {
    const 状态 = 商队({ 食物: 14, 清水: 14, 士气: 10 });
    扣补给(状态);
    expect(状态.资源.食物).toBe(0);
    expect(状态.资源.清水).toBe(0);
    expect(状态.资源.士气).toBe(10);            // 🔴 一口没动
  });

  it('补　两个百分比函数只记 A 类的数字（指令 §8.3：本阶段不作用到任何字段）', () => {
    expect(断粮扣血百分比()).toBe(10);          // 3A:105
    expect(断水扣血百分比()).toBe(20);          // 3A:113
    const 状态 = 商队({ 食物: 0, 清水: 0 });
    expect((状态 as unknown as Record<string, unknown>).血量).toBeUndefined();  // 🔴 没偷偷造血量字段
    expect((状态 as unknown as Record<string, unknown>).最大生命).toBeUndefined();
  });
});

describe('判据 9~12 · 断粮断水惩罚（3A:105 / 3A:113 / 3A:129）', () => {
  it('判据 9　食物 = 0 → 士气 −1', () => {
    const 状态 = 商队({ 士气: 10 });
    expect(断粮扣士气(状态, true, false)).toBe(1);
    expect(状态.资源.士气).toBe(9);
  });

  it('判据 10　清水 = 0 → 士气 −1', () => {
    const 状态 = 商队({ 士气: 10 });
    expect(断粮扣士气(状态, false, true)).toBe(1);
    expect(状态.资源.士气).toBe(9);
  });

  it('判据 11　🔴 两者都 0 → 叠加 −2（指令 §8.2 的解释，待项目主确认）', () => {
    const 状态 = 商队({ 士气: 10 });
    expect(断粮扣士气(状态, true, true)).toBe(2);
    expect(状态.资源.士气).toBe(8);
  });

  it('判据 12　🔴 士气已经是 0 时断粮 → 还是 0，不许变 −1', () => {
    const 状态 = 商队({ 士气: 0 });
    expect(断粮扣士气(状态, true, true)).toBe(0);   // 下限截断，实际扣 0
    expect(状态.资源.士气).toBe(0);
    expect(状态.资源.士气).toBeGreaterThanOrEqual(0);
  });

  it('补　士气只剩 1 时双重惩罚也只掉到 0（不越过下限）', () => {
    const 状态 = 商队({ 士气: 1 });
    expect(断粮扣士气(状态, true, true)).toBe(1);
    expect(状态.资源.士气).toBe(0);
  });
});

describe('判据 14 · 阶段之间不许互相依赖（指令 §0 约束 2）', () => {
  const 读 = (名: string): string => readFileSync(fileURLToPath(new URL(`./${名}`, import.meta.url)), 'utf8');

  it('资源篮 14　`消耗补给.ts` / `日结算02.ts` 里一行 `src/p1` 都不许有', () => {
    for (const 名 of ['消耗补给.ts', '日结算02.ts']) {
      const 源 = 读(名);
      // 🔴 只查**真正的 import 语句**，不看注释 ——
      // 🔴 注释里写「全文不许出现 from '../p1/...'`」是在警告不要写它，
      // 🔴 🔴 那句话本身含有 `../p1/` 字样，🔴 如果全文搜就会把自己判成不合格。
      const 导入行 = 源
        .split('\n')
        .filter(L => /^\s*import\b/.test(L))
        .join('\n');
      expect(导入行).not.toMatch(/\.\.\/p1\//);
      expect(导入行).not.toMatch(/['"][^'"]*p1\//);
      // 🔴 require(...) 同样不行
      const require行 = 源.split('\n').filter(L => /\brequire\s*\(/.test(L)).join('\n');
      expect(require行).not.toMatch(/p1/);
    }
  });
});
