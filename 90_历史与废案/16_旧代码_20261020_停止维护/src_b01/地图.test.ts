// ============================================================================
// 单元 01 · 指令① 那 7 条断言（+ 地图本身的守卫）
//
// 跑法：npx vitest run                    （根配置已含 src/b01/**，无需额外参数）
// ============================================================================

import { describe, it, expect, vi, beforeAll } from 'vitest';
import {
  加载地图, 查格, 设格, 解析路况, 可通行, 可停留,
  不可通行类型, 可停留类型, 全部格子类型, 坐标key,
} from './地图';
import type { 地图对象, 格子类型 } from './地图';
import 地图json from './地图.json';

/// 造一张最小假地图（默认 40×40），参数就是 locations 数组。
/// 🔴 start/end 跟着尺寸走（贴在角上），否则小图会因 end 越界被加载器拒（这是对的，是我写错了）
function 假地图(locations: unknown[], 宽 = 40, 高 = 40) {
  return {
    map: { width: 宽, height: 高 },
    start: [1, 1],
    end: [宽 - 2, 高 - 2],
    locations,
  };
}

describe('① 类型是扁平枚举 + 通行判断正确', () => {
  it('13 个值一个不多一个不少（防「山/水」被折成「地形」）', () => {
    expect([...全部格子类型].sort()).toEqual(
      [...['空地', '山', '水', '桥', '林', '废墟', '商路',
        '大城', '小城', '城镇', '驿站', '村庄', '营地']].sort(),
    );
    expect(全部格子类型.length).toBe(13);
    expect(全部格子类型).not.toContain('地形');
  });

  it('「山」「水」都判不可通行；其余 11 个值都可通行', () => {
    const 拦路名单: 格子类型[] = ['山', '水'];
    for (const 类型名 of 拦路名单) {
      expect(可通行(设格(假空地图(), 5, 5, 类型名)), `${类型名} 应当不可通行`).toBe(false);
    }
    const 应可通行: 格子类型[] = 全部格子类型.filter((类) => 类 !== '山' && 类 !== '水');
    for (const 类型名 of 应可通行) {
      expect(可通行(设格(假空地图(), 5, 5, 类型名)), `${类型名} 应当可通行`).toBe(true);
    }
  });

  it('废墟 / 桥 / 林 可通行；大城 / 驿站 / ... 可停留', () => {
    const 能走不能停: 格子类型[] = ['废墟', '桥', '林'];
    const 地点类: 格子类型[] = ['大城', '小城', '城镇', '驿站', '村庄', '营地'];
    for (const 类型名 of 能走不能停) {
      expect(可通行(设格(假空地图(), 5, 5, 类型名))).toBe(true);
    }
    for (const 类型名 of 地点类) {
      expect(可停留(设格(假空地图(), 5, 5, 类型名))).toBe(true);
    }
    // 非地点类一律不可停留
    const 不算停留: 格子类型[] = ['空地', '商路', '桥', '林', '废墟'];
    for (const 类型名 of 不算停留) {
      expect(可停留(设格(假空地图(), 5, 5, 类型名)), `${类型名} 不该算停留`).toBe(false);
    }
  });
});

/// 每次现造一张干净的空地图，免得 设格 互相污染
function 假空地图(): 地图对象 {
  return 加载地图(假地图([]));
}

describe('② 天气枚举与天气→体力消耗表（12 种）', () => {
  it('表里 12 个键，跟枚举一一对应', async () => {
    const 模块 = await import('./状态');
    const 表 = 模块.天气每格加成;
    expect(Object.keys(表).length).toBe(12);
    expect(Object.keys(表).sort()).toEqual([...十二种天气()].sort());
  });

  it('数值逐条核对施工图 §3.5.3 原表（不是抄我自己的表）', async () => {
    const { 天气每格加成 } = await import('./状态');
    const 原表: Record<string, number> = {
      晴朗: 0, 阴天: 0, 小雨: 0,
      暴雨: 5,
      高温: 0, 酷热: 5,
      寒潮: 0, 严寒: 5,
      浓雾: 0, 重雾: 5,
      灰烬风: 5, 灰烬风暴: 10,
    };
    expect(天气每格加成).toEqual(原表);
    // ★ 三个待确认值 + 灰烬风暴，单独钉一遍，改表时必须在这里留痕
    expect(天气每格加成['暴雨' as never]).toBe(5);
    expect(天气每格加成['重雾' as never]).toBe(5);
    expect(天气每格加成['灰烬风' as never]).toBe(5);
    expect(天气每格加成['灰烬风暴' as never]).toBe(10);
    expect(Object.values(天气每格加成).reduce((a, b) => a + b, 0)).toBe(35);  // 5×5 + 10
  });

  it('天气表里存的键名就是天气名，没有任何「_mod」后缀', async () => {
    const { 天气每格加成 } = await import('./状态');
    expect(Object.keys(天气每格加成).some((k) => k.endsWith('_mod'))).toBe(false);
  });
});

