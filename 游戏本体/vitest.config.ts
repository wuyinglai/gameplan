import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts'],

    // ==========================================================================
    // 🔴 2026-10-19 WorkBuddy 修：在这台机器上并行跑会撞上系统临时目录的
    //    EPERM 权限错误（Temp\...\ssr\...），vitest 会当场中断，
    //    🔴 结果只跑完第一个测试文件就报"全部通过" —— **这就是假绿**。
    //    （2026-10-19 实测：地图 27 条 + 主循环 13 条 = 40 条，一起跑只出 27 条）
    //
    // 🔴 singleThread / isolate:false 让测试在同一个进程里顺序跑，
    //    不再需要写临时文件 —— 既避开 EPERM，也让"跑了几条"这个问题变得可见。
    // ==========================================================================
    pool: 'threads',
    poolOptions: {
      threads: {
        singleThread: true,
      },
    },
    isolate: false,

    // 🔴 跑完必须能看到「一共跑了几个文件 / 几条」—— 少跑了要看得见
    reporter: 'verbose',
  },
});