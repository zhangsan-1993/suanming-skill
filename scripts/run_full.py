#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整推演执行脚本（演示用，勿在生产调用）
"""

from divination_engine import DivinationEngine
import json


def main():
    # 蒋诗言：2000年9月9日 12点 女 浙江临海（经度121.2）
    engine = DivinationEngine()
    result = engine.full_process(2000, 9, 9, 12, '女', 121.2)

    print('SUCCESS' if result['success'] else 'FAILED')
    if result['success']:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
