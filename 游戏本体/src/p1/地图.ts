// ============================================================================
// P1 · 地图 —— 只负责：怎么存、怎么查一格、怎么加载
// 🔴 不许碰：时间、体力、天气          依据：施工图 §3.1 / §4 步骤 0
//
// 🔴 地图 json 是**副本**，由 `node 工具/地图同步.mjs` 从
//    `B类_开发文档\基础文档\测试地图_v0.7\地图.json` 同步过来，🔴 不许手改这份。
//    2026-10-19 踩过：换图后没人复制，43 条测试全绿跑的却是旧图。
// ============================================================================

import 地图json from './地图.json';
import {
  T到类型, 该T是否可通行, 坐标键,
  type 地图对象, type 格子, type 路况档,
} from './类型';

/// 🔴 地图文件的形状（§3.4 实测：start/end 是**数组**不是对象）
interface 地图条目 { t: string; x: number; y: number; r?: number }
interface 地图文件形状 {
  map: { width: number; height: number };
  start: [number, number];
  end: [number, number];
  note?: string;
  locations: 地图条目[];
}

const 是整数 = (v: unknown): v is number => typeof v === 'number' && Number.isInteger(v);
const 是坐标对 = (v: unknown): v is [number, number] =>
  Array.isArray(v) && v.length === 2 && 是整数(v[0]) && 是整数(v[1]);

/// 🔴 未在 json 标注的格子 → 空地 · 普通 · 可通行。🔴 这是规则不是偷懒（§3.1）
/// 🔴 每次返回**新对象**，不许返回共享单例（谁改一下就会污染全图）
export function 默认格(): 格子 {
  return { 类型: '空地', 路况: 1, 可通行: true, 已到访: false, 地点名: null };
}

/// 🔴 路况：缺省 = 1 普通（判据 47）；不是 0~3 的脏值 → 按普通 + 打警告
function 取路况(r: unknown, 说明: string): 路况档 {
  if (r === undefined || r === null) return 1;
  if (r === 0 || r === 1 || r === 2 || r === 3) return r;
  console.warn(`⚠️ 路况 r 不在 0~3（收到 ${String(r)}，${说明}）—— 按「普通」处理`);
  return 1;
}

/// 🔴 加载地图。抛错 = 地图文件坏了，程序不该继续跑
export function 加载地图(原始: unknown = 地图json): 地图对象 {
  if (typeof 原始 !== 'object' || 原始 === null) {
    throw new Error('地图文件坏了：顶层不是对象');
  }
  const 文件 = 原始 as Partial<地图文件形状>;
  const 宽 = 文件.map?.width;
  const 高 = 文件.map?.height;
  if (!是整数(宽) || !是整数(高) || 宽 <= 0 || 高 <= 0) {
    throw new Error('地图文件坏了：缺 map.width / map.height（要正整数）');
  }
  if (!Array.isArray(文件.locations)) {
    throw new Error('地图文件坏了：缺 locations 数组');
  }
  // 🔴 start/end 在 json 里是数组，加载时**必须转成对象**（§3.4 明写）
  if (!是坐标对(文件.start)) throw new Error('地图文件坏了：start 要 [x, y]');
  if (!是坐标对(文件.end)) throw new Error('地图文件坏了：end 要 [x, y]');

  const 格子表 = new Map<string, 格子>();
  for (const 条 of 文件.locations) {
    const 类型 = T到类型[条.t];
    if (类型 === undefined) {
      throw new Error(
        `地图文件坏了：未知类型键 "${条.t}" @ ${条.x},${条.y} —— ` +
        `请补 类型.ts 的 T到类型，不许静默当空地`,
      );
    }
    if (!是整数(条.x) || !是整数(条.y)) {
      throw new Error(`地图文件坏了：坐标不是整数 @ ${String(条.x)},${String(条.y)}`);
    }
    if (条.x < 0 || 条.x >= 宽 || 条.y < 0 || 条.y >= 高) {
      throw new Error(`地图文件坏了：坐标越界 ${条.x},${条.y}（图 ${宽}×${高}）`);
    }
    const 键 = 坐标键(条.x, 条.y);
    if (格子表.has(键)) {
      // ⚠️ 施工图没规定「同一格被列两次」怎么办。这里取最保守的做法：
      //    🔴 不覆盖（先来的算）+ 打警告 —— 静默丢一条数据是最难查的那种。
      //    官方图 v0.7 实测 0 处重复，所以这条分支正常不触发。
      console.warn(`⚠️ 同一格被列了两次：${键} —— 保留先来的那条（规则未定义，已报待裁定）`);
      continue;
    }
    格子表.set(键, {
      类型,
      路况: 取路况(条.r, `${条.t} @ ${条.x},${条.y}`),
      可通行: 该T是否可通行(条.t),      // 🔴 可通行由 **t 键** 决定，不由格子类型决定
      已到访: false,
      地点名: null,
    });
  }

  return {
    宽,
    高,
    起点: { x: 文件.start[0], y: 文件.start[1] },
    终点: { x: 文件.end[0], y: 文件.end[1] },
    格子表,
  };
}

/// 🔴 查一格。坐标不合法时**抛错**（不是返回 null —— §3.1）
export function 查格(地图: 地图对象, x: number, y: number): 格子 {
  if (!是整数(x) || !是整数(y)) {
    throw new Error(`坐标必须是整数，收到 ${String(x)},${String(y)}`);
  }
  if (x < 0 || x >= 地图.宽 || y < 0 || y >= 地图.高) {
    throw new Error(`坐标越界：${x},${y}（图 ${地图.宽}×${地图.高}，有效 0..${地图.宽 - 1} / 0..${地图.高 - 1}）`);
  }
  return 地图.格子表.get(坐标键(x, y)) ?? 默认格();
}

/// 🔴 这一格在图内吗 —— 走一格第 ① 步用（越界要返回「出地图了」而不是抛错）
export function 在图内(地图: 地图对象, x: number, y: number): boolean {
  return 是整数(x) && 是整数(y) && x >= 0 && x < 地图.宽 && y >= 0 && y < 地图.高;
}

/// 🔴 四方向是否相邻。🔴 全项目只有这一处判「相邻」（斜向 / 隔两格 / 原地都算 false）
export function 是否相邻(从: { x: number; y: number }, 到: { x: number; y: number }): boolean {
  return Math.abs(到.x - 从.x) + Math.abs(到.y - 从.y) === 1;
}
