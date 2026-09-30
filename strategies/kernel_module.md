---
name: kernel-module
description: 内核模块 CVE 通用模板策略
triggers:
  vuln_class: [uaf, double_free, oob, overflow, race]
  kernel: true
---
## 🔴 内核模块 CVE 通用模板策略（自动注入）

此 CVE 需要编译/加载内核模块（.ko）。请使用以下模板结构编写脚本，
不要自由发挥。模板中的基础设施部分已处理常见陷阱，不要修改。

### 脚本结构

```
exp.sh → insmod module.ko → trigger → verify
```

### 模板

```bash
#!/bin/sh
set -e

# 编译内核模块
cd /tmp
cat > module.c << 'EOF'
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init module_init(void)
{
    printk(KERN_INFO "module loaded\n");
    return 0;
}

static void __exit module_exit(void)
{
    printk(KERN_INFO "module unloaded\n");
}

module_init(module_init);
module_exit(module_exit);
MODULE_LICENSE("GPL");
EOF

make -C /lib/modules/$(uname -r)/build M=/tmp modules

# 加载模块
insmod /tmp/module.ko

# 触发漏洞（按 CVE 具体要求）
# ...

# 验证
lsmod | grep module
```

### 注意事项

1. 编译需要 kernel-headers：`apt-get install linux-headers-$(uname -r)`
2. 部分内核需要 CONFIG_MODVERSIONS，注意模块接口兼容性
3. 加载模块需要 root 权限
4. 模块卸载：`rmmod module_name`
