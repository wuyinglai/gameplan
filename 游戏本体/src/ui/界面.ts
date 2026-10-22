// ============================================================================
// 人工测试台（浏览器 UI）· 第 1 段：状态与画布
//
// 🔴 本文件只做三件事：读状态 → 画到 canvas → 把按钮点击转成对已有函数的调用。
//    页面里没有任何游戏规则（不扣体力、不算时间、不判通行）—— 全部调 src/p1、
//    src/p2 里已经写好并测过的函数。规则若出错，责任在被调的模块，不在这里。
// 跑法：npm run ui（= npx vite），浏览器开 http://localhost:5173
// ============================================================================

import { 加载地图, 查格, 是否相邻 } from '../p1/地图';
import { 新建游戏状态 } from '../p1/状态';
import { 走一格 } from '../p1/移动';
import { 结束当天 } from '../p1/结束当天';
import { 推进天气段, 天气段长, 天气概率 } from '../p1/天气';
import { 坐标键 } from '../p1/类型';
import { 侦察, 采集, 搜索, 补给, 修车, 治疗, 交易 } from '../p1/接口位';
import type { 格子类型, 天气名, 游戏状态, 操作结果 } from '../p1/类型';
import { 描述 } from '../p1/入口';
import 原始地图 from '../p1/地图.json';

type 原始项 = { t: string; x: number; y: number; r?: number };

const 地图 = 加载地图();
let 状态: 游戏状态 = 新建游戏状态(地图);
/// 上一次刷新时的「第几天」—— 报() 用它判断这次操作有没有跨日
/// （🔴 不能在 报() 里现记：调用方传参时 结束当天() 已经跑完了，天数早就变了）
let 上次天数 = 状态.第几天;

/// 🔴 水 / 山的 t 键只在这里用来上色（逻辑不认它 —— 通行与否由 p1 判）
const 水键 = new Set<string>();
const 山键 = new Set<string>();
for (const 项 of (原始地图 as { locations: 原始项[] }).locations) {
  if (项.t === 'blk_wt') 水键.add(坐标键(项.x, 项.y));
  else if (项.t === 'block') 山键.add(坐标键(项.x, 项.y));
}

const 类型色: Record<格子类型, string> = {
  大城: '#f0c674', 小城: '#d9a441', 城镇: '#8ac26b', 村庄: '#5c9e4a',
  驿站: '#5aa9e6', 营地: '#c58bd6',
  地形: '#6b5f4d',           // 可通行的地形（碎石地 / 桥）
  空地: '#2f3a48',
};
const 商路色 = '#6d6250';     // 空地且 r=0（路况好）
const 山色 = '#2b3644';
const 水色 = '#123246';

const 主画布 = document.getElementById('主视野') as HTMLCanvasElement;
const 小画布 = document.getElementById('小地图') as HTMLCanvasElement;
const 主画笔 = 主画布.getContext('2d')!;
const 小画笔 = 小画布.getContext('2d')!;
const 状态区 = document.getElementById('状态') as HTMLDivElement;
const 日志区 = document.getElementById('日志') as HTMLDivElement;

let 视野半径 = 20;              // 主视野看 41×41 格（可按「视野 ±」调）
const 画布边长 = 432;

/// 主视野最后一次画出来的布局 —— 「点地图」要把鼠标像素换算回格子坐标，全靠它
let 主布局 = { 每格: 10, 偏移: 11, 中心x: 0, 中心y: 0 };
/// 鼠标划过 / 刚点过的格子 —— 画成橙框 / 白闪框，让你确认「我点的是哪一格」
let 悬停: { x: number; y: number } | null = null;
let 闪烁: { x: number; y: number } | null = null;

// ---------------------------------------------------------------------------
// 第 2 段：上色与渲染（判定结果一律问 p1，本页不自己判规则）
// ---------------------------------------------------------------------------

function 颜色(x: number, y: number): string {
  const 键 = 坐标键(x, y);
  if (水键.has(键)) return 水色;      // blk_wt
  if (山键.has(键)) return 山色;      // block
  const 格 = 查格(地图, x, y);
  if (!格.可通行) return 山色;
  if (格.类型 === '空地') return 格.路况 === 0 ? 商路色 : 类型色.空地;
  return 类型色[格.类型];
}

