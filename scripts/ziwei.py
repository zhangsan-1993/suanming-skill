#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紫微斗数排盘工具 v3.0 —— 依《紫微斗数全书》安星法完整实现

典籍依据（references/ziwei.md、SKILL.md 紫微典籍规则表）：
- 《紫微斗数全书·安星法》  寅起正月，顺数至生月，逆数生时为命宫；
                            顺数生时为身宫
- 《紫微斗数全书·定五行局》 命宫干支纳音定局：水二、木三、金四、土五、火六
- 《紫微斗数全书·起紫微》  六五四三二，酉午亥辰丑；局数除日数，商数宫前走
- 《紫微斗数全书·排盘诀》  紫微→天机→空一→太阳→武曲→天同→空两→廉贞（逆行）；
                            天府→太阴→贪狼→巨门→天相→天梁→七杀→空三→破军（顺行）
- 《紫微斗数全书·四化诀》  南派：甲廉破武阳、乙机梁紫阴、丙同机昌廉、
                            丁阴同机巨、戊贪阴右机、己武贪梁曲、庚阳武阴同、
                            辛巨阳曲昌、壬梁紫左武、癸破巨阴贪
- 《紫微斗数全书·定宫诀》  命宫→逆时针：兄弟、夫妻、子女、财帛、疾厄、
                            迁移、交友、事业、田宅、福德、父母
- 《紫微斗数全书·起大限》  大限由命宫起，阳男阴女顺行，阴男阳女逆行，
                            每十年过一宫

【v3.0 重写说明（2026-09 修正）】
1. 十四主星曾误用「命宫偏移」定位而撞宫，现按排盘诀的间隔口诀实现：
   紫微系逆行、天府系顺行。
2. 四化表戊/庚/辛/癸等年干曾多处置错，现依南派口诀全表校正。
3. 十二宫曾把「命宫」硬绑在第 1 宫、与命宫落点冲突，现改为命宫落点即命宫，
   其余按定宫诀逆时针排布。
4. 紫微星定位、命身宫一度用公历月日，现改用农历生月生日（斗数以农历为准）。
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple

# ==================== 常量 ====================

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 十二宫（自命宫起逆时针）
SHI_ER_GONG = ['命宫', '兄弟', '夫妻', '子女', '财帛', '疾厄',
               '迁移', '交友', '官禄', '田宅', '福德', '父母']

# 十四主星
ZHU_XING = ['紫微', '天机', '太阳', '武曲', '天同', '廉贞',
            '天府', '太阴', '贪狼', '巨门', '天相', '天梁', '七杀', '破军']

# 紫微系（北斗六星，逆行）；相对紫微的偏移（负=逆行宫数）
# 口诀：紫微天机星逆行，隔一阳武天同行，又隔二宫看廉贞
ZIWEI_XI = {'紫微': 0, '天机': -1, '太阳': -3, '武曲': -4, '天同': -5, '廉贞': -8}

# 天府系（南斗八星，顺行）；相对天府的偏移
# 口诀：天府太阴与贪狼，巨门天相及天梁，七杀空三破军乡
TIANFU_XI = {'天府': 0, '太阴': 1, '贪狼': 2, '巨门': 3,
             '天相': 4, '天梁': 5, '七杀': 6, '破军': 10}

# 五行局数：水二、木三、金四、土五、火六
JUSHU = {'水': 2, '木': 3, '金': 4, '土': 5, '火': 6}

# 起紫微星诀：六五四三二 → 酉午亥辰丑
# 即 局数 -> 起始宫
ZIWEI_START = {6: '酉', 5: '午', 4: '亥', 3: '辰', 2: '丑'}

# 六十甲子纳音（每两甲子一组，共三十组）
# 顺序依《六十甲子纳音表》：海中金、炉中火、大林木、路旁土、剑锋金……
NAYIN_30 = ['金', '火', '木', '土', '金', '火', '水', '土', '金', '木',
            '水', '土', '火', '木', '水', '金', '火', '木', '土', '金',
            '火', '水', '土', '金', '木', '水', '土', '火', '木', '水']

# 五虎遁（年干 -> 寅月天干索引）
WUHUDUN = {0: 2, 5: 2, 1: 4, 6: 4, 2: 6, 7: 6, 3: 8, 8: 8, 4: 0, 9: 0}