function 十二种天气(): string[] {
  return ['晴朗', '阴天', '小雨', '暴雨', '高温', '酷热', '寒潮', '严寒', '浓雾', '重雾', '灰烬风', '灰烬风暴'];
}

describe('③ 加载器对四种坏数据的反应', () => {
  it('未知类型键 → 抛错', () => {
    expect(() => 加载地图(假地图([{ t: 'castle', x: 2, y: 2 }]))).toThrowError(/未知类型键/);
  });

  it('special → 营地（可停留）、blk_ru → 废墟（不可停留）', () => {
    // 2026-10-19：原先这里断言两个旧键「映射表里没有 → 抛错」。指令① §四.3① 把全表
    // 补齐了，现在按表转换。⚠️ 全表原文自相矛盾（blk_ru 表格写废墟、正文写桥），
    // 已在指令文件里按表格值就地修正并署名留痕。
    const 图 = 加载地图(假地图([
      { t: 'special', x: 3, y: 3 },
      { t: 'blk_ru', x: 4, y: 4 },
    ]));
    const 营地格 = 查格(图, 3, 3);
    const 废墟格 = 查格(图, 4, 4);
    expect(营地格.类型).toBe('营地');
    expect(废墟格.类型).toBe('废墟');
    expect(可通行(营地格)).toBe(true);
    expect(可通行(废墟格)).toBe(true);
    // 营地按类型必然可停留（全表标 ❌ 在结构上做不到 —— 已记偏离）；废墟不可停留
    expect(可停留(营地格)).toBe(true);
    expect(可停留(废墟格)).toBe(false);
  });

  it('r = 7 越界 → 不抛错，按普通 + 打警告', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const 图 = 加载地图(假地图([{ t: 'road', x: 5, y: 5, r: 7 }]));
    expect(查格(图, 5, 5).路况档).toBe('普通');
    expect(警告).toHaveBeenCalledTimes(1);
    警告.mockRestore();
  });

  it('坐标 (999,999) 越界 → 抛错', () => {
    expect(() => 加载地图(假地图([{ t: 'road', x: 999, y: 999 }]))).toThrowError(/坐标越界/);
  });

  it('缺 start / 缺 end / 缺尺寸 / 顶层不是对象 → 四种都抛错', () => {
    const 骨架 = 假地图([]) as Record<string, unknown>;
    expect(() => 加载地图({ ...骨架, start: undefined })).toThrowError(/缺 start/);
    expect(() => 加载地图({ ...骨架, end: undefined })).toThrowError(/缺 end/);
    expect(() => 加载地图({ ...骨架, map: undefined })).toThrowError(/缺尺寸/);
    expect(() => 加载地图('一张地图')).toThrowError(/形状不对/);
  });
});

