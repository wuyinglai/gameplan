// ============================================================================
// 测试专用工具 —— 🔴 不是产品代码；文件名不以 .test.ts 结尾，vitest 不会当成测试
//
// 🔴 两条硬要求：
//    ① 真图上的测试坐标一律**现找**，不许写死（图会重生成 —— 10-19 就是这么翻车的）
//    ② 需要「一定走得动 / 一定是某种路况」的链式测试，用构造的小图，不靠真图碰运气
// ============================================================================

import 地图json from './地图.json';
import { 加载地图 } from './地图';
import { 新建游戏状态 } from './状态';
import {
  T到类型, 该T是否可通行, 坐标键,
  type 格子类型, type 游戏状态, type 地图对象, type 路况档,
} from './类型';

interface 条目 { t: string; x: number; y: number; r?: number }
const 原始 = 地图json as unknown as {
  map: { width: number; height: number };
  start: [number, number];
  end: [number, number];
  locations: 条目[];
};

/// 每个测试自己加载一份（🔴 已到访是格上的可变字段，共享会互相污染）
export function 真图(): 地图对象 { return 加载地图(地图json); }
export function 真局(): 游戏状态 { return 新建游戏状态(真图()); }

/// 造一张小图：起点 (1,1)，向东排 长度-1 格商路 —— 时间/体力链专用
/// 🔴 边长必须 > 长度，否则最后一格会越界被加载器拒
export function 走廊图(长度 = 20, 路况: 路况档 = 0): 地图对象 {
  const 清单: 条目[] = [{ t: 'big', x: 1, y: 1 }];
  for (let x = 2; x <= 长度; x += 1) 清单.push({ t: 'road', x, y: 1, r: 路况 });
  const 边 = 长度 + 2;
  return 加载地图({ map: { width: 边, height: 边 }, start: [1, 1], end: [长度, 1], locations: 清单 });
}
export function 走廊局(长度 = 20, 路况: 路况档 = 0): 游戏状态 {
  return 新建游戏状态(走廊图(长度, 路况));
}

const 全部条目 = 原始.locations;
const 索引 = new Map(全部条目.map((o) => [坐标键(o.x, o.y), o] as const));
const 四邻 = (x: number, y: number) => [[x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]] as const;

/// 在真图上找一对相邻格：脚下可通行 + 目标满足条件（🔴 现找，不写死坐标）
export function 找一步(条件: (条: 条目) => boolean): {
  脚下: { x: number; y: number }; 目标: { x: number; y: number };
} {
  for (const 标 of 全部条目) {
    if (!条件(标)) continue;
    for (const [nx, ny] of 四邻(标.x, 标.y)) {
      const 邻 = 索引.get(坐标键(nx, ny));
      if (邻 && 该T是否可通行(邻.t)) {
        return { 脚下: { x: nx, y: ny }, 目标: { x: 标.x, y: 标.y } };
      }
    }
  }
  throw new Error('真图上找不到满足条件的相邻格 —— 图换了，测试要跟着改（不是代码错）');
}

export const 是山 = (条: 条目) => 条.t === 'block';
export const 是水 = (条: 条目) => 条.t === 'blk_wt';
export const 是碎石差路 = (条: 条目) => 条.t === 'blk_fr' && 条.r === 2;
export const 是商路好路 = (条: 条目) => 条.t === 'road' && 条.r === 0;

/// 终点旁边可站的一格（判据 12）
export function 终点旁边(): { x: number; y: number } {
  const [ex, ey] = 原始.end;
  const 上限x = 原始.map.width - 1, 上限y = 原始.map.height - 1;
  for (const [nx, ny] of 四邻(ex, ey)) {
    if (nx < 0 || ny < 0 || nx > 上限x || ny > 上限y) continue;
    const 邻 = 索引.get(坐标键(nx, ny));
    if (邻 && 该T是否可通行(邻.t)) return { x: nx, y: ny };
  }
  throw new Error('终点四周没有可站的格子');
}

/// 小图上摆一格（🔴 只用于构造数据的小图，不碰真图）
export function 摆一格(地图: 地图对象, x: number, y: number, t: string, 路况: 路况档 = 1): void {
  地图.格子表.set(坐标键(x, y), {
    类型: T到类型[t] as 格子类型,
    路况,
    可通行: 该T是否可通行(t),
    已到访: false,
    地点名: null,
  });
}

/// 快照状态里所有会变的东西 —— 断言「拒绝时状态一点没变」
export function 快照(状态: 游戏状态): string {
  return JSON.stringify({
    坐标: 状态.当前坐标, 天: 状态.第几天, 时: 状态.当前小时,
    体力: 状态.野外体力, 天气: 状态.当前天气, 天气剩余: 状态.天气剩余天数,
    已结算: 状态.今天已结算,
  });
}
