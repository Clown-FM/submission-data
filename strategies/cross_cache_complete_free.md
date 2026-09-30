---
name: cross-cache-complete-free
description: 跨 cache Complete Free — 适用条件判断与使用指引
triggers:
  vuln_class: [uaf, double_free]
  kernel: true
  target_level: [local_privilege_escalation]
---

## 适用条件

此技术在**全部满足**以下条件时适用：

1. ✅ 漏洞在 **nf_tables 子系统**（fix commit 路径含 `net/netfilter/nf_tables`）
2. ✅ 目标内核 **≥ 5.14**（存在 `kmalloc-cg-*` 拆分）
3. ✅ **SLAB_FREELIST_HARDENED=y**（probe 确认）
4. ✅ 漏洞对象和 spray 原语在不同 kmalloc cache 族

**任一条件不满足 → 换用替代方案**（见下方）。

## 实现文档

条件满足时，读取完整实现：

```bash
cat /home/researcher/ExpPilot/exppilot/exploit_techniques/cross_cache.md
```

辅助库：框架已将 `cc_helper.h` 部署到 VM 的 `/tmp/cc_helper.h`。

## cc_helper.h 兼容性

`cc_helper.h` 依赖 **libnl-3**（`struct nl_sock`）。写 exploit.c 前检查：

```bash
pkg-config --libs libnl-3 libnl-nf-3 2>/dev/null && echo "libnl3 OK"
```

- ✅ libnl-3 可用 → `#include "/tmp/cc_helper.h"`
      然后提供 `create_table()` / `del_table()` / `create_ct_expect_obj()` 三个适配函数
- ❌ 只有 libmnl → cc_helper.h 不兼容
      参考 cross_cache.md 手写 spray，或尝试 expkit complete-free（通用工具）

## 不满足条件时的替代方案

| 条件不满足 | 替代技术 | 参考文档 |
|-----------|---------|---------|
| 非 nf_tables 子系统 | msg_msg / skb / user_key_payload spray | `cat .../exploit_techniques/msg_msg.md` |
| < 5.14（无 cg 拆分）| same-cache spray，不需要跨族 | `cat .../exploit_techniques/msg_msg.md` |
| SLAB_HARDENED=n | 普通 spray，不需要 complete free | `cat .../exploit_techniques/msg_msg.md` |
| libnl-3 不可装 | 手写 spray 或 expkit complete-free（不依赖 libnl-3） | `cat .../exploit_techniques/cross_cache.md` |
