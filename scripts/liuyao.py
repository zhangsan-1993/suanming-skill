#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六爻起卦工具 v3.0 —— 京房八宫纳甲体系完整实现

典籍依据：
- 《火珠林·起卦章》    三枚铜钱抛六次：三正为老阳○，三反为老阴×，
                        二正一反为少阳—，一正二反为少阴- -
- 《卜筮正宗·纳甲法》  八宫纳甲：乾内子寅辰、外午申戌；坎内寅辰午、外申戌子...
- 《火珠林·世应章》    八宫各有世应：本宫世六应三，一世世初应四……
- 《卜筮正宗·六亲章》  以卦宫五行为「我」，与各爻地支五行论生克定六亲
- 《卜筮正宗·用神章》  问官=官鬼，问财=妻财，问病=子孙/官鬼，问自身=世爻
- 《火珠林·断易章》    用神旺相+动爻生扶=吉；用神休囚+动爻克害=凶
- 《梅花易数·时间占》  年月日÷8为上卦，年月日时÷8为下卦，年月日时÷6为动爻

【v3.0 重写说明（2026-09 修正）】
v2.0 存在根本性缺陷，已全部替换：
1. 六亲曾按「爻的阴阳」硬编码（阳=官鬼、阴=妻财），现改为按卦宫五行与
   纳甲地支五行的生克关系推算。
2. 曾完全缺失纳甲（各爻无干支），现按《卜筮正宗·纳甲法》补齐八宫纳甲。
3. 世应曾硬编码为「世初爻、应四爻」，现按八宫卦世应规律判定。
4. 卦宫曾误取「外卦」，现按京房八宫卦序正确判定卦之归属。
5. 卦名曾用「X之Y」非标准称法，现输出标准六十四卦名（如 山雷颐）。
6. get_gua_from_lines 曾以爻值 6/7/8/9 充当二进制权重、并误用先天数为索引，
   导致乾卦被识别为坤卦；现改为按三爻阴阳查标准八卦表。
