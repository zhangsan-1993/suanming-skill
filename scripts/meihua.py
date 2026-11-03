#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梅花易数起卦工具 v1.0

典籍依据（SKILL.md「四、梅花易数 — 典籍规则表」）：
- 《梅花易数·时间占》  年月日÷8 余数为上卦，年月日时÷8 余数为下卦，
                        年月日时÷6 余数为动爻
- 《梅花易数·数占法》  两数：前数÷8 为上卦，后数÷8 为下卦，两数和÷6 为动爻
- 《梅花易数·观物占》  所见物象取先天八卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8
- 《梅花易数·体用章》  无动爻之卦为体（本身），有动爻之卦为用（事物）；
                        体克用=吉，用克体=凶，体生用=泄气，用生体=大吉
- 《梅花易数·八卦万物类象》 乾为天/君/父/金；坤为地/母/土；震为雷/动/木；
                        巽为风/入/木；坎为水/险；离为火/丽/电；艮为山/止/土；
                        兑为泽/悦/金
- 《梅花易数·互变章》  本卦二三四爻为下互，三四五爻为上互；动爻变化爻为变卦；
                        综卦=上下颠倒，错卦=阴阳全变
- 《周易·说卦传》      万物类象之扩展

说明：八卦数取先天数（乾1…坤8）；余数为 0 时，卦取 8（坤）、爻取 6（上爻）。
"""

import json
import sys
from typing import Dict, List, Tuple

# 复用六爻模块中已验证的八卦与六十四卦名基础
from liuyao import TRIGRAM, TRIGRAM_BY_LINES, GUA64

# 先天八卦数
XIANTIAN = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']

# 八卦五行
GUA_WUXING = {
    '乾': '金', '兑': '金', '离': '火', '震': '木',
    '巽': '木', '坎': '水', '艮': '土', '坤': '土',
}

# 八卦万物类象（《梅花易数·八卦万物类象》+《周易·说卦传》）
WAN_WU_LEI_XIANG = {
    '乾': ['天', '君', '父', '金', '玉', '圆', '马', '首', '西北', '刚健', '果决'],
    '坤': ['地', '母', '土', '布', '釜', '牛', '腹', '西南', '柔顺', '承载', '众'],
    '震': ['雷', '动', '木', '龙', '足', '长男', '东方', '奋起', '决躁', '震动'],
    '巽': ['风', '入', '木', '鸡', '股', '长女', '东南', '进退', '顺入', '号令'],
    '坎': ['水', '险', '陷', '豕', '耳', '中男', '北方', '隐伏', '忧患', '沟渎'],
    '离': ['火', '丽', '电', '日', '雉', '目', '中女', '南方', '文明', '光明'],
    '艮': ['山', '止', '土', '狗', '手', '少男', '东北', '静止', '阻碍', '门阙'],
    '兑': ['泽', '悦', '金', '羊', '口', '少女', '西方', '口舌', '毁折', '喜悦'],
}

# 五行生克
WUXING_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WUXING_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

YAO_NAMES = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']


# ==================== 历法 ====================

def _lunar(year: int, month: int, day: int):
    """公历 -> 农历 (年, 月, 日)"""
    from lunardate import LunarDate
    try:
        ld = LunarDate.from_solar_date(year, month, day)
    except AttributeError:
        ld = LunarDate.fromSolarDate(year, month, day)
    return ld.year, ld.month, ld.day


def hour_to_shichen(hour: int) -> int:
    """时辰序号：子=1 … 亥=12"""
    return (int((hour + 1) / 2) % 12) + 1


# ==================== 起卦 ====================

def _num_to_gua(n: int) -> str:
    """数 -> 卦（先天数，余 0 取 8）"""
    r = n % 8
    if r == 0:
        r = 8
    return XIANTIAN[r - 1]


def _num_to_yao(n: int) -> int:
    """数 -> 动爻（1-6，余 0 取 6）"""
    r = n % 6
    return r if r != 0 else 6


def time_qigua(year: int, month: int, day: int, hour: int) -> Dict:
    """
    时间起卦《梅花易数·时间占》
    年月日÷8 为上卦，年月日时÷8 为下卦，年月日时÷6 为动爻。
    年月日取农历，时取时辰序号（子1…亥12）。
    """
    ly, lm, ld = _lunar(year, month, day)
    shi = hour_to_shichen(hour)
    year_zhi_num = ((ly - 4) % 12) + 1          # 农历年地支序号 1-12

    n1 = year_zhi_num + lm + ld
    n2 = year_zhi_num + lm + ld + shi

    up = _num_to_gua(n1)
    down = _num_to_gua(n2)
    moving = _num_to_yao(n2)

    return {'up': up, 'down': down, 'moving': moving,
            'lunar': (ly, lm, ld), 'shichen': shi,
            'detail': f'上卦({year_zhi_num}+{lm}+{ld})={n1}→{up}；'
                      f'下卦({year_zhi_num}+{lm}+{ld}+{shi})={n2}→{down}；'
                      f'动爻={n2}%{6}→{moving}'}


def number_qigua(n1: int, n2: int) -> Dict:
    """
    数字起卦《梅花易数·数占法》
    前数÷8 为上卦，后数÷8 为下卦，两数和÷6 为动爻。
    """
    up = _num_to_gua(n1)
    down = _num_to_gua(n2)
    moving = _num_to_yao(n1 + n2)
    return {'up': up, 'down': down, 'moving': moving,
            'detail': f'上卦={n1}%{8}→{up}；下卦={n2}%{8}→{down}；'
                      f'动爻=({n1}+{n2})%{6}→{moving}'}


def object_qigua(nums: List[int]) -> Dict:
    """
    物象起卦《梅花易数·观物占》
    所见物象取先天八卦数（乾1…坤8），两数成卦，和为动爻。
    """
    if len(nums) < 2:
        raise ValueError('物象起卦至少需要两个数')
    up = _num_to_gua(nums[0])
    down = _num_to_gua(nums[1])
    moving = _num_to_yao(sum(nums))
    return {'up': up, 'down': down, 'moving': moving,
            'detail': f'上卦={nums[0]}→{up}；下卦={nums[1]}→{down}；'
                      f'动爻={sum(nums)}%{6}→{moving}'}


# ==================== 卦象推演 ====================

def build_gua(up: str, down: str, moving: int) -> Dict:
    """由上下卦与动爻组装完整卦象：六爻、卦名、体用、互卦、变卦、综卦、错卦"""
    bits = list(TRIGRAM[down]) + list(TRIGRAM[up])      # 初→上：下卦三爻 + 上卦三爻

    info = GUA64.get((up, down))
    name = info['name'] if info else f'{up}{down}之卦'

    # 体用：动爻在下卦(1-3)则下卦为用、上卦为体；动爻在上卦(4-6)则反之
    if moving <= 3:
        yong, ti = down, up
    else:
        yong, ti = up, down

    # 变卦：动爻阴阳互变
    changed = bits[:]
    changed[moving - 1] = 1 - changed[moving - 1]
    bian_down = TRIGRAM_BY_LINES[tuple(changed[0:3])]
    bian_up = TRIGRAM_BY_LINES[tuple(changed[3:6])]
    bian_info = GUA64.get((bian_up, bian_down))
    bian_name = bian_info['name'] if bian_info else f'{bian_up}{bian_down}之卦'

    # 互卦：二三四爻为下互，三四五爻为上互（索引 1-3 / 2-4）
    hu_down = TRIGRAM_BY_LINES[tuple(bits[1:4])]
    hu_up = TRIGRAM_BY_LINES[tuple(bits[2:5])]
    hu_info = GUA64.get((hu_up, hu_down))
    hu_name = hu_info['name'] if hu_info else f'{hu_up}{hu_down}之卦'

    # 综卦（上下颠倒）、错卦（阴阳全变）
    zong_info = GUA64.get((down, up))
    zong_name = zong_info['name'] if zong_info else f'{down}{up}之卦'
    cuo_bits = [1 - b for b in bits]
    cuo_up = TRIGRAM_BY_LINES[tuple(cuo_bits[3:6])]
    cuo_down = TRIGRAM_BY_LINES[tuple(cuo_bits[0:3])]
    cuo_info = GUA64.get((cuo_up, cuo_down))
    cuo_name = cuo_info['name'] if cuo_info else f'{cuo_up}{cuo_down}之卦'

    return {
        'name': name, 'up': up, 'down': down, 'moving': moving,
        'bits': bits, 'ti': ti, 'yong': yong,
        'ti_wuxing': GUA_WUXING[ti], 'yong_wuxing': GUA_WUXING[yong],
        'bian_name': bian_name, 'bian_up': bian_up, 'bian_down': bian_down,
        'hu_name': hu_name, 'hu_up': hu_up, 'hu_down': hu_down,
        'zong_name': zong_name, 'cuo_name': cuo_name,
    }


def judge(gua: Dict) -> Dict:
    """
    体用生克吉凶判断《梅花易数·体用章》
    体克用=吉，用克体=凶，体生用=泄气，用生体=大吉，比和=相助之吉
    """
    ti, yong = gua['ti_wuxing'], gua['yong_wuxing']

    if ti == yong:
        level, desc = '吉', '体用比和，五行同气，主百事顺遂、有人相助'
    elif WUXING_SHENG.get(yong) == ti:          # 用生体
        level, desc = '大吉', '用生体，主外力相助、事易成，得人或势之助'
    elif WUXING_SHENG.get(ti) == yong:          # 体生用
        level, desc = '泄气', '体生用，主耗损精力财物，事成而身疲，宜量力'
    elif WUXING_KE.get(ti) == yong:             # 体克用
        level, desc = '吉', '体克用，主事可成但费力、须主动争取，进度偏迟'
    else:                                        # 用克体
        level, desc = '凶', '用克体，主受阻受制、事多阻碍，宜守不宜进'

    return {'level': level, 'desc': desc,
            'ti': ti, 'yong': yong,
            'relation': f'体({gua["ti"]}·{ti}) / 用({gua["yong"]}·{yong})'}


# ==================== 输出 ====================

def format_report(q: Dict, gua: Dict, j: Dict, question: str = None) -> str:
    out = []
    out.append("=" * 58)
    out.append("【梅花易数 · 起卦】")
    out.append("=" * 58)
    out.append(f"  起卦方式：{q['mode']}")
    if 'lunar' in q:
        out.append(f"  农历：{q['lunar'][0]}年{q['lunar'][1]}月{q['lunar'][2]}日"
                   f"　时辰：第{q['shichen']}时")
    out.append(f"  卦数推演：{q['detail']}")
    out.append("")

    out.append("=" * 58)
    out.append(f"【本卦】{gua['name']}（上{gua['up']}下{gua['down']}）")
    out.append("=" * 58)
    sym = {1: '———', 0: '— —'}
    for i in range(5, -1, -1):
        mark = '×' if (i + 1) == gua['moving'] else ' '
        who = '（用）' if ((gua['moving'] <= 3 and i < 3) or
                          (gua['moving'] > 3 and i >= 3)) else '（体）'
        out.append(f"  {YAO_NAMES[i]}：{sym[gua['bits'][i]]}{mark} {who}")
    out.append("")
    out.append(f"  动爻：{YAO_NAMES[gua['moving'] - 1]}")
    out.append(f"  体卦：{gua['ti']}（{gua['ti_wuxing']}）"
               f"　用卦：{gua['yong']}（{gua['yong_wuxing']}）")
    out.append(f"  互卦：{gua['hu_name']}（上{gua['hu_up']}下{gua['hu_down']}）")
    out.append(f"  变卦：{gua['bian_name']}（上{gua['bian_up']}下{gua['bian_down']}）")
    out.append(f"  综卦：{gua['zong_name']}　错卦：{gua['cuo_name']}")
    out.append("")

    out.append("=" * 58)
    out.append("【体用生克】《梅花易数·体用章》")
    out.append("=" * 58)
    out.append(f"  {j['relation']}")
    out.append(f"  吉凶：{j['level']}　{j['desc']}")
    out.append("")

    out.append("【卦象类象】《梅花易数·八卦万物类象》")
    out.append(f"  体卦 {gua['ti']}：{'、'.join(WAN_WU_LEI_XIANG[gua['ti']])}")
    out.append(f"  用卦 {gua['yong']}：{'、'.join(WAN_WU_LEI_XIANG[gua['yong']])}")
    out.append("")
    out.append("【解读要点】")
    out.append("  1. 体卦为问卦者本身，用卦为所问之事/对方")
    out.append("  2. 先看体用五行生克定吉凶（见上）")
    out.append("  3. 互卦示事情中间过程，变卦示最终结局")
    out.append("  4. 结合类象与所问之事取象类比")
    if question:
        out.append("")
        out.append(f"【所问】{question}")
    return "\n".join(out)


# ==================== 主函数 ====================

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("梅花易数起卦工具 v1.0（《梅花易数》先天八卦数）")
        print("用法:")
        print("  时间起卦: python meihua.py time <年> <月> <日> <时> [问题]")
        print("  数字起卦: python meihua.py number <数1> <数2> [问题]")
        print("  物象起卦: python meihua.py object <数1> <数2> [...] [问题]")
        print("示例:")
        print("  python meihua.py time 2026 9 3 10 小米舆情走势")
        print("  python meihua.py number 38 52 某事吉凶")
        print("  python meihua.py object 3 6 见雷见水")
        sys.exit(0)

    if len(sys.argv) < 2:
        print(json.dumps(error_response("MISSING_ARGUMENTS",
                                        "用法: python meihua.py time/number/object [参数]"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    mode = sys.argv[1]

    try:
        if mode == 'time':
            if len(sys.argv) < 6:
                print(json.dumps(error_response("MISSING_ARGUMENTS",
                                                "时间起卦需提供年月日时"),
                                 ensure_ascii=False, indent=2))
                sys.exit(1)
            try:
                y, m, d, h = (int(sys.argv[i]) for i in (2, 3, 4, 5))
            except ValueError as e:
                print(json.dumps(error_response("INVALID_NUMBER",
                                                f"年月日时必须为整数: {e}"),
                                 ensure_ascii=False, indent=2))
                sys.exit(2)
            from p0_validators import _valid_date
            verrs = _valid_date(y, m, d, h)
            if verrs:
                print(json.dumps(error_response("INVALID_INPUT", verrs),
                                 ensure_ascii=False, indent=2))
                sys.exit(2)
            question = ' '.join(sys.argv[6:]) or None
            q = time_qigua(y, m, d, h)
            q['mode'] = f'时间起卦（{y}-{m:02d}-{d:02d} {h:02d}时）'
            q['solar'] = (y, m, d, h)

        elif mode == 'number':
            if len(sys.argv) < 4:
                print(json.dumps(error_response("MISSING_ARGUMENTS",
                                                "数字起卦需提供两个数"),
                                 ensure_ascii=False, indent=2))
                sys.exit(1)
            try:
                n1, n2 = int(sys.argv[2]), int(sys.argv[3])
            except ValueError as e:
                print(json.dumps(error_response("INVALID_NUMBER",
                                                f"两数必须为整数: {e}"),
                                 ensure_ascii=False, indent=2))
                sys.exit(2)
            question = ' '.join(sys.argv[4:]) or None
            q = number_qigua(n1, n2)
            q['mode'] = f'数字起卦（{n1}, {n2}）'

        elif mode == 'object':
            if len(sys.argv) < 4:
                print(json.dumps(error_response("MISSING_ARGUMENTS",
                                                "物象起卦至少需两个数"),
                                 ensure_ascii=False, indent=2))
                sys.exit(1)
            nums, rest = [], []
            for a in sys.argv[2:]:
                try:
                    nums.append(int(a))
                except ValueError:
                    rest.append(a)
            question = ' '.join(rest) or None
            q = object_qigua(nums)
            q['mode'] = f'物象起卦（{nums}）'

        else:
            print(json.dumps(error_response("INVALID_MODE",
                                            f"未知模式：{mode}，"
                                            f"支持 time/number/object"),
                             ensure_ascii=False, indent=2))
            sys.exit(1)
    except Exception as e:
        print(json.dumps(error_response("CALC_ERROR", str(e)),
                         ensure_ascii=False, indent=2))
        sys.exit(3)

    gua = build_gua(q['up'], q['down'], q['moving'])
    j = judge(gua)

    print(format_report(q, gua, j, question))

    result = {
        'mode': q['mode'],
        'ben_gua': gua['name'],
        'up': gua['up'], 'down': gua['down'],
        'moving_yao': YAO_NAMES[gua['moving'] - 1],
        'ti': {'gua': gua['ti'], 'wuxing': gua['ti_wuxing']},
        'yong': {'gua': gua['yong'], 'wuxing': gua['yong_wuxing']},
        'hu_gua': gua['hu_name'],
        'bian_gua': gua['bian_name'],
        'zong_gua': gua['zong_name'],
        'cuo_gua': gua['cuo_name'],
        'judgement': j,
        'question': question,
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
