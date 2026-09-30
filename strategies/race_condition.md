---
name: race-condition
description: 竞争条件利用策略（含并发攻击、GIL 绕过、时间窗口调整）
triggers:
  vuln_class: [race]
---

## 竞争条件复现策略

### 应用层竞争条件（Web / API / 多线程服务）

#### 并发请求工具

竞争条件需要精确的时间窗口。使用多进程并发替代多线程（绕过 GIL）：

```bash
# 批量并发发送请求
for i in $(seq 1 20); do
    (curl -s "http://target/vulnerable?param=$i" > /tmp/race_$i.log &)
done
wait
# 检查是否有成功触发的响应
grep -l "sensitive_data" /tmp/race_*.log
```

#### 逐步调整参数

从低并发开始，逐步增加，找到触发窗口：

```
并发数: 5 → 10 → 20 → 50 → 100
请求间隔: 0ms → 1ms → 5ms → 10ms
时间同步: 预热连接 → 同时发送
```

#### GIL 绕过（Ruby / Python 等解释型语言）

Ruby 和 CPython 的 GIL 阻止真正的并行线程执行。
纯多线程无法触发竞争条件，应使用**多进程**：

```bash
# ✅ 多进程（绕过 GIL）
for i in $(seq 1 10); do
    (curl -s http://target/vulnerable &)
done

# ❌ 单线程发包——在 GIL 保护的语言中几乎不可能触发
python3 << 'EOF'
import requests
for i in range(10):
    requests.get("http://target/vulnerable")
EOF
```

#### 时间窗口校准

如果首次尝试未触发，逐步调整参数再试：

1. 增加并发数（10 → 50 → 200）
2. 微调请求间延迟
3. 先发预热请求建立连接，再同时发送碰撞请求

### 内核层竞争条件

内核 race（packet_socket / timerfd / data race）参考以下技术文档：

```bash
cat /home/researcher/ExpPilot/exppilot/exploit_techniques/packet_socket.md
cat /home/researcher/ExpPilot/exppilot/exploit_techniques/timerfd.md
```

适用场景：

| 原语 | 适用 CVE 特征 | 参考文档 |
|------|-------------|---------|
| packet_socket | 网络协议栈 race、并发 socket 操作 | `cat .../packet_socket.md` |
| timerfd | 定时器 race、竞争性释放 | `cat .../timerfd.md` |

### 结果判定

竞争条件的触发是概率性的。多次重试仍无法触发时：

- `verification_method = "code_analysis"` — 标记为代码分析
- `summary` 中说明已确认漏洞代码路径，但运行时无法稳定触发