function 方框(画笔: CanvasRenderingContext2D, x: number, y: number, 色: string, 尺寸: number): void {
  画笔.strokeStyle = 色;
  画笔.lineWidth = Math.max(1, Math.round(尺寸 / 4));
  画笔.strokeRect(x - 尺寸 / 2, y - 尺寸 / 2, 尺寸, 尺寸);
}

function 画标记(
  画笔: CanvasRenderingContext2D, 世界x: number, 世界y: number,
  屏幕x: number, 屏幕y: number, 色: string, 字: string, 每格: number,
): void {
  if (世界x < 0 || 世界y < 0 || 世界x >= 地图.宽 || 世界y >= 地图.高) return;
  方框(画笔, 屏幕x, 屏幕y, 色, Math.max(6, 每格));
  画笔.fillStyle = 色;
  画笔.font = `${Math.max(9, Math.round(每格 * 0.8))}px sans-serif`;
  画笔.fillText(字, 屏幕x + 每格, 屏幕y - 每格 / 3);
}

function 画主视野(): void {
  const 边数 = 视野半径 * 2 + 1;
  const 每格 = Math.floor(画布边长 / 边数);
  const 偏移 = Math.floor((画布边长 - 每格 * 边数) / 2);   // 网格比画布窄时居中，别贴左上角
  主画笔.fillStyle = '#0a0d12';
  主画笔.fillRect(0, 0, 画布边长, 画布边长);

  const 中心x = 状态.当前坐标.x;
  const 中心y = 状态.当前坐标.y;
  主布局 = { 每格, 偏移, 中心x, 中心y };      // ← 点地图换算坐标要用
  for (let dy = -视野半径; dy <= 视野半径; dy += 1) {
    for (let dx = -视野半径; dx <= 视野半径; dx += 1) {
      const x = 中心x + dx;
      const y = 中心y + dy;
      if (x < 0 || y < 0 || x >= 地图.宽 || y >= 地图.高) continue;   // 图外留黑
      主画笔.fillStyle = 颜色(x, y);
      主画笔.fillRect(偏移 + (dx + 视野半径) * 每格, 偏移 + (视野半径 - dy) * 每格, 每格, 每格);
    }
  }

  const 屏幕 = (x: number, y: number): [number, number] => [
    偏移 + (x - 中心x + 视野半径) * 每格 + 每格 / 2,
    偏移 + (视野半径 - (y - 中心y)) * 每格 + 每格 / 2,
  ];
  const [起x, 起y] = 屏幕(地图.起点.x, 地图.起点.y);
  const [终x, 终y] = 屏幕(地图.终点.x, 地图.终点.y);
  画标记(主画笔, 地图.起点.x, 地图.起点.y, 起x, 起y, '#f0c674', '起', 每格);
  画标记(主画笔, 地图.终点.x, 地图.终点.y, 终x, 终y, '#e05c5c', '终', 每格);

  // 商队本体（正中心）—— 🔴 双白框 + 坐标标签，让你一眼看清「我现在是哪一格」
  const [我x, 我y] = 屏幕(中心x, 中心y);
  主画笔.fillStyle = '#ffffff';
  主画笔.beginPath();
  主画笔.arc(我x, 我y, Math.max(3, 每格 / 2.6), 0, Math.PI * 2);
  主画笔.fill();
  方框(主画笔, 我x, 我y, '#ffffff', 每格);
  方框(主画笔, 我x, 我y, '#ffffff77', 每格 + 6);
  主画笔.fillStyle = '#ffffff';
  主画笔.font = '11px sans-serif';
  主画笔.fillText(`我 (${中心x}, ${中心y})`, 我x + 每格 / 2 + 4, 我y - 每格 / 2 - 3);

  // 鼠标悬停 = 橙色框（告诉你点下去会是哪一格）；刚点过的格子 = 白色外闪框
  if (悬停 !== null) {
    const [悬x, 悬y] = 屏幕(悬停.x, 悬停.y);
    方框(主画笔, 悬x, 悬y, '#e7873c', 每格 + 2);
    主画笔.fillStyle = '#e7873c';
    主画笔.fillText(`(${悬停.x}, ${悬停.y})`, 悬x + 每格 / 2 + 4, 悬y + 每格 / 2 + 10);
  }
  if (闪烁 !== null) {
    const [闪x, 闪y] = 屏幕(闪烁.x, 闪烁.y);
    方框(主画笔, 闪x, 闪y, '#ffffff', 每格 + 8);
  }
}

