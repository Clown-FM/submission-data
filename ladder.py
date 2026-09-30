#!/usr/bin/env python3
"""
深度阶梯打分。

论文 §3.3 的四级阶梯，按每次运行的 **最后影响类型**（`actual_type`）
判定档位。判定与运行是否成功无关：一个被指派为代码执行的运行，
无论最终是否成功，都记在 Level 2。这与论文"Depth is recorded for
every run, reproduced or not"一致，但读的时候要注意：档位来自
**指派的影响类型**，不是运行实际达到的深度。

用法：
    python3 ladder.py                # 打印各集合的阶梯分布
    python3 ladder.py user-space     # 只打印某一个集合

论文报告的数字（可用于核对）：
    user-space   L0=249  L1=279  L2=103  不入档=209   合计=840
    kernel       L0=14   L1=3    L2=57   不入档=4     合计=78
"""
import json
import glob
import os
import sys
from collections import Counter

# 影响类型 -> 阶梯档位。未列出的类型不入档。
LEVEL_OF = {
    # Level 2：代码执行
    'remote_code_execution': 'L2',
    'local_privilege_escalation': 'L2',
    # Level 1：确认的信息泄露
    'remote_information_disclosure': 'L1',
    'local_information_disclosure': 'L1',
    'offline_data_recovery': 'L1',
    # Level 0：触发（崩溃 / 挂起），或只到浏览器端的执行
    'remote_denial_of_service': 'L0',
    'local_denial_of_service': 'L0',
    'xss': 'L0',
    'reflected_xss': 'L0',
    'remote_xss': 'L0',
}
NOT_PLACED = 'not_placed'

PAPER = {
    'user-space': {'L0': 249, 'L1': 279, 'L2': 103, NOT_PLACED: 209},
    'kernel':     {'L0': 14,  'L1': 3,   'L2': 57,  NOT_PLACED: 4},
}


def score(collection):
    """返回该集合的档位计数。"""
    counts = Counter()
    for path in glob.glob(os.path.join(collection, '*', '_result.json')):
        with open(path, encoding='utf-8') as f:
            record = json.load(f)
        counts[LEVEL_OF.get(record.get('actual_type'), NOT_PLACED)] += 1
    return counts


def main():
    root = os.path.dirname(os.path.abspath(__file__))
    names = sys.argv[1:] or ['user-space', 'kernel', 'remote', 'other']

    for name in names:
        collection = os.path.join(root, name)
        if not os.path.isdir(collection):
            print(f'{name}: 目录不存在')
            continue
        counts = score(collection)
        total = sum(counts.values())
        line = (f'{name:12s} L0={counts["L0"]:4d}  L1={counts["L1"]:4d}  '
                f'L2={counts["L2"]:4d}  not_placed={counts[NOT_PLACED]:4d}  '
                f'total={total:4d}')

        if name in PAPER:
            expected = PAPER[name]
            ok = all(counts[k] == v for k, v in expected.items())
            line += '   [matches paper]' if ok else '   [DOES NOT MATCH PAPER]'
        print(line)


if __name__ == '__main__':
    main()