describe('④ 坐标查格', () => {
  it('范围内但 json 没列出的格子 → 返回默认（空地 · 普通 · 未到访）', () => {
    const 图 = 加载地图(假地图([{ t: 'road', x: 1, y: 1, r: 0 }], 10, 10));
    const 空格 = 查格(图, 7, 8);
    expect(空格.类型).toBe('空地');
    expect(空格.路况档).toBe('普通');
    expect(空格.已到访).toBe(false);
    expect(空格.地点名).toBeNull();
    // 🔴 默认格不能污染格子表
    expect(图.格子表.has(坐标key(7, 8))).toBe(false);
  });

  it('范围外 → 抛错（不许当成空地返回）', () => {
    const 图 = 加载地图(假地图([], 10, 10));
    expect(() => 查格(图, 10, 0)).toThrowError(/坐标越界/);
    expect(() => 查格(图, -1, 3)).toThrowError(/坐标越界/);
    expect(() => 查格(图, 3, 99)).toThrowError(/坐标越界/);
    expect(() => 查格(图, 1.5, 2)).toThrowError(/坐标必须是整数/);
  });

  it('把 (2,3) 从空地改成山 → 再查就是山且不可通行', () => {
    const 图 = 加载地图(假地图([], 10, 10));
    expect(查格(图, 2, 3).类型).toBe('空地');
    设格(图, 2, 3, '山');
    const 山格 = 查格(图, 2, 3);
    expect(山格.类型).toBe('山');
    expect(可通行(山格)).toBe(false);
    expect(图.格子表.has(坐标key(2, 3))).toBe(true);
    // 别的格不受影响
    expect(查格(图, 2, 4).类型).toBe('空地');
  });

  it('r 省 / 0 / 1 / 2 / 3 → 普通 / 好 / 普通 / 差 / 恶劣', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const 图 = 加载地图(假地图([
      { t: 'road', x: 1, y: 1 },
      { t: 'road', x: 1, y: 2, r: 0 },
      { t: 'road', x: 1, y: 3, r: 1 },
      { t: 'road', x: 1, y: 4, r: 2 },
      { t: 'road', x: 1, y: 5, r: 3 },
    ], 10, 10));
    expect(查格(图, 1, 1).路况档).toBe('普通');
    expect(查格(图, 1, 2).路况档).toBe('好');
    expect(查格(图, 1, 3).路况档).toBe('普通');
    expect(查格(图, 1, 4).路况档).toBe('差');
    expect(查格(图, 1, 5).路况档).toBe('恶劣');
    expect(警告).not.toHaveBeenCalled();
    警告.mockRestore();
  });

  it('路况只认 r，跟类型无关（桥 r=3 → 恶劣）', () => {
    expect(解析路况(3, '桥')).toBe('恶劣');
    expect(解析路况(undefined, '桥')).toBe('普通');
  });
});

describe('⑤ 🔴 防退化断言（当初那个静默 bug 的守门人）', () => {
  it('不可通行集合里的值必须都在枚举里', () => {
    for (const 值 of 不可通行类型) {
      expect(全部格子类型, `不可通行集合里有枚举外的值："${值}"`).toContain(值);
    }
  });

  it('可停留集合里的值必须都在枚举里', () => {
    for (const 值 of 可停留类型) {
      expect(全部格子类型, `可停留集合里有枚举外的值："${值}"`).toContain(值);
    }
  });

  it('反证：集合里塞一个枚举外的值，上面两条必须报错（断言本身不空转）', () => {
    const 脏集合 = new Set(['山', '深水']) as unknown as ReadonlySet<string>;
    const 会报错 = [...脏集合].some((值) => !全部格子类型.includes(值 as never));
    expect(会报错).toBe(true);
    expect([...脏集合].includes('山')).toBe(true);
  });
});

describe('⑥ 真实地图夹具能读出来（Gap 7 已裁定，不再 skip）', () => {
  let 地图!: 地图对象;
  beforeAll(() => { 地图 = 加载地图(地图json); });

  it('400×400，起点 = 大城、终点 = 小城（坐标从 json 读，不是写死的）', () => {
    expect(地图.宽).toBe(400);
    expect(地图.高).toBe(400);
    expect(查格(地图, 地图.起点.x, 地图.起点.y).类型).toBe('大城');
    expect(查格(地图, 地图.终点.x, 地图.终点.y).类型).toBe('小城');
    // ⚠️ 起点与终点本轮**都是可停留的城**，跨日效果完全一样（见回执：
    //    「驿站过夜」那两条 TC 用的是施工图 §6.4 的另一张图，不是这张夹具）。
    expect(可停留(查格(地图, 地图.终点.x, 地图.终点.y))).toBe(true);
  });

  it('夹具的每一格都读进来了；山/水 真的拦住玩家（数量按 json 现算，换图不失效）', () => {
    // 🔴 2026-10-19 改：原来这里写死 4254 / 2149 / 1155 / 734（旧占位图的快照）。
    //    官方测试图已换成 ChatGPT v0.7（41131 条），写死的数字会让测试在换图当天
    //    集体假红；反过来若有人只把数字改掉、地图其实没换对，也照样假绿。
    //    所以改成**从 json 现算**：断言的是「加载器 == 源数据」，与是哪张图无关。
    const 条目 = 地图json.locations as { t: string; x: number; y: number }[];
    const 按 = (键: string[]) => 条目.filter((o) => 键.includes(o.t)).length;
    const 山键 = ['block', 'blk_mt'], 水键 = ['blk_wt'];
    const 商路键 = ['road'];
    const 地点键 = ['big', 'small', 'town', 'village', 'inn1', 'inn0', 'camp', 'special'];

    const 全部 = [...地图.格子表.values()];
    // 加载器不许吞条目，也不许凭空造格（同坐标重复会被合并 → 比对唯一坐标数）
    expect(条目.length).toBe(new Set(条目.map((o) => `${o.x},${o.y}`)).size); // 夹具不许有重复格
    expect(全部.length).toBe(条目.length);

    let 山数 = 0, 水数 = 0, 商路数 = 0, 可停留数 = 0;
    for (const 格 of 全部) {
      if (!可通行(格)) {
        expect(['山', '水'], `意外不可通行的类型："${格.类型}"`).toContain(格.类型);
        if (格.类型 === '山') 山数 += 1;
        if (格.类型 === '水') 水数 += 1;
      }
      if (格.类型 === '商路') 商路数 += 1;
      if (可停留(格)) 可停留数 += 1;
    }
    expect(山数).toBe(按(山键));
    expect(水数).toBe(按(水键));
    expect(商路数).toBe(按(商路键));
    expect(可停留数).toBe(按(地点键));
    // 🔴 三块硬约束：图上确实有山有水有地点，否则上面四个断言会集体 0==0 空转
    expect(山数).toBeGreaterThan(0);
    expect(水数).toBeGreaterThan(0);
    expect(可停留数).toBeGreaterThan(0);
  });

  it('起点旁边那一格是可走的商路，路况「好」（r=0 生效）', () => {
    const 旁边 = 查格(地图, 地图.起点.x + 1, 地图.起点.y);
    expect(旁边.类型).toBe('商路');
    expect(旁边.路况档).toBe('好');
    expect(可通行(旁边)).toBe(true);
  });
});

