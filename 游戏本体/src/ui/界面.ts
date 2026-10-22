// ============================================================================
// 人工测试台（浏览器 UI）· 第 1 段：状态与画布
//
// 🔴 本文件只做三件事：读状态 → 画到 canvas → 把按钮点击转成对已有函数的调用。
//    页面里没有任何游戏规则（不扣体力、不算时间、不判通行）—— 全部调 src/p1、
//    src/p2 里已经写好并测过的函数。规则若出错，责任在被调的模块，不在这里。
// 跑法：npm run ui（= npx vite），浏览器开 http://localhost:5173
// ============================================================================

import { 加载地图, 查格 } from '../p1/地图';
import { 新建游戏状态 } from '../p1/状态';
import { 走一格 } from '../p1/移动';
import { 结束当天 } from '../p1/结束当天';
import { 每格消耗 } from '../p1/消耗';
import { 每格加成 } from '../p1/天气';
import { 坐标键, 地点类 } from '../p1/类型';
import { 侦察, 采集, 搜索, 补给, 修车, 治疗, 交易 } from '../p1/接口位';
import { 新建商队, 描述资源 } from '../p2/资源';
import type { 格子类型, 游戏状态, 操作结果 } from '../p1/类型';
import { 描述 } from '../p1/入口';
import 原始地图 from '../p1/地图.json';

type 原始项 = { t: string; x: number; y: number; r?: number };

const 地图 = 加载地图();
let 状态: 游戏状态 = 新建游戏状态(地图);
const 商队 = 新建商队();          // P2 第 1 步：只有字段，全 0

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

  // 商队本体（正中心）
  const [我x, 我y] = 屏幕(中心x, 中心y);
  主画笔.fillStyle = '#ffffff';
  主画笔.beginPath();
  主画笔.arc(我x, 我y, Math.max(3, 每格 / 2.6), 0, Math.PI * 2);
  主画笔.fill();
  方框(主画笔, 我x, 我y, '#ffffff', 每格);
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
  const 格 = 查格(地图, x, y);
  状态区.textContent = [
    描述('现在', 状态).trim(),
    `天气 ${状态.当前天气} · 还剩 ${状态.天气剩余天数} 天 · 天气每格加成 ${每格加成(状态.当前天气)}`
      + '（§6.1 未裁定 → 恒 0）',
    `脚下这一格要走 ${每格消耗(状态, 格.路况)} 点体力`
      + `（基准 15＋天气 ${每格加成(状态.当前天气)}＋路况 r=${格.路况} 档加成未裁定）`,
    `脚下 (${x}, ${y}) ${格.类型}${格.地点名 === null ? '' : ' · ' + 格.地点名}`
      + ` · 路况 r=${格.路况} · 可通行 ${格.可通行} · 已到访 ${格.已到访}`,
    `是地点吗：${地点类.has(格.类型) ? '是 —— 踩上去 = 进界面（P2 第 3 步才有内容）' : '否'}`,
    `今天已结算：${状态.今天已结算}（幂等标记 · 判据 24 / 26）`,
    描述资源('商队资源', 商队).trim() + '　←︎ P2 第 1 步只有字段，第 2 步起才会增减',
  ].join('\n');
  画主视野();
  画小地图();
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
  if (果.成功) {
    记日志(`${动作} → ✅ ${果.已抵达 === true ? '已抵达（地点类格子）· ' : ''}${描述('现在', 状态).trim()}`, '成功');
  } else {
    记日志(`${动作} → ❌ 拒绝：${果.原因}（按判据状态不该变，请看上面数字）`, '拒绝');
  }
  刷新();
}

function 走(dx: number, dy: number, 动作: string): void {
  报(动作, 走一格(状态, 状态.当前坐标.x + dx, 状态.当前坐标.y + dy));
}

function 重开(): void {
  状态 = 新建游戏状态(地图);
  记日志('—— 重开：新建游戏状态()，回起点、第 1 天 07:00、体力 100 ——', '说明');
  刷新();
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
  ' ': () => 报('结束当天（空格）', 结束当天(状态)),
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
记日志('方向键 / WASD 走一格 · Space 结束当天 · R 重开 · 三个「测试」按钮专门打边界判据 2/3/4/18', '说明');
刷新();
