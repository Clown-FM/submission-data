---
name: remote-dos
description: 远程拒绝服务利用策略（含子类型识别、环境评估、攻击参数选择）
triggers:
  target_level: [remote_denial_of_service]
---

## 🔴 远程拒绝服务利用策略

### 步骤 1: 判断 DoS 子类型

分析 CVE 描述和 fix commit，确认属于哪个子类型。**子类型决定后续所有策略选择。**

| 子类型 | CVE 描述关键词 | 攻击方式 | 需要持续负载? |
|--------|--------------|---------|-------------|
| **进程崩溃型** (crash) | crash, NULL pointer, segfault, panic, assertion, abort | 单次请求触发崩溃 | 不需要 |
| **ReDoS** | regular expression, ReDoS, backtracking, catastrophic | 单条 payload 触发 CPU 100% | 不需要 |
| **CPU 耗尽型** (数据库 LIKE) | LIKE, query, search, "%...%", full table scan | 高并发 LIKE 查询 | **需要** |
| **连接耗尽型** | connection pool, worker, thread, file descriptor, prefork | 占满 worker/连接池 | **需要** |
| **内存泄漏型** | memory leak, OOM, allocation, never freed | 持续触发内存分配 | 可能需要 |

**识别方法：**
- 读 CVE description 中的关键词
- 读 fix commit 的 diff：如果是加长度校验 → 连接耗尽 / CPU 耗尽；如果是修正则 → ReDoS；如果是修空指针 → crash

### 步骤 2: 选择验证模式

根据子类型选择 verify.sh 的骨架：

```
进程崩溃型 → 顺序模式（顺序 skeleton，攻击→检查崩溃）
ReDoS       → 并发模式（concurrent_skeleton，攻击后台& + 探测）
CPU 耗尽型  → 并发模式（concurrent_skeleton，需要持续负载）
连接耗尽型  → 并发模式（concurrent_skeleton，需要持续负载）
内存泄漏型  → 并发模式（concurrent_skeleton，需要持续负载）
```

### 步骤 3: 环境评估（仅持续负载型 DoS）

如果子类型**需要持续负载**，在写 exp.sh 前先评估环境容量：

```bash
# Apache worker 数（决定并发上限）
grep -i maxrequestworkers /etc/apache2/*.conf 2>/dev/null || echo "default=150"

# MySQL 连接上限
mysql -N -B -e "SHOW VARIABLES LIKE 'max_connections'" 2>/dev/null || echo "default=150"

# 数据库数据量（LIKE 查询型必须）
mysql -N -B -e "SELECT COUNT(*) FROM <表名>" 2>/dev/null || echo "unknown"

# 基线延迟
START=$(date +%s%N)
curl -o /dev/null -s -w "%{http_code}" http://127.0.0.1/
BASELINE_MS=$(( ($(date +%s%N) - START) / 1000000 ))
```

**攻击并发数选择：**
- 并发数 = min(Apache workers × 1.5, MySQL max_connections × 0.8, 300)
- 不熟悉环境默认用 100-200 并发
- 如果首次攻击无效果，翻倍并发再试

### 步骤 4: 数据注入（仅数据库查询型 DoS）

LIKE `%...%` 在空表上即时返回，无法造成 DoS。

```bash
ROW_COUNT=$(mysql -N -B <DB名> -e "SELECT COUNT(*) FROM <表>" 2>/dev/null || echo "0")
if [ "$ROW_COUNT" -lt 1000 ]; then
    echo "  数据量不足 ($ROW_COUNT 行)，注入 10000 行 seed data..."
    mysql <DB名> -e "
        INSERT INTO <表>(title, content, ...)
        SELECT CONCAT('seed_', n), REPEAT('x', 500), ...
        FROM (SELECT (a.a + b.a*10 + c.a*100 + d.a*1000) AS n
              FROM (SELECT 0 AS a UNION SELECT 1 UNION SELECT 2 UNION SELECT 3
                    UNION SELECT 4 UNION SELECT 5 UNION SELECT 6
                    UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a
              CROSS JOIN ...) nums
        LIMIT 10000;
    "
fi
```

写在 exp.sh 中，攻击之前。

### 步骤 5: 编写 attacker.py（仅持续负载型）

基于框架模板（`dos_attacker_template.py`）适配。关键参数：

```bash
# attacker.py 调用示例
python3 /tmp/attacker.py \
    --url="http://127.0.0.1/index.php?route=/forum/search&s=" \
    --concurrent=200 \
    --mode=mixed \
    --duration=30 \
    --report=/tmp/dos_result.json
```

**集成方式（重要）：attacker.py 由 exp.sh 调用，不是 verify.sh 直接调：**

```bash
# exp.sh 中（正确）
python3 /tmp/attacker.py --url=http://target/ --duration=30 &
ATK_PID=$!
wait $ATK_PID
echo "EXP 完成"
```

```bash
# verify.sh 中（正确 — concurrent_skeleton 自动处理）
bash /tmp/exp.sh &     ← 只调 exp.sh，attacker.py 在 exp.sh 内部启动
# 探测线程并发监视 ...
```

### 步骤 6: 超时处理

如果 verify.sh 因攻击耗时太长而超时：

- ✅ **增大 docker_run timeout** — Agent 可以传 timeout=300
- ✅ **attacker.py 已在后台 &** — 探测线程独立运行
- ❌ **不要删掉 attacker.py 来缩短时间**
- ❌ **不要降低并发数来加速**

### 步骤 7: 效果判定（仅持续负载型）

ReDoS/CPU 耗尽/连接耗尽/内存泄漏型 DoS 的**服务进程不死亡**。不可用判定按验收标准（见 cve_remote_denial_of_service.yaml acceptance 矩阵）：

```
探测期间:
  - HTTP 000 或 connection refused → DoS 成功 ✅
  - 延迟 p99 > 基线 × 5 倍       → DoS 成功 ✅
  - 超时/错误率 ≥ 30%           → DoS 成功 ✅（ReDoS 需 ≥ 50%，按验收标准）
  - 以上都达不到                 → 提高并发再试一次，仍达不到则标记"环境限制" ⚠️
```

验收标准对不同子类型有更严格的阈值（如 ReDoS 要求 > 50%），
以验收标准为准。以上是实际操作中的参考阈值。