describe('⑦ 同坐标重复的守卫（Gap 7：裁定 = 地点类优先 + 警告，不抛错）', () => {
  it('先山后城 → 保留城', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const 图 = 加载地图(假地图([
      { t: 'block', x: 9, y: 9 },
      { t: 'big', x: 9, y: 9 },
    ]));
    expect(查格(图, 9, 9).类型).toBe('大城');
    expect(警告).toHaveBeenCalledTimes(1);
    警告.mockRestore();
  });

  it('先城后山 → 还是保留城（顺序无关）', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const 图 = 加载地图(假地图([
      { t: 'big', x: 9, y: 9 },
      { t: 'block', x: 9, y: 9 },
    ]));
    expect(查格(图, 9, 9).类型).toBe('大城');
    expect(警告).toHaveBeenCalledTimes(1);
    警告.mockRestore();
  });

  it('两条都可通行（商路 + 商路）→ 保留先来的那条，并打警告', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    const 图 = 加载地图(假地图([
      { t: 'road', x: 8, y: 8, r: 0 },
      { t: 'road', x: 8, y: 8, r: 2 },
    ]));
    expect(查格(图, 8, 8).路况档).toBe('好');
    expect(警告).toHaveBeenCalledTimes(1);
    警告.mockRestore();
  });

  it('不重复时不打任何警告', () => {
    const 警告 = vi.spyOn(console, 'warn').mockImplementation(() => {});
    加载地图(假地图([{ t: 'road', x: 2, y: 2, r: 0 }, { t: 'inn1', x: 3, y: 3, r: 1 }], 20, 20));
    expect(警告).not.toHaveBeenCalled();
    警告.mockRestore();
  });
});

describe('⑧ 数据卫生：起点终点从 json 读，不许硬编码（硬约束 6）', () => {
  // 不用 fs 扫源码（工程没装 @types/node），改成**行为验证**：
  // 换两张 start/end 完全不同的地图，初始位置跟着变 —— 写死了就会露馅。
  it('两张地图的起点不同 → 新局出生点跟着不同', async () => {
    const { 新建游戏状态 } = await import('./状态');
    const 甲 = 加载地图({
      map: { width: 20, height: 20 }, start: [3, 17], end: [19, 1],
      locations: [{ t: 'big', x: 3, y: 17 }, { t: 'small', x: 19, y: 1 }],
    });
    const 乙 = 加载地图({
      map: { width: 30, height: 12 }, start: [29, 0], end: [0, 11],
      locations: [{ t: 'big', x: 29, y: 0 }, { t: 'small', x: 0, y: 11 }],
    });
    expect(新建游戏状态(甲).当前坐标).toEqual({ x: 3, y: 17 });
    expect(新建游戏状态(乙).当前坐标).toEqual({ x: 29, y: 0 });
    expect(新建游戏状态(甲).地图.终点).toEqual({ x: 19, y: 1 });
    expect(新建游戏状态(乙).地图.宽).toBe(30);
  });
});