# 四化（南派安四化星诀）—— (化禄, 化权, 化科, 化忌)
SIHUA = {
    '甲': ('廉贞', '破军', '武曲', '太阳'),   # 甲廉破武阳
    '乙': ('天机', '天梁', '紫微', '太阴'),   # 乙机梁紫阴
    '丙': ('天同', '天机', '文昌', '廉贞'),   # 丙同机昌廉
    '丁': ('太阴', '天同', '天机', '巨门'),   # 丁阴同机巨
    '戊': ('贪狼', '太阴', '右弼', '天机'),   # 戊贪阴右机
    '己': ('武曲', '贪狼', '天梁', '文曲'),   # 己武贪梁曲
    '庚': ('太阳', '武曲', '太阴', '天同'),   # 庚阳武阴同
    '辛': ('巨门', '太阳', '文曲', '文昌'),   # 辛巨阳曲昌
    '壬': ('天梁', '紫微', '左辅', '武曲'),   # 壬梁紫左武
    '癸': ('破军', '巨门', '太阴', '贪狼'),   # 癸破巨阴贪
}

# 主星庙旺陷（references/ziwei.md 十四主星庙旺简表）
MIAO_WANG = {
    '紫微': {'庙': ['寅', '卯'], '旺': ['亥', '子', '午', '未'], '地': ['辰', '戌', '丑'],
             '利': ['巳'], '平': ['申', '酉'], '陷': []},
    '天机': {'庙': ['寅', '卯'], '旺': ['亥', '子'], '地': ['辰', '戌', '丑'],
             '利': ['午'], '平': ['巳'], '陷': ['申', '酉']},
    '太阳': {'庙': ['寅', '卯', '午', '未'], '旺': ['巳'], '地': ['亥'],
             '利': ['申', '酉'], '平': ['辰', '戌'], '陷': ['子']},
    '武曲': {'庙': ['辰', '戌', '丑', '未'], '旺': ['申', '酉'], '地': ['寅', '卯'],
             '利': ['亥', '子'], '平': ['午'], '陷': ['巳']},
    '天同': {'庙': ['卯', '辰', '巳', '未'], '旺': ['亥', '子'], '地': ['寅'],
             '利': ['午'], '平': ['丑'], '陷': ['申', '酉']},
    '廉贞': {'庙': ['寅', '午', '未'], '旺': ['亥'], '地': ['辰', '戌'],
             '利': ['申', '酉'], '平': ['卯'], '陷': ['子', '丑']},
    '天府': {'庙': ['午', '未', '申', '酉'], '旺': ['卯', '辰'], '地': ['亥', '子'],
             '利': ['寅'], '平': ['丑'], '陷': ['巳']},
    '太阴': {'庙': ['亥', '子', '丑'], '旺': ['申', '酉'], '地': ['卯', '辰'],
             '利': ['午'], '平': ['寅'], '陷': ['巳']},
    '贪狼': {'庙': ['亥', '子'], '旺': ['寅', '卯'], '地': ['辰', '戌'],
             '利': ['午'], '平': ['巳'], '陷': ['申', '酉']},
    '巨门': {'庙': ['寅', '卯'], '旺': ['申', '酉'], '地': ['辰', '戌'],
             '利': ['亥', '子'], '平': ['午'], '陷': ['巳']},
    '天相': {'庙': ['寅', '卯', '辰', '巳'], '旺': ['亥', '子'], '地': ['午', '未'],
             '利': ['丑'], '平': ['戌'], '陷': ['申', '酉']},
    '天梁': {'庙': ['寅', '卯', '午', '未'], '旺': ['亥', '子'], '地': ['丑'],
             '利': ['辰', '戌'], '平': ['申', '酉'], '陷': ['巳']},
    '七杀': {'庙': ['寅', '卯', '午', '未'], '旺': ['申', '酉'], '地': ['亥', '子'],
             '利': ['辰', '戌'], '平': ['丑'], '陷': ['巳']},
    '破军': {'庙': ['辰', '戌'], '旺': ['丑'], '地': ['寅', '卯'],
             '利': ['亥', '子'], '平': ['午'], '陷': ['巳']},
}

# 命主（按年支）：子属贪狼丑亥门，寅戌生人属禄存，卯酉属文巳未武，辰申廉宿午破军
MINGZHU = {'子': '贪狼', '丑': '巨门', '亥': '巨门', '寅': '禄存', '戌': '禄存',
           '卯': '文曲', '酉': '文曲', '巳': '武曲', '未': '武曲',
           '辰': '廉贞', '申': '廉贞', '午': '破军'}

