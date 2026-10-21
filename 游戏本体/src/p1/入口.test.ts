// ============================================================================
// 演示入口（项目主看的就是这段输出）—— 只验「能跑、打印的是中文、数字对得上」
// ============================================================================

import { describe, it, expect, vi } from 'vitest';
import { 演示, 描述 } from './入口';
import { 加载地图 } from './地图';
import { 新建游戏状态 } from './状态';
import 地图json from './地图.json';

describe('演示入口', () => {
  it('跑完不抛错，并且打的是中文行', () => {
    const 打印 = vi.spyOn(console, 'log').mockImplementation(() => {});
    expect(() => 演示()).not.toThrow();
    const 全部行 = 打印.mock.calls.map((c) => String(c[0])).join('\n');
    打印.mockRestore();
    expect(全部行).toContain('《余烬商队》P1 演示');
    expect(全部行).toContain('第 1 天 07:00');
    expect(全部行).toContain('体力 100 / 100');
  });

  it('描述() 一行里同时有天数、时刻、坐标、体力', () => {
    const 状态 = 新建游戏状态(加载地图(地图json));
    expect(描述('状态', 状态)).toContain('第 1 天 07:00');
    expect(描述('状态', 状态)).toContain('体力 100 / 100');
    expect(描述('状态', 状态)).toContain(`(${状态.当前坐标.x}, ${状态.当前坐标.y})`);
  });
});