function 画小地图(): void {
  const 图 = 小画笔.createImageData(地图.宽, 地图.高);
  const 填 = (i: number, 十六: string): void => {
    图.data[i] = parseInt(十六.slice(1, 3), 16);
    图.data[i + 1] = parseInt(十六.slice(3, 5), 16);
    图.data[i + 2] = parseInt(十六.slice(5, 7), 16);
    图.data[i + 3] = 255;
  };
  for (let i = 0; i < 图.data.length; i += 4) 填(i, 类型色.空地);
  地图.格子表.forEach((格, 键) => {
    const [xs, ys] = 键.split(',');
    const x = Number(xs);
    const y = Number(ys);
    const i = ((地图.高 - 1 - y) * 地图.宽 + x) * 4;
    if (水键.has(键)) 填(i, 水色);
    else if (山键.has(键)) 填(i, 山色);
    else if (!格.可通行) 填(i, 山色);
    else if (格.类型 === '空地') 填(i, 格.路况 === 0 ? 商路色 : 类型色.空地);
    else 填(i, 类型色[格.类型]);
  });
  小画笔.putImageData(图, 0, 0);

  const 屏 = (x: number, y: number): [number, number] => [x, 地图.高 - 1 - y];
  const [起x, 起y] = 屏(地图.起点.x, 地图.起点.y);
  const [终x, 终y] = 屏(地图.终点.x, 地图.终点.y);
  方框(小画笔, 起x, 起y, '#f0c674', 7);
  方框(小画笔, 终x, 终y, '#e05c5c', 7);
  const [我x, 我y] = 屏(状态.当前坐标.x, 状态.当前坐标.y);
  小画笔.fillStyle = '#ffffff';
  小画笔.fillRect(我x - 2, 我y - 2, 5, 5);
}

// ---------------------------------------------------------------------------
// 第 3 段：状态栏、日志、按钮与键盘绑定
// ---------------------------------------------------------------------------

function 刷新(): void {
  const { x, y } = 状态.当前坐标;
  状态区.textContent = [
    `天气 ${状态.当前天气} · 还剩 ${状态.天气剩余天数} 天`,
    `体力 ${状态.野外体力} / ${状态.体力上限}`,
    `第 ${状态.第几天} 天 ${String(状态.当前小时).padStart(2, '0')}:00 · 位置 (${x}, ${y})`,
  ].join('\n');
  画主视野();
  画小地图();
  上次天数 = 状态.第几天;
}

let 序号 = 0;
function 记日志(文本: string, 类别: '成功' | '拒绝' | '说明' = '说明'): void {
  序号 += 1;
  const 行 = document.createElement('div');
  行.className = 类别;
  行.textContent = `${String(序号).padStart(2, '0')} · ${文本}`;
  日志区.appendChild(行);
  日志区.scrollTop = 日志区.scrollHeight;
}

function 报(动作: string, 果: 操作结果): void {
  const 跨了日 = 状态.第几天 !== 上次天数;          // 必须在 刷新() 之前比（刷新会把上次天数推平）
  if (果.成功) {
    记日志(`${动作} → ✅ ${果.已抵达 === true ? '已抵达（地点类格子）· ' : ''}${描述('现在', 状态).trim()}`, '成功');
  } else {
    记日志(`${动作} → ❌ 拒绝：${果.原因}（状态没变）`, '拒绝');
  }
  刷新();
  建天气面板();                                       // 跨日会换天气，● 标记跟着更新
  if (!果.成功 && (果.原因 === '体力不够' || 果.原因 === '时间不够')) 提示该收工(果.原因);
  else if (果.成功 && 跨了日) 复原收工按钮();
}

function 走(dx: number, dy: number, 动作: string): void {
  报(动作, 走一格(状态, 状态.当前坐标.x + dx, 状态.当前坐标.y + dy));
}

function 重开(): void {
  状态 = 新建游戏状态(地图);
  记日志('—— 重开：新建游戏状态()，回起点、第 1 天 07:00、体力 100 ——', '说明');
  刷新();
  复原收工按钮();
  建天气面板();
}