# 身主（按年支）：子午安身铃火宿，丑未天相寅申梁，卯酉天同身主是，巳亥天机辰戌昌
SHENZHU = {'子': '铃星', '午': '火星', '丑': '天相', '未': '天相',
           '寅': '天梁', '申': '天梁', '卯': '天同', '酉': '天同',
           '巳': '天机', '亥': '天机', '辰': '文昌', '戌': '文昌'}


# ==================== 历法与干支 ====================

def _lunar_date(year: int, month: int, day: int):
    """公历 -> LunarDate（兼容 lunardate 新旧 API）"""
    from lunardate import LunarDate
    try:
        return LunarDate.from_solar_date(year, month, day)   # 新 API
    except AttributeError:
        return LunarDate.fromSolarDate(year, month, day)     # 旧 API 回退


def solar_to_lunar(year: int, month: int, day: int) -> Tuple[int, int, bool]:
    """公历 -> 农历（年, 月, 是否闰月）；依赖 lunardate"""
    try:
        ld = _lunar_date(year, month, day)
        return ld.year, ld.month, ld.isLeapMonth
    except Exception:
        return None, None, False


def get_year_ganzhi(year: int, month: int, day: int, hour: int) -> Tuple[str, str]:
    """年柱干支（立春分界，与 bazi 同源）"""
    from p0_validators import get_jieqi_datetime
    from datetime import datetime as _dt
    birth = _dt(year, month, day, hour)
    lichun = get_jieqi_datetime(year, '立春')
    eff_year = year if birth >= lichun else year - 1
    return TIANGAN[(eff_year - 4) % 10], DIZHI[(eff_year - 4) % 12]


def ganzhi_index(gan: str, zhi: str) -> int:
    """干支 -> 六十甲子序号（0-59）；干支须同阴阳"""
    g, z = TIANGAN.index(gan), DIZHI.index(zhi)
    for i in range(60):
        if i % 10 == g and i % 12 == z:
            return i
    return -1