7. 六神起法 LIUSHEN_START 乙/丙/丁/戊/己 有误，现按「甲乙起青龙……」校正。
8. 时间起卦曾逐爻取模（无典籍依据），现改为《梅花易数·时间占》标准法。
"""

import json
import random
from datetime import datetime
from typing import Dict, List, Tuple

# ==================== 常量定义 ====================

# 八卦三爻（初、二、三；1=阳爻, 0=阴爻）
# 象：乾三连 兑上缺 离中虚 震仰盂 巽下断 坎中满 艮覆碗 坤六断
TRIGRAM = {
    '乾': (1, 1, 1),
    '兑': (1, 1, 0),
    '离': (1, 0, 1),
    '震': (1, 0, 0),
    '巽': (0, 1, 1),
    '坎': (0, 1, 0),
    '艮': (0, 0, 1),
    '坤': (0, 0, 0),
}
TRIGRAM_BY_LINES = {v: k for k, v in TRIGRAM.items()}

# 先天八卦数：乾1 兑2 离3 震4 巽5 坎6 艮7 坤8（梅花易数起卦用）
XIANTIAN = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']

# 八卦五行 / 八宫五行
GUA_WUXING = {
    '乾': '金', '兑': '金', '离': '火', '震': '木',
    '巽': '木', '坎': '水', '艮': '土', '坤': '土',
}

# 京房纳甲 —— 每宫六爻地支（初爻→上爻）
# 阳宫顺行、阴宫逆行，每隔一位取支
NAJIA_ZHI = {
    '乾': ['子', '寅', '辰', '午', '申', '戌'],
    '震': ['子', '寅', '辰', '午', '申', '戌'],
    '坎': ['寅', '辰', '午', '申', '戌', '子'],
    '艮': ['辰', '午', '申', '戌', '子', '寅'],
    '坤': ['未', '巳', '卯', '丑', '亥', '酉'],
    '巽': ['丑', '亥', '酉', '未', '巳', '卯'],
    '离': ['卯', '丑', '亥', '酉', '未', '巳'],
    '兑': ['巳', '卯', '丑', '亥', '酉', '未'],
}

# 京房纳甲 —— 天干：(内卦干, 外卦干)
# 乾纳甲壬、坤纳乙癸，其余六卦内外同干
NAJIA_GAN = {
    '乾': ('甲', '壬'), '坤': ('乙', '癸'),
    '震': ('庚', '庚'), '巽': ('辛', '辛'),
    '坎': ('戊', '戊'), '离': ('己', '己'),
    '艮': ('丙', '丙'), '兑': ('丁', '丁'),
}

# 八宫六十四卦名（按世序：本宫、一世、二世、三世、四世、五世、游魂、归魂）
GUA64_NAMES = {
    '乾': ['乾为天', '天风姤', '天山遁', '天地否', '风地观', '山地剥', '火地晋', '火天大有'],
    '坎': ['坎为水', '水泽节', '水雷屯', '水火既济', '泽火革', '雷火丰', '地火明夷', '地水师'],
    '艮': ['艮为山', '山火贲', '山天大畜', '山泽损', '火泽睽', '天泽履', '风泽中孚', '风山渐'],
    '震': ['震为雷', '雷地豫', '雷水解', '雷风恒', '地风升', '水风井', '泽风大过', '泽雷随'],
    '巽': ['巽为风', '风天小畜', '风火家人', '风雷益', '天雷无妄', '火雷噬嗑', '山雷颐', '山风蛊'],
    '离': ['离为火', '火山旅', '火风鼎', '火水未济', '山水蒙', '风水涣', '天水讼', '天火同人'],
    '坤': ['坤为地', '地雷复', '地泽临', '地天泰', '雷天大壮', '泽天夬', '水天需', '水地比'],
    '兑': ['兑为泽', '泽水困', '泽地萃', '泽山咸', '水山蹇', '地山谦', '雷山小过', '雷泽归妹'],
}

# 世爻位置索引（0=初爻 … 5=上爻），按世序
# 本宫世在六、一世世在初、二世在二、三世在三、四世在四、五世在五、
# 游魂世在四、归魂世在三
SHI_INDEX = [5, 0, 1, 2, 3, 4, 3, 2]

# 六神
LIUSHEN = ['青龙', '朱雀', '勾陈', '螣蛇', '白虎', '玄武']

# 六神起法（按日干定初爻起何神）
# 甲乙起青龙，丙丁起朱雀，戊起勾陈，己起螣蛇，庚辛起白虎，壬癸起玄武
LIUSHEN_START = {
    '甲': 0, '乙': 0,
    '丙': 1, '丁': 1,
    '戊': 2,
    '己': 3,
    '庚': 4, '辛': 4,
    '壬': 5, '癸': 5,
}

# 天干地支
TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 地支五行
ZHI_WUXING = {
    '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
    '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'
}

# 五行生克
WUXING_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WUXING_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

YAO_NAMES = ['初爻', '二爻', '三爻', '四爻', '五爻', '上爻']


# ==================== 生成八宫六十四卦表 ====================

def _flip(bit: int) -> int:
    return 1 - bit


def build_gua64() -> Dict[Tuple[str, str], Dict]:
    """
    按京房八宫卦序生成六十四卦索引。

    《火珠林·世应章》八宫变化规则（自纯卦起）：
      一世变初爻、二世变二爻、三世变三爻、四世变四爻、五世变五爻；
      游魂：五世再变回四爻；归魂：游魂之内卦复归纯卦内卦。

    Returns:
        {(上卦, 下卦): {'name': 卦名, 'gong': 宫, 'shi': 世爻索引,
                        'seq': 世序, 'lines': (六爻0/1)}}
    """
    table = {}
    for gong in ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']:
        base = TRIGRAM[gong]              # 内卦三爻
        lines = list(base + base)         # 纯卦：上卦=下卦
        for seq in range(8):
            if seq == 0:
                pass                                   # 本宫：纯卦
            elif seq <= 5:                             # 一世至五世：变第 seq 爻
                lines[seq - 1] = _flip(lines[seq - 1])
            elif seq == 6:                             # 游魂：五世再变回四爻（外卦初爻）
                lines[3] = TRIGRAM[gong][0]
            else:                                      # 归魂：内卦复归纯卦
                lines[0], lines[1], lines[2] = base

            inner = tuple(lines[0:3])                  # 下卦（初、二、三）
            outer = tuple(lines[3:6])                  # 上卦（四、五、上）
            key = (TRIGRAM_BY_LINES[outer], TRIGRAM_BY_LINES[inner])
            table[key] = {
                'name': GUA64_NAMES[gong][seq],
                'gong': gong,
                'shi': SHI_INDEX[seq],
                'seq': seq,
                'lines': tuple(lines),
            }
    return table


GUA64 = build_gua64()


# ==================== 爻与卦的换算 ====================

def lines_to_bits(lines: List[int]) -> List[int]:
    """爻值 -> 阴阳：7/9 为阳(1)，6/8 为阴(0)"""
    return [1 if v in (7, 9) else 0 for v in lines]


def bits_to_trigram(bits: Tuple[int, int, int]) -> str:
    """三爻阴阳 -> 八卦名"""
    return TRIGRAM_BY_LINES[tuple(bits)]


def analyze_gua(lines: List[int]) -> Dict:
    """
    由六爻（值 6/7/8/9）解析卦象：卦名、上卦、下卦、卦宫、世应。
    """
    bits = lines_to_bits(lines)
    inner = bits_to_trigram(tuple(bits[0:3]))     # 下卦
    outer = bits_to_trigram(tuple(bits[3:6]))     # 上卦

    info = GUA64.get((outer, inner))
    if info is None:                               # 兜底（正常不会触发）
        info = {
            'name': f'{outer}{inner}之卦', 'gong': outer,
            'shi': 0, 'seq': 1, 'lines': tuple(bits),
        }

    shi = info['shi']
    ying = (shi + 3) % 6                           # 应爻与世爻隔两位

    return {
        'inner': inner,
        'outer': outer,
        'name': info['name'],
        'gong': info['gong'],
        'gong_wuxing': GUA_WUXING[info['gong']],
        'shi': shi,
        'ying': ying,
        'seq': info['seq'],
        'bits': bits,
    }


# ==================== 起卦 ====================

def coin_divination() -> Tuple[int, str]:
    """
    硬币占卜法（三枚铜钱）
    《火珠林·起卦章》：三正为老阳○，三反为老阴×，
                       二正一反为少阳—，一正二反为少阴- -
    爻值：6=老阴(动), 7=少阳, 8=少阴, 9=老阳(动)
    """
    heads = sum(random.randint(0, 1) for _ in range(3))
    if heads == 3:
        return 9, '老阳(动)'
    if heads == 2:
        return 8, '少阴'
    if heads == 1:
        return 7, '少阳'
    return 6, '老阴(动)'


def time_divination(year: int, month: int, day: int, hour: int) -> List[Tuple[int, str]]:
    """
    时间起卦法
    《梅花易数·时间占》：年月日÷8 余数为上卦，年月日时÷8 余数为下卦，
                        年月日时÷6 余数为动爻。
    余数为 0 时，卦取 8（坤）、爻取 6（上爻）。
    """
    shi_index = int((hour + 1) / 2) % 12          # 时辰序号 0-11
    shi_num = shi_index + 1                        # 以 1-12 计

    n = year + month + day
    m = year + month + day + shi_num

    up = (n % 8) or 8
    down = (m % 8) or 8
    moving = (m % 6) or 6                          # 第几爻动（1-6）

    up_gua = XIANTIAN[up - 1]
    down_gua = XIANTIAN[down - 1]

    bits = list(TRIGRAM[down_gua]) + list(TRIGRAM[up_gua])   # 下三爻 + 上三爻

    lines = []
    for i, b in enumerate(bits):
        if i == moving - 1:                        # 动爻
            lines.append((9, '老阳(动)') if b == 1 else (6, '老阴(动)'))
        else:
            lines.append((7, '少阳') if b == 1 else (8, '少阴'))
    return lines


def random_divination(seed: int = None) -> List[Tuple[int, str]]:
    """随机起卦法（自动起卦用，连续摇六次）"""
    if seed is None:
        import time
        seed = int(time.time() * 1000)
    random.seed(seed)
    return [coin_divination() for _ in range(6)]


# ==================== 装卦 ====================

def assign_najia(gong: str) -> List[Dict[str, str]]:
    """
    纳甲：按《卜筮正宗·纳甲法》给六爻配天干地支。
    八宫各按其纯卦纳甲，与卦在宫中何世无关。
    """
    zhi = NAJIA_ZHI[gong]
    gan_inner, gan_outer = NAJIA_GAN[gong]
    result = []
    for i in range(6):
        gan = gan_inner if i < 3 else gan_outer
        result.append({'gan': gan, 'zhi': zhi[i], 'ganzhi': gan + zhi[i]})
    return result


def assign_liuqin(gong: str) -> List[str]:
    """
    装六亲
    《卜筮正宗·六亲章》：以卦宫五行为「我」，与纳甲各地支五行论生克：
        生我=父母，我生=子孙，克我=官鬼，我克=妻财，同我=兄弟
    """
    me = GUA_WUXING[gong]
    zhi = NAJIA_ZHI[gong]
    result = []
    for z in zhi:
        w = ZHI_WUXING[z]
        if w == me:
            result.append('兄弟')
        elif WUXING_SHENG.get(w) == me:            # 该支生我
            result.append('父母')
        elif WUXING_SHENG.get(me) == w:            # 我生该支
            result.append('子孙')
        elif WUXING_KE.get(w) == me:               # 该支克我
            result.append('官鬼')
        else:                                       # 我克该支
            result.append('妻财')
    return result


def assign_liushen(day_gan: str) -> List[str]:
    """
    装六神
    《卜筮正宗》：甲乙起青龙，丙丁起朱雀，戊起勾陈，
                 己起螣蛇，庚辛起白虎，壬癸起玄武，自初爻顺排。
    """
    start = LIUSHEN_START.get(day_gan, 0)
    return [LIUSHEN[(start + i) % 6] for i in range(6)]


def get_moving_lines(lines: List[int]) -> List[int]:
    """动爻位置（老阳老阴为动爻）"""
    return [i for i, v in enumerate(lines) if v in (6, 9)]


def get_biangua(lines: List[int]) -> Tuple[List[int], str, Dict]:
    """求变卦：动爻阴阳互变，并解析变卦卦象"""
    bits = lines_to_bits(lines)
    # 变卦：动爻阴阳互变（老阳变阴、老阴变阳），静爻不变；
    # 变爻在变卦中仍记作 6/9，以示其动
    changed_lines = []
    for v, b in zip(lines, bits):
        if v in (6, 9):
            changed_lines.append(9 if b == 0 else 6)
        else:
            changed_lines.append(v)
    info = analyze_gua(changed_lines)
    return changed_lines, info['name'], info


# ==================== 日干支 ====================

def calculate_day_ganzhi(year: int, month: int, day: int) -> Tuple[str, str]:
    """计算日柱干支（儒略日法，锚点 2000-01-01 = 戊午）"""
    def julian_day(y: int, m: int, d: int) -> float:
        if m <= 2:
            y -= 1
            m += 12
        a = int(y / 100)
        b = 2 - a + int(a / 4)
        return int(365.25 * (y + 4716)) + int(30.6001 * (m + 1)) + d + b - 1524.5

    base_gan, base_zhi = 4, 6                      # 2000-01-01 = 戊午
    diff = int(julian_day(year, month, day) - 2451544.5)
    return TIANGAN[(base_gan + diff) % 10], DIZHI[(base_zhi + diff) % 12]


# ==================== 输出 ====================

def draw_hexagram_text(lines: List[Tuple[int, str]], liushen: List[str],
                       liuqin: List[str], najia: List[Dict],
                       gua: Dict, moving: List[int]) -> str:
    """绘制卦象文本（含纳甲干支、六亲、六神、世应、动爻标记）"""
    out = []
    out.append("=" * 58)
    out.append(f"【本卦】{gua['name']}（{gua['gong']}宫 · {gua['gong_wuxing']}）")
    out.append("=" * 58)

    symbol = {1: '———', 0: '— —'}
    for i in range(5, -1, -1):                     # 自上爻至初爻
        bit = gua['bits'][i]
        mark = '○' if lines[i][0] == 9 else ('×' if lines[i][0] == 6 else ' ')
        shi_mark = '【世】' if i == gua['shi'] else ('【应】' if i == gua['ying'] else '    ')
        dong = ' (动)' if i in moving else ''
        out.append(
            f"{YAO_NAMES[i]}：{liushen[i]} {liuqin[i]} {najia[i]['ganzhi']} "
            f"{symbol[bit]}{mark} {shi_mark}{dong}"
        )
    out.append("")
    out.append(f"  上卦（外）：{gua['outer']}　下卦（内）：{gua['inner']}")
    out.append(f"  世爻：{YAO_NAMES[gua['shi']]}　应爻：{YAO_NAMES[gua['ying']]}")
    return "\n".join(out)


def format_analysis(gua: Dict, biang: Dict, liuqin: List[str],
                    question: str = None) -> str:
    """解卦要点与用神提示"""
    out = []
    out.append("【装卦说明】")
    out.append(f"  卦宫：{gua['name']}属{gua['gong']}宫（{gua['gong_wuxing']}）")
    out.append(f"  六亲（自初爻起）：{'、'.join(liuqin)}")
    out.append("")
    out.append("【六亲含义】《增删卜易》")
    out.append("  父母爻：文书、契约、父母、房产、车辆")
    out.append("  兄弟爻：兄弟姐妹、竞争、破财")
    out.append("  子孙爻：子女、福神、喜悦、医生")
    out.append("  妻财爻：妻子、钱财、物资")
    out.append("  官鬼爻：官职、小人、疾病、丈夫")
    out.append("")
    out.append("【用神选取】《卜筮正宗·用神章》")
    out.append("  问功名/官非 = 官鬼　问钱财 = 妻财")
    out.append("  问文书/长辈 = 父母　问自身 = 世爻")
    out.append("  问疾病 = 子孙（占病）/ 官鬼（占官非）")
    out.append("")
    out.append("【解卦要点】《增删卜易》")
    out.append("  1. 先看世爻旺衰")
    out.append("  2. 依所问之事取用神（见上）")
    out.append("  3. 观动爻之变、日月生克冲合")
    out.append("  4. 断吉凶：用神旺相+动爻生扶=吉，休囚受克=凶")
    if question:
        out.append("")
        out.append(f"【所问】{question}")
    return "\n".join(out)


# ==================== 主函数 ====================

def main():
    """主函数"""
    import sys

    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("六爻起卦工具 v3.0（京房八宫纳甲体系）")
        print("用法:")
        print("  自动起卦: python liuyao.py auto [问题描述]")
        print("  时间起卦: python liuyao.py time <年> <月> <日> <时> [问题描述]")
        print("示例:")
        print("  python liuyao.py auto 我的财运如何")
        print("  python liuyao.py time 2026 9 2 18 小米近期舆情走势")
        sys.exit(0)

    if len(sys.argv) < 2:
        print(json.dumps(error_response("MISSING_ARGUMENTS",
                                        "用法: python liuyao.py auto/time [参数]"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    mode = sys.argv[1]

    if mode == 'auto':
        question = sys.argv[2] if len(sys.argv) > 2 else None
        raw = random_divination()
    elif mode == 'time':
        if len(sys.argv) < 6:
            print(json.dumps(error_response("MISSING_ARGUMENTS",
                                            "时间起卦需提供年月日时"),
                             ensure_ascii=False, indent=2))
            sys.exit(1)
        try:
            year, month, day, hour = (int(sys.argv[i]) for i in (2, 3, 4, 5))
        except ValueError as e:
            print(json.dumps(error_response("INVALID_NUMBER",
                                            f"年月日时必须为整数: {e}"),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
        from p0_validators import _valid_date
        verrs = _valid_date(year, month, day, hour)
        if verrs:
            print(json.dumps(error_response("INVALID_INPUT", verrs),
                             ensure_ascii=False, indent=2))
            sys.exit(2)
        question = sys.argv[6] if len(sys.argv) > 6 else None
        raw = time_divination(year, month, day, hour)
    else:
        print(json.dumps(error_response("INVALID_MODE",
                                        f"未知模式：{mode}，支持 auto 或 time"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    lines = [v for v, _ in raw]
    descs = [d for _, d in raw]

    now = datetime.now()
    day_gan, day_zhi = calculate_day_ganzhi(now.year, now.month, now.day)

    gua = analyze_gua(lines)
    najia = assign_najia(gua['gong'])
    liuqin = assign_liuqin(gua['gong'])
    liushen = assign_liushen(day_gan)
    moving = get_moving_lines(lines)
    _, biang_name, biang_info = get_biangua(lines)

    print(draw_hexagram_text(raw, liushen, liuqin, najia, gua, moving))
    print("")
    print(f"【变卦】{biang_name}")
    print("")
    print(format_analysis(gua, biang_info, liuqin, question))

    result = {
        'ben_gua': gua['name'],
        'ben_gong': gua['gong'],
        'gong_wuxing': gua['gong_wuxing'],
        'inner': gua['inner'],
        'outer': gua['outer'],
        'bian_gua': biang_name,
        'ri_ganzhi': f"{day_gan}{day_zhi}",
        'shi_position': gua['shi'],
        'ying_position': gua['ying'],
        'lines': [
            {'position': YAO_NAMES[i], 'value': lines[i], 'desc': descs[i],
             'yang': gua['bits'][i], 'ganzhi': najia[i]['ganzhi'],
             'liushen': liushen[i], 'liuqin': liuqin[i],
             'is_moving': i in moving}
            for i in range(6)
        ],
        'dong_yao': [YAO_NAMES[i] for i in moving],
        'question': question,
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