const 钮 = (id: string): HTMLButtonElement => document.getElementById(id) as HTMLButtonElement;

钮('往右').onclick = () => 走(1, 0, '往东走一格');
钮('往左').onclick = () => 走(-1, 0, '往西走一格');
钮('往上').onclick = () => 走(0, 1, '往北走一格（y+1）');
钮('往下').onclick = () => 走(0, -1, '往南走一格（y-1）');
钮('原地').onclick = () => 报('原地不动（判据 2）', 走一格(状态, 状态.当前坐标.x, 状态.当前坐标.y));
钮('结束当天').onclick = () => 报('结束当天', 结束当天(状态));
钮('重开').onclick = 重开;
钮('斜走').onclick = () => 走(1, 1, '斜着走一格（判据 2）');
钮('隔两格').onclick = () => 走(2, 0, '隔两格走（判据 3）');
钮('出图').onclick = () => 报('往图外走（判据 4）', 走一格(状态, -1, -1));
钮('跳到明天').onclick = () => {
  if (状态.今天已结算) {
    // 🔴 调试用：规则里一天只能跨一次（判据 24/25），要连推天数必须清掉这个幂等标记。
    //    这不是游戏规则，只是让你快速看到天气轮换、体力每日回复这些跨日才发生的事。
    状态.今天已结算 = false;
    记日志('⚠ 测试清掉「今天已结算」标记（规则是一天只跨一次，这里专为连推天数）', '说明');
  }
  报('⏩ 跳到明天', 结束当天(状态));
};
钮('拨到18点').onclick = () => {
  // 🔴 调试专用：正常时钟只有 7/9/11/13/15/17，走一格 2 小时最多正好 19:00，
  //    所以「时间不够」这条分支平时永远撞不到 —— 拨到 18:00 才测得到（判据 20）。
  状态.当前小时 = 18;
  记日志('已把 当前小时 拨到 18:00 —— 再走一格该被拒「时间不够」，且时间、体力都不动', '说明');
  刷新();
};
钮('体力清零').onclick = () => {
  状态.野外体力 = 0;
  记日志('已把 野外体力 直接改成 0 —— 下一步该被拒「体力不够」（判据 18）', '说明');
  刷新();
};
钮('放大').onclick = () => { 视野半径 = Math.max(5, 视野半径 - 5); 刷新(); };
钮('缩小').onclick = () => { 视野半径 = Math.min(60, 视野半径 + 5); 刷新(); };

const 接口位清单: Array<[string, (对谁: 游戏状态) => 操作结果]> = [
  ['侦察', 侦察], ['采集', 采集], ['搜索', 搜索], ['补给', 补给],
  ['修车', 修车], ['治疗', 治疗], ['交易', 交易],
];
const 接口位组 = document.getElementById('接口位组') as HTMLDivElement;
for (const [名, 函数] of 接口位清单) {
  const 钮位 = document.createElement('button');
  钮位.className = '接口位';
  钮位.textContent = 名;
  钮位.onclick = () => 报(`接口位「${名}」（P2~P7 空位）`, 函数(状态));
  接口位组.appendChild(钮位);
}

const 按键表: Record<string, () => void> = {
  arrowright: () => 走(1, 0, '往东走一格'), d: () => 走(1, 0, '往东走一格'),
  arrowleft: () => 走(-1, 0, '往西走一格'), a: () => 走(-1, 0, '往西走一格'),
  arrowup: () => 走(0, 1, '往北走一格（y+1）'), w: () => 走(0, 1, '往北走一格（y+1）'),
  arrowdown: () => 走(0, -1, '往南走一格（y-1）'), s: () => 走(0, -1, '往南走一格（y-1）'),
  ' ': () => 过一天('开始下一天（空格）'),
  r: 重开,
};
window.addEventListener('keydown', (事: KeyboardEvent) => {
  const 动作 = 按键表[事.key.toLowerCase()];
  if (动作 === undefined) return;
  事.preventDefault();
  动作();
});