def nayin_wuxing(gan: str, zhi: str) -> str:
    """查六十甲子纳音五行"""
    idx = ganzhi_index(gan, zhi)
    if idx < 0:
        return '土'
    return NAYIN_30[idx // 2]


def wuhudun_gan(year_gan: str, zhi: str) -> str:
    """五虎遁：由年干、地支求该支天干（用于命宫天干）"""
    yg = TIANGAN.index(year_gan)
    start = WUHUDUN[yg]                       # 寅月天干索引
    zhi_idx = DIZHI.index(zhi)                # 子=0
    offset = (zhi_idx - 2) % 12               # 自寅(2)顺数
    return TIANGAN[(start + offset) % 10]


def hour_to_zhi_index(hour: int) -> int:
    """时辰 -> 地支索引：23/0 为子(0)，1/2 为丑(1)……"""
    return int((hour + 1) / 2) % 12


# ==================== 安星核心 ====================

def get_ming_shen_gong(lunar_month: int, hour: int) -> Tuple[int, int]:
    """
    安命身宫诀：
      寅起正月，顺数至生月，逆数生时为命宫
      寅起正月，顺数至生月，顺数生时为身宫
    """
    yue_gong = (DIZHI.index('寅') + (lunar_month - 1)) % 12    # 自寅顺数至生月
    shi = hour_to_zhi_index(hour)
    ming = (yue_gong - shi) % 12                                # 逆数生时
    shen = (yue_gong + shi) % 12                                # 顺数生时
    return ming, shen


def get_wuxing_ju(ming_zhi: str, year_gan: str) -> Tuple[str, int]:
    """
    定五行局：命宫地支遁天干 -> 纳音 -> 局数（水二木三金四土五火六）
    """
    ming_gan = wuhudun_gan(year_gan, ming_zhi)
    wx = nayin_wuxing(ming_gan, ming_zhi)
    return wx, JUSHU[wx]


def get_ziwei_gong(ju: int, lunar_day: int) -> int:
    """
    起紫微星诀：六五四三二，酉午亥辰丑；局数除日数，商数宫前走。
    自该局起始宫顺数 (生日-1)//局数 格。
    """
    start_zhi = ZIWEI_START[ju]
    start = DIZHI.index(start_zhi)
    steps = (lunar_day - 1) // ju
    return (start + steps) % 12


def distribute_main_stars(ziwei_gong: int) -> Dict[int, List[str]]:
    """
    排十四主星：
      紫微系逆行（紫微→天机→空一→太阳→武曲→天同→空两→廉贞）
      天府星在紫微顺行四宫；天府系顺行（天府→太阴→贪狼→巨门→
      天相→天梁→七杀→空三→破军）
    """
    palaces = {i: [] for i in range(12)}

    for star, off in ZIWEI_XI.items():
        palaces[(ziwei_gong + off) % 12].append(star)

    tianfu_gong = (ziwei_gong + 4) % 12
    for star, off in TIANFU_XI.items():
        palaces[(tianfu_gong + off) % 12].append(star)

    return palaces


def palace_name(ming_gong: int, idx: int) -> str:
    """定宫诀：自命宫逆时针排十二宫"""
    return SHI_ER_GONG[(idx - ming_gong) % 12]


def calculate_sihua(year_gan: str) -> Dict[str, str]:
    """安四化星诀（南派）"""
    lu, quan, ke, ji = SIHUA[year_gan]
    return {'化禄': lu, '化权': quan, '化科': ke, '化忌': ji}


def get_miaowang(star: str, zhi: str) -> str:
    """查星曜庙旺"""
    if star not in MIAO_WANG:
        return '平'
    for level, zhis in MIAO_WANG[star].items():
        if zhi in zhis:
            return level
    return '平'


def get_daxian(ming_gong: int, age: int, gender: str, year_gan: str) -> Tuple[int, Tuple[int, int]]:
    """
    起大限诀：大限由命宫起，阳男阴女顺行，阴男阳女逆行，每十年过一宫。
    阳年干：甲丙戊庚壬；阴年干：乙丁己辛癸
    """
    yang_gan = TIANGAN.index(year_gan) % 2 == 0
    forward = (yang_gan and gender == '男') or ((not yang_gan) and gender == '女')
    step = age // 10
    if forward:
        idx = (ming_gong + step) % 12
    else:
        idx = (ming_gong - step) % 12
    return idx, (step * 10 + 1, step * 10 + 10)


# ==================== 排盘主流程 ====================

def pan(year: int, month: int, day: int, hour: int, gender: str) -> Dict:
    """完整排盘"""
    lunar_year, lunar_month, is_leap = solar_to_lunar(year, month, day)
    if lunar_year is None:
        raise RuntimeError('农历转换失败，请安装 lunardate')

    ld = _lunar_date(year, month, day)
    lunar_day = ld.day

    year_gan, year_zhi = get_year_ganzhi(year, month, day, hour)
    ming_gong, shen_gong = get_ming_shen_gong(lunar_month, hour)
    ming_zhi = DIZHI[ming_gong]
    ming_gan = wuhudun_gan(year_gan, ming_zhi)
    wuxing, ju = get_wuxing_ju(ming_zhi, year_gan)
    ziwei_gong = get_ziwei_gong(ju, lunar_day)
    palaces = distribute_main_stars(ziwei_gong)
    sihua = calculate_sihua(year_gan)

    current_year = datetime.now().year
    age = current_year - year
    daxian_idx, daxian_years = get_daxian(ming_gong, age, gender, year_gan)

    return {
        'year_gan': year_gan, 'year_zhi': year_zhi,
        'lunar': {'year': lunar_year, 'month': lunar_month,
                  'day': lunar_day, 'is_leap': is_leap},
        'ming_gong': ming_gong, 'shen_gong': shen_gong,
        'ming_ganzhi': ming_gan + ming_zhi,
        'wuxing_ju': wuxing, 'ju': ju,
        'ziwei_gong': ziwei_gong,
        'palaces': palaces,
        'sihua': sihua,
        'daxian': {'index': daxian_idx, 'years': daxian_years},
        'mingzhu': MINGZHU.get(year_zhi, ''),
        'shenzhu': SHENZHU.get(year_zhi, ''),
        'age': age,
    }


def format_report(p: Dict, year, month, day, hour, gender) -> str:
    out = []
    out.append("=" * 58)
    out.append("【紫微斗数命盘】")
    out.append("=" * 58)
    ln = p['lunar']
    out.append(f"  公历：{year}-{month:02d}-{day:02d} {hour:02d}时　性别：{gender}")
    out.append(f"  农历：{ln['year']}年{'闰' if ln['is_leap'] else ''}"
               f"{ln['month']}月{ln['day']}日")
    out.append(f"  年柱：{p['year_gan']}{p['year_zhi']}")
    out.append(f"  五行局：{p['wuxing_ju']}{p['ju']}局")
    out.append(f"  命宫：{DIZHI[p['ming_gong']]}宫（{p['ming_ganzhi']}）")
    out.append(f"  身宫：{DIZHI[p['shen_gong']]}宫")
    out.append(f"  命主：{p['mingzhu']}　身主：{p['shenzhu']}")
    out.append("")

    out.append("【十二宫星曜分布】")
    for i in range(12):
        stars = p['palaces'].get(i, [])
        name = palace_name(p['ming_gong'], i)
        zhi = DIZHI[i]
        if stars:
            detail = []
            for s in stars:
                mw = get_miaowang(s, zhi)
                mark = ''
                for k, v in p['sihua'].items():
                    if v == s:
                        mark = k
                detail.append(f"{s}（{mw}）{mark}")
            out.append(f"  {zhi}宫 {name}：{'、'.join(detail)}")
        else:
            out.append(f"  {zhi}宫 {name}：（空宫）")
    out.append("")

    out.append("【四化飞星】《紫微斗数全书》南派诀")
    for k in ['化禄', '化权', '化科', '化忌']:
        out.append(f"  {k}：{p['sihua'][k]}")
    out.append("")
    out.append(f"  当前大限：{DIZHI[p['daxian']['index']]}宫"
               f"（{p['daxian']['years'][0]}-{p['daxian']['years'][1]}岁）")
    return "\n".join(out)


# ==================== 自检 ====================

def check_main_stars(palaces: Dict[int, List[str]]) -> Tuple[bool, List[str]]:
    """十四主星应各出现一次，不得缺失或重复"""
    errors = []
    seen = {}
    for stars in palaces.values():
        for s in stars:
            if s in ZHU_XING:
                seen[s] = seen.get(s, 0) + 1
    for star in ZHU_XING:
        if star not in seen:
            errors.append(f'主星 {star} 缺失')
        elif seen[star] > 1:
            errors.append(f'主星 {star} 重复出现 {seen[star]} 次')
    return (len(errors) == 0, errors)


# ==================== 主函数 ====================

def main():
    import sys

    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("紫微斗数排盘工具 v3.0（依《紫微斗数全书》安星法）")
        print("用法: python ziwei.py <年> <月> <日> <时> [性别:男/女]")
        print("示例:")
        print("  python ziwei.py 1993 6 18 15 女")
        print("  python ziwei.py 2000 1 1 12 男")
        sys.exit(0)

    if len(sys.argv) < 5:
        print(json.dumps(error_response("MISSING_ARGUMENTS",
                                        "用法: python ziwei.py <年> <月> <日> <时> [性别]"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        year, month, day, hour = (int(sys.argv[i]) for i in (1, 2, 3, 4))
    except ValueError as e:
        print(json.dumps(error_response("INVALID_NUMBER", f"参数必须为整数: {e}"),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    gender = sys.argv[5] if len(sys.argv) > 5 else '男'

    from p0_validators import _valid_date
    verrs = _valid_date(year, month, day, hour)
    if verrs:
        print(json.dumps(error_response("INVALID_INPUT", verrs),
                         ensure_ascii=False, indent=2))
        sys.exit(2)
    if gender not in ('男', '女'):
        print(json.dumps(error_response("INVALID_GENDER",
                                        f"性别必须为男或女，收到 {gender}"),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    p = pan(year, month, day, hour, gender)

    ok, errs = check_main_stars(p['palaces'])
    print(format_report(p, year, month, day, hour, gender))
    if not ok:
        print("\n⚠ 主星校验未通过：" + "；".join(errs))

    result = {
        'birth': {'year': year, 'month': month, 'day': day, 'hour': hour, 'gender': gender},
        'lunar': p['lunar'],
        'year_ganzhi': p['year_gan'] + p['year_zhi'],
        'wuxing_ju': f"{p['wuxing_ju']}{p['ju']}局",
        'ming_gong': DIZHI[p['ming_gong']],
        'ming_ganzhi': p['ming_ganzhi'],
        'shen_gong': DIZHI[p['shen_gong']],
        'ziwei_gong': DIZHI[p['ziwei_gong']],
        'mingzhu': p['mingzhu'],
        'shenzhu': p['shenzhu'],
        'palaces': {DIZHI[i]: {'宫名': palace_name(p['ming_gong'], i),
                               '星曜': [{'星': s, '庙旺': get_miaowang(s, DIZHI[i])}
                                        for s in p['palaces'].get(i, [])]}
                    for i in range(12)},
        'sihua': p['sihua'],
        'daxian': {'宫': DIZHI[p['daxian']['index']], 'years': p['daxian']['years']},
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
