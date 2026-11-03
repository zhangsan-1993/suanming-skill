#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻自动起卦脚本（铜钱摇卦模拟）
运行方式：python qigua.py
可选参数：python qigua.py --question "我想测什么"
"""

import random
import argparse
import json
import sys
from datetime import datetime

# ===== 六十四卦对照表 =====
# 上卦（外卦）x 下卦（内卦） → 卦名
# 卦序：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
GUA_NAMES = {
    (1,1):"乾为天", (1,2):"天泽履", (1,3):"天火同人", (1,4):"天雷无妄",
    (1,5):"天风姤",  (1,6):"天水讼", (1,7):"天山遁",  (1,8):"天地否",
    (2,1):"泽天夬", (2,2):"兑为泽", (2,3):"泽火革",  (2,4):"泽雷随",
    (2,5):"泽风大过",(2,6):"泽水困",(2,7):"泽山咸",  (2,8):"泽地萃",
    (3,1):"火天大有",(3,2):"火泽睽",(3,3):"离为火",  (3,4):"火雷噬嗑",
    (3,5):"火风鼎", (3,6):"火水未济",(3,7):"火山旅", (3,8):"火地晋",
    (4,1):"雷天大壮",(4,2):"雷泽归妹",(4,3):"雷火丰",(4,4):"震为雷",
    (4,5):"雷风恒", (4,6):"雷水解",  (4,7):"雷山小过",(4,8):"雷地豫",
    (5,1):"风天小畜",(5,2):"风泽中孚",(5,3):"风火家人",(5,4):"风雷益",
    (5,5):"巽为风", (5,6):"风水涣",  (5,7):"风山渐",  (5,8):"风地观",
    (6,1):"水天需", (6,2):"水泽节",  (6,3):"水火既济",(6,4):"水雷屯",
    (6,5):"水风井", (6,6):"坎为水",  (6,7):"水山蹇",  (6,8):"水地比",
    (7,1):"山天大畜",(7,2):"山泽损", (7,3):"山火贲",  (7,4):"山雷颐",
    (7,5):"山风蛊", (7,6):"山水蒙",  (7,7):"艮为山",  (7,8):"山地剥",
    (8,1):"地天泰", (8,2):"地泽临",  (8,3):"地火明夷",(8,4):"地雷复",
    (8,5):"地风升", (8,6):"地水师",  (8,7):"地山谦",  (8,8):"坤为地",
}

# 单卦二进制（0=阴 1=阳）→ 卦宫编号
# 乾111=1 兑110=2 离101=3 震100=4 巽011=5 坎010=6 艮001=7 坤000=8
def trigram_to_num(lines):
    """lines: [爻1, 爻2, 爻3]，爻值：0阴 1阳，爻1在下"""
    binary = lines[2]*4 + lines[1]*2 + lines[0]*1
    mapping = {7:1, 6:2, 5:3, 4:4, 3:5, 2:6, 1:7, 0:8}
    return mapping[binary]

def yao_to_symbol(yao_val):
    """yao_val: 6/7/8/9 → 符号字符串"""
    symbols = {6:"X— —（老阴，动爻→变阳）", 7:"————（少阳，静爻）",
               8:"— —（少阴，静爻）",  9:"Y————（老阳，动爻→变阴）"}
    return symbols[yao_val]

def yao_to_yin_yang(yao_val):
    """返回本爻阴阳"""
    return 1 if yao_val in (7, 9) else 0  # 1=阳 0=阴

def yao_changed(yao_val):
    """返回变爻后的阴阳"""
    if yao_val == 9: return 0   # 老阳变阴
    if yao_val == 6: return 1   # 老阴变阳
    return yao_to_yin_yang(yao_val)

def shake_one_yao():
    """模拟三枚铜钱，返回爻值 6/7/8/9"""
    coins = [random.choice([2, 3]) for _ in range(3)]  # 字=2 花=3
    total = sum(coins)
    return total  # 6=老阴 7=少阳 8=少阴 9=老阳

def get_gua_name(lines_yin_yang):
    """lines_yin_yang: 6个元素，[爻1,...,爻6]"""
    lower = trigram_to_num(lines_yin_yang[0:3])
    upper = trigram_to_num(lines_yin_yang[3:6])
    return GUA_NAMES.get((upper, lower), "未知卦")

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    parser = argparse.ArgumentParser(description="六爻铜钱起卦")
    parser.add_argument("--question", "-q", type=str, default="", help="所测之事")
    args = parser.parse_args()

    now = datetime.now()
    print("=" * 50)
    print(f"  六爻铜钱起卦")
    print(f"  起卦时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    if args.question:
        print(f"  所测之事：{args.question}")
    print("=" * 50)

    # 摇出六爻（从第一爻到第六爻）
    yaos = [shake_one_yao() for _ in range(6)]

    # 本卦爻的阴阳
    ben_lines = [yao_to_yin_yang(y) for y in yaos]
    # 变卦爻的阴阳（动爻变化）
    bian_lines = [yao_changed(y) for y in yaos]

    # 获取卦名
    ben_gua_name = get_gua_name(ben_lines)
    bian_gua_name = get_gua_name(bian_lines)

    # 是否有动爻
    dong_yaos = [i+1 for i, y in enumerate(yaos) if y in (6, 9)]

    print(f"\n【本卦】{ben_gua_name}")
    print(f"【变卦】{bian_gua_name}" if dong_yaos else "【无动爻，本卦即终卦】")
    print(f"【动爻】{'、'.join([f'第{i}爻' for i in dong_yaos])}" if dong_yaos else "【动爻】无")
    print()
    print("  爻位  │  爻象")
    print("  ──────┼────────────────────────────────")
    for i in range(5, -1, -1):  # 从第六爻到第一爻展示
        label = f"  第{i+1}爻  │  "
        print(label + yao_to_symbol(yaos[i]))
    print()
    print("（注：Y=老阳动爻将变阴，X=老阴动爻将变阳）")
    print()
    print("起卦完成，请根据以上卦象进行解读。")
    print("=" * 50)

    # JSON输出
    result = {
        'time': now.isoformat(),
        'question': args.question,
        'ben_gua': ben_gua_name,
        'bian_gua': bian_gua_name,
        'dong_yaos': dong_yaos,
        'yaos': yaos,
        'ben_lines': ben_lines,
        'bian_lines': bian_lines
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
