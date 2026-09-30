---
name: local-dos
description: 本地拒绝服务利用策略
triggers:
  target_level: [local_denial_of_service]
---
## 🔴 本地拒绝服务利用策略（自动注入）

本地 Denial of service 分为两类：

| 类型 | 特征 | 示例 |
|------|------|------|
| **消费型** | 耗尽 CPU/内存 → 拒绝服务 | fork 炸弹、内存泄漏 |
| **崩溃型** | 触发内核/进程 Oops → 拒绝服务 | 空指针解引用、panic |

### 消费型 DoS 验证

1. 记录基线：`docker_stats(name=container)` 记录 CPU/内存
2. 触发压力：批量启动子进程/线程，消耗系统资源
3. 攻击后对比：如果 CPU 或内存达到上限则判定为 DoS

### 崩溃型 DoS 验证

1. 运行 exp.sh 触发崩溃
2. 确认进程退出且无法被正常唤醒
3. 或 dmesg 中存在 kernel panic/oops 日志
