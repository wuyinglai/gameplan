// ============================================================================
// 测试专用工具 —— 🔴 不是产品代码；文件名不以 .test.ts 结尾，vitest 不会当成测试
//
// 🔴 两条硬要求：
//    ① 真图上的测试坐标一律**现找**，不许写死（图会重生成 —— 10-19 就是这么翻车的）
//    ② 需要「一定走得动 / 一定是某种路况」的链式测试，用构造的小图，不靠真图碰运气
// ============================================================================

import 地图json from './地图.json';
import { 加载地图, 查格 } from './地图';
import { 新建游戏状态 } from './状态';
import { 走一格 } from './移动';
import { 结束当天 } from './结束当天';
import {
  T到类型, 该T是否可通行, 坐标键, 地点类,
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

/// 🔴 真图最短路（BFS · 四方向 · 山/水 算堵）——
///    只给**测试与验收脚本**「走一趟 / 连跑 30 天」用。
/// 🔴 P1 不做选路玩法（正式选路是 P8 的事），这里只是要保证长跑有一条一定走得通的路，
///    而不是靠起点旁边的运气。
export function 真图最短路径(): { x: number; y: number }[] {
  const 宽 = 原始.map.width, 高 = 原始.map.height;
  const 堵 = new Set<string>();
  for (const 条 of 全部条目) if (!该T是否可通行(条.t)) 堵.add(坐标键(条.x, 条.y));

  const [起点x, 起点y] = 原始.start;
  const [终点x, 终点y] = 原始.end;
  const 前驱 = new Map<string, string | null>([[坐标键(起点x, 起点y), null]]);
  const 队列: Array<[number, number]> = [[起点x, 起点y]];   // 🔴 用指针推进，不用 shift（16 万格会慢到爆）
  let 头 = 0;
  let 到了 = false;

  while (头 < 队列.length && !到了) {
    const [x, y] = 队列[头];
    头 += 1;
    for (const [nx, ny] of 四邻(x, y)) {
      if (nx < 0 || ny < 0 || nx >= 宽 || ny >= 高) continue;
      const 键 = 坐标键(nx, ny);
      if (前驱.has(键) || 堵.has(键)) continue;
      前驱.set(键, 坐标键(x, y));
      if (nx === 终点x && ny === 终点y) { 到了 = true; break; }
      队列.push([nx, ny]);
    }
  }

  if (!到了) {
    throw new Error(
      `🔴 真图上从起点 ${起点x},${起点y} 走不到终点 ${终点x},${终点y}（可达 ${前驱.size} 格）—— 这是地图/死锁问题，不是测试问题`,
    );
  }

  const 路径: Array<{ x: number; y: number }> = [];
  let 当前: string | null = 坐标键(终点x, 终点y);
  while (当前 !== null) {
    const [x, y] = 当前.split(',').map(Number);
    路径.push({ x, y });
    当前 = 前驱.get(当前) ?? null;
  }
  return 路径.reverse();      // [起点, ..., 终点]
}

// ---------------------------------------------------------------------------
// 🔴 长跑驱动器 —— 「连跑 N 天」和「走一趟」共用同一套走法
//    （测试和验收脚本跑的是同一段逻辑，验收表里的数字才可复现）
// ---------------------------------------------------------------------------

export interface 长跑结果 {
  跨日次数: number;
  走过格数: number;
  抵达: boolean;
  停止原因: string;                 // '抵达终点' / '到天数上限' / 🔴 其它 = 卡死或走不通
  天数: number;
  时刻集合: number[];               // 🔴 全程出现过的 当前小时（断言里不许有 19）
  体力最低: number;
  体力最高: number;
  天气剩余最小: number;
  经过地点: string[];               // 走过的地点类格子的地点名 / 坐标
}

export interface 长跑限制 { 天数?: number; 格数?: number; 到终点?: boolean }

/// 沿给定路径一直走：走不动（体力/时间）就「结束当天」，直到抵达或触到上限。
/// 🔴 走不通 / 结束当天也被拒 = 死锁，立刻停下并把原因带回去（不静默、不硬试）。
export function 沿路径长跑(
  状态: 游戏状态,
  路径: ReadonlyArray<{ x: number; y: number }>,
  限制: 长跑限制 = {},
): 长跑结果 {
  const 结果: 长跑结果 = {
    跨日次数: 0, 走过格数: 0, 抵达: false, 停止原因: '', 天数: 状态.第几天,
    时刻集合: [状态.当前小时],        // 🔴 出发那一刻也要记进去，否则 07:00 永远不进数组
    体力最低: 状态.野外体力, 体力最高: 状态.野外体力,
    天气剩余最小: 状态.天气剩余天数, 经过地点: [],
  };
  const 看过 = new Set<number>(结果.时刻集合);
  const 记时刻 = () => {
    if (!看过.has(状态.当前小时)) { 看过.add(状态.当前小时); 结果.时刻集合.push(状态.当前小时); }
    结果.体力最低 = Math.min(结果.体力最低, 状态.野外体力);
    结果.体力最高 = Math.max(结果.体力最高, 状态.野外体力);
    结果.天气剩余最小 = Math.min(结果.天气剩余最小, 状态.天气剩余天数);
  };

  let 下一步 = 1;                       // 路径[0] 是起点，人已经站在那儿

  while (true) {
    结果.天数 = 状态.第几天;
    if (限制.天数 !== undefined && 状态.第几天 > 限制.天数) { 结果.停止原因 = '到天数上限'; break; }
    if (限制.格数 !== undefined && 结果.走过格数 >= 限制.格数) { 结果.停止原因 = '到格数上限'; break; }
    if (下一步 >= 路径.length) { 结果.停止原因 = 结果.抵达 ? '抵达终点' : '路径走完了'; break; }

    const 目标 = 路径[下一步];
    const 跨日前 = 状态.第几天;
    const 果 = 走一格(状态, 目标.x, 目标.y);
    记时刻();

    if (果.成功) {
      结果.走过格数 += 1;
      下一步 += 1;
      if (状态.第几天 > 跨日前) 结果.跨日次数 += 1;    // 保险丝：走路已不再顺带跨日（2026-10-23 裁定）
      const 格 = 查格(状态.地图, 状态.当前坐标.x, 状态.当前坐标.y);
      if (地点类.has(格.类型)) {
        结果.经过地点.push(格.地点名 ?? 坐标键(状态.当前坐标.x, 状态.当前坐标.y));
      }
      if (果.已抵达 === true) { 结果.抵达 = true; 结果.停止原因 = '抵达终点'; break; }
      continue;
    }

    if (果.原因 === '体力不够' || 果.原因 === '时间不够') {
      // ✍️ 2026-10-23 项目主裁定：走路不再自动跨日，跨日一律由 结束当天() 触发 ——
      //    所以这里一定能成功；旧代码那个「今天已结算过了 → 重试」分支已经不存在了。
      const 结 = 结束当天(状态);
      if (!结.成功) { 结果.停止原因 = `结束当天被拒：${结.原因}`; break; }
      结果.跨日次数 += 1;
      记时刻();
      continue;
    }

    // 过不去 / 出地图了 / 不是相邻格 —— 路径本身有问题，带现场回去
    结果.停止原因 = `走不通（${果.原因}）@ ${状态.当前坐标.x},${状态.当前坐标.y} → ${目标.x},${目标.y}`;
    break;
  }

  结果.天数 = 状态.第几天;
  return 结果;
}