记日志(
  `测试台起来了：地图 ${地图.宽}×${地图.高} · 登记 ${地图.格子表.size} 格 · `
  + `起点 (${地图.起点.x}, ${地图.起点.y}) → 终点 (${地图.终点.x}, ${地图.终点.y})`,
  '说明',
);
// ---------------------------------------------------------------------------
// 第 4 段：人工测试专用入口（天气调试 / 点地图直达 / 走不动了提示）
// 🔴 这些只是调试入口：不改任何规则函数。直达 🔴 不扣体力、不推时间，
//    日志里会写明「测试直达」，别把它当成游戏里的走法。
// ---------------------------------------------------------------------------

const 大按钮 = document.getElementById('开始下一天') as HTMLButtonElement;
const 收工原文 = 大按钮.textContent ?? '⏭ 结束今天 · 开始下一天';

/// 走不动了（体力/时间不够）→ 时间不会自己跨日，提示按大按钮
function 提示该收工(为什么: string): void {
  大按钮.style.background = '#8a4b1f';
  大按钮.style.borderColor = '#e7873c';
  大按钮.textContent = `⚠ ${为什么} · 点这里开始下一天`;
  记日志(`走不动了（${为什么}）。🔴 现在规则是「走到 19:00 才自动跨日」，卡住时时间会停住 —— 按橙色这个键才进第 ${状态.第几天 + 1} 天`, '说明');
}

function 复原收工按钮(): void {
  大按钮.style.background = '#2f6b3f';
  大按钮.style.borderColor = '#5aab6e';
  大按钮.textContent = 收工原文;
}

/// 测试台的「过一天」：原地站着也能连着按。
/// 规则里一天只跨一次（判据 24 / 25），要连着过得先清掉幂等标记 —— 小按钮「结束当天」
/// 保持原样（连点第二次必须被拒，那是你要测的幂等），只有这个大按钮和空格键会替你清。
function 过一天(标签: string): void {
  if (状态.今天已结算) {
    状态.今天已结算 = false;
    记日志('⚠ 测试台替你清掉「今天已结算」标记（规则：一天只跨一次）—— 这样原地站着也能连着过天数', '说明');
  }
  报(标签, 结束当天(状态));
}

大按钮.onclick = () => 过一天('开始下一天');

/// 点地图：相邻格 = 真走一格；远处格 = 测试直达；山/水 = 过不去
function 点到(x: number, y: number, 从哪: string): void {
  if (x === 状态.当前坐标.x && y === 状态.当前坐标.y) return;
  if (是否相邻(状态.当前坐标, { x, y })) {
    走(x - 状态.当前坐标.x, y - 状态.当前坐标.y, `点${从哪} (${x},${y}) 真走一格`);
    return;
  }
  if (x < 0 || y < 0 || x >= 地图.宽 || y >= 地图.高) {
    记日志(`点${从哪} (${x},${y}) → ❌ 出地图了`, '拒绝');
    return;
  }
  const 格 = 查格(地图, x, y);
  if (!格.可通行) {
    记日志(`点${从哪} (${x},${y}) → ❌ 过不去（这一格不可通行 · ${格.类型}）`, '拒绝');
    return;
  }
  const 从 = `(${状态.当前坐标.x},${状态.当前坐标.y})`;
  状态.当前坐标 = { x, y };
  记日志(`点${从哪} → ⚠ 测试直达：${从} → (${x},${y})。🔴 没扣体力、没推时间、没判时间够不够，不是游戏走法`, '说明');
  复原收工按钮();
  刷新();
}

/// 像素 → 格子坐标（主视野）
function 主视野格子(事: MouseEvent): { x: number; y: number } {
  const 矩形 = 主画布.getBoundingClientRect();
  const 像素x = (事.clientX - 矩形.left) * (主画布.width / 矩形.width);
  const 像素y = (事.clientY - 矩形.top) * (主画布.height / 矩形.height);
  const 列 = Math.floor((像素x - 主布局.偏移) / 主布局.每格) - 视野半径;
  const 行 = 视野半径 - Math.floor((像素y - 主布局.偏移) / 主布局.每格);
  return { x: 主布局.中心x + 列, y: 主布局.中心y + 行 };
}

/// 鼠标划过就套橙框 + 标坐标 —— 省得你点下去才知道点的是哪一格
主画布.addEventListener('mousemove', (事: MouseEvent) => {
  const 格 = 主视野格子(事);
  const 一样 = 悬停 !== null && 悬停.x === 格.x && 悬停.y === 格.y;
  if (一样) return;
  悬停 = 格;
  画主视野();
});
主画布.addEventListener('mouseleave', () => { 悬停 = null; 画主视野(); });

主画布.addEventListener('click', (事: MouseEvent) => {
  const 格 = 主视野格子(事);
  悬停 = 格;
  闪烁 = 格;                                     // 白闪一下，确认「这格我点到了」
  点到(格.x, 格.y, '主视野');
  window.setTimeout(() => { 闪烁 = null; 画主视野(); }, 450);
});

小画布.addEventListener('click', (事: MouseEvent) => {
  const 矩形 = 小画布.getBoundingClientRect();
  const x = Math.floor((事.clientX - 矩形.left) * (小画布.width / 矩形.width));
  const 屏y = Math.floor((事.clientY - 矩形.top) * (小画布.height / 矩形.height));
  点到(x, 地图.高 - 1 - 屏y, '小地图');
});

// —— 天气调试面板：点哪种就强制切成哪种；「随机掷一段」走真实跨日逻辑 ——

const 天气面板 = document.getElementById('天气面板') as HTMLDivElement;

/**
 * 强制切成指定天气，但 🔴 段长走真实随机（写 5~7 天就 5 / 6 / 7 都可能，不再一律取下限）。
 * 做法：把 剩余 设成 1 逼 推进天气段() 重掷，同时注入一个随机源 ——
 * 第一掷返回目标天气概率带的中点（保证掷中它），之后交回 Math.random()（段长真随机）。
 * 掷天气与掷段长全在 天气.ts 的真实代码里跑，本页不自己算数。
 */
function 强制天气(天气: 天气名): void {
  let 累计 = 0;
  let 骰值 = 0.999;
  for (const 候选 of Object.keys(天气概率) as 天气名[]) {
    const 前 = 累计;
    累计 += 天气概率[候选];
    if (候选 === 天气) { 骰值 = (前 + 累计) / 2; break; }
  }
  状态.天气剩余天数 = 1;
  let 第一掷 = true;
  推进天气段(状态, () => {
    if (第一掷) { 第一掷 = false; return 骰值; }
    return Math.random();
  });
  记日志(`⚠ 测试强制：${状态.当前天气} · 本段随机 ${状态.天气剩余天数} 天（真实概率 ${(天气概率[天气] * 100).toFixed(0)}% · 正常一段 ${天气段长[天气][0]}~${天气段长[天气][1]} 天）`, '说明');
  刷新();
}

function 建天气面板(): void {
  天气面板.textContent = '';
  for (const 天 of Object.keys(天气概率) as 天气名[]) {
    const [小, 大] = 天气段长[天];
    const 是当前 = 状态.当前天气 === 天;
    const 钮位 = document.createElement('button');
    钮位.className = 是当前 ? '天气当前' : '天气项';
    钮位.textContent = `${是当前 ? '● ' : ''}${天} ${Math.round(天气概率[天] * 100)}%·${小}~${大}天`;
    钮位.onclick = () => {
      强制天气(天);
      建天气面板();                              // 重画一遍，让「● 当前天气」跟过去
    };
    天气面板.appendChild(钮位);
  }
  const 掷钮 = document.createElement('button');
  掷钮.className = '天气掷';
  掷钮.textContent = '🎲 随机换下一段（走真实跨日逻辑）';
  掷钮.onclick = () => {
    if (状态.今天已结算) {
      记日志('今天已经跨过日了 —— 先走一格或按「开始下一天」进入新的一天，再按这个键才会掷新天气', '说明');
      return;
    }
    状态.天气剩余天数 = 1;               // 交给真实的 结算.跨日() 去重掷天气与段长
    报('🎲 随机换下一段天气', 结束当天(状态));
  };
  天气面板.appendChild(掷钮);
}

记日志('方向键 / WASD 走一格 · 空格 开始下一天 · R 重开 · 点地图 = 相邻真走 / 远处直达', '说明');
记日志('右边 12 个天气按钮可以强制切天气；标着「2%·3~6天」= 出现概率和这段持续天数（5A §2.1/§2.2）', '说明');
刷新();
建天气面板();
