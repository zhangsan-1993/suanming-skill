#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
八字排盘工具 v2.0
整合《渊海子平》《滴天髓》《子平真诠》《穷通宝鉴》《三命通会》等经典理论
参考古籍：《千里命稿》《八字命学新诠》等现代教材
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import math

# 引入 p0_validators 的权威节气/干支计算（p0 不反向 import bazi，无循环依赖）
from p0_validators import get_jieqi_datetime, check_jieqi_boundary, _julian_day

# ============== 天干地支常量 ==============

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']  # 0-9
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']  # 0-11

# 天干阴阳
YINYANG_TIAN = {'甲': '阳', '乙': '阴', '丙': '阳', '丁': '阴', '戊': '阳', '己': '阴', '庚': '阳', '辛': '阴', '壬': '阳', '癸': '阴'}

# 天干五行
WUXING_TIAN = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 地支阴阳
YINYANG_ZHI = {'子': '阳', '丑': '阴', '寅': '阳', '卯': '阴', '辰': '阳', '巳': '阴', '午': '阳', '未': '阴', '申': '阳', '酉': '阴', '戌': '阳', '亥': '阴'}

# 地支五行
WUXING_ZHI = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}

# 地支藏干（地支所藏人元）
ZANGGAN = {
    '子': ['癸'],
    '丑': ['己', '癸', '辛'],
    '寅': ['甲', '丙', '戊'],
    '卯': ['乙'],
    '辰': ['戊', '乙', '癸'],
    '巳': ['丙', '庚', '戊'],
    '午': ['丁', '己'],
    '未': ['己', '丁', '乙'],
    '申': ['庚', '壬', '戊'],
    '酉': ['辛'],
    '戌': ['戊', '辛', '丁'],
    '亥': ['壬', '甲']
}

# ============== 节气计算 ==============
# 二十四节气（以节为月界，立春为寅月之首）
JIEQI_NAMES = [
    '立春', '雨水', '惊蛰', '春分', '清明', '谷雨',
    '立夏', '小满', '芒种', '夏至', '小暑', '大暑',
    '立秋', '处暑', '白露', '秋分', '寒露', '霜降',
    '立冬', '小雪', '大雪', '冬至', '小寒', '大寒'
]

# 节气的大致日期系数（简化版，用于粗略计算）
# 实际精确计算需要天文算法，此处用近似公式
JIEQI_COEFFICIENTS = {
    '立春': 4.0, '雨水': 19.0, '惊蛰': 5.0, '春分': 20.0,
    '清明': 5.0, '谷雨': 20.0, '立夏': 6.0, '小满': 21.0,
    '芒种': 6.0, '夏至': 21.0, '小暑': 7.0, '大暑': 22.0,
    '立秋': 8.0, '处暑': 23.0, '白露': 8.0, '秋分': 23.0,
    '寒露': 9.0, '霜降': 24.0, '立冬': 8.0, '小雪': 23.0,
    '大雪': 7.0, '冬至': 22.0, '小寒': 6.0, '大寒': 20.0
}

# 节气月份对应（节=月初）
JIEQI_MONTH = {
    '立春': 2, '雨水': 2, '惊蛰': 3, '春分': 3, '清明': 4, '谷雨': 4,
    '立夏': 5, '小满': 5, '芒种': 6, '夏至': 6, '小暑': 7, '大暑': 7,
    '立秋': 8, '处暑': 8, '白露': 9, '秋分': 9, '寒露': 10, '霜降': 10,
    '立冬': 11, '小雪': 11, '大雪': 12, '冬至': 12, '小寒': 1, '大寒': 1
}


def get_jieqi_date(year: int, jieqi_name: str) -> datetime:
    """
    计算指定年份节气日期（简化算法）
    基于蔡勒公式的近似计算
    """
    # 使用简化算法：节气日期 ≈ 月份基数 + 日期系数 + 年份修正
    month = JIEQI_MONTH[jieqi_name]
    base_date = JIEQI_COEFFICIENTS[jieqi_name]

    # 简化计算，实际使用需查表或天文算法
    century = (year - 2000) // 100
    year_offset = (year - 2000) % 100

    # 节气日期的简化公式
    if month <= 2:
        adjustment = -0.5 * century + 0.2
    else:
        adjustment = -0.5 * century + 0.1

    day = int(base_date + year_offset * 0.2422 + adjustment)

    # 时区校正（约8小时）
    return datetime(year, month, day, 0, 0, 0)


def get_lunar_month(year: int, month: int, day: int) -> Tuple[int, str]:
    """
    获取农历月（节气月）和社会月
    《渊海子平》：以立春为岁首（寅月=正月）
    《子平真诠》：月令为提纲
    """
    # 计算立春日期
    lichun = get_jieqi_date(year, '立春')

    # 如果在立春之前，算上年
    current_date = datetime(year, month, day)

    # 判断是否在立春之前
    if current_date < lichun:
        # 在立春之前，年柱需要退一年
        year_offset = -1
        # 重新计算上年立春
        lichun = get_jieqi_date(year - 1, '立春')
    else:
        year_offset = 0

    # 计算当前节气
    # 简化：每个节气间隔约15天
    days_since_lichun = (current_date - lichun).days
    month_index = days_since_lichun // 15  # 粗略估算

    # 月柱计算（天干地支）
    # 年份对应的天干起始（甲己之年丙作首等）
    gan_zhi_year_start = (year + year_offset - 4) % 10  # 甲=0, 乙=1, ...

    # 月柱推算：年干定月干（甲己之年丙作首）
    # 五虎遁：甲己丙为首，乙庚戊为头，丙辛从庚起，丁壬壬位推，戊癸甲为正
    month_stems_base = {
        '甲': 2, '己': 2,  # 丙寅
        '乙': 3, '庚': 3,  # 戊寅
        '丙': 4, '辛': 4,  # 庚寅
        '丁': 5, '壬': 5,  # 壬寅
        '戊': 6, '癸': 6   # 甲寅
    }
    month_stem_index = (month_stems_base[TIANGAN[gan_zhi_year_start]] + month - 1) % 10
    month_zhi_index = (month + 1) % 12  # 寅月=1, 卯月=2, ...

    return year + year_offset, year_offset


def calculate_day_gz(year: int, month: int, day: int, hour: int) -> Tuple[str, str, str, str]:
    """
    计算日柱、月柱、年柱、时柱
    《穷通宝鉴》核心：以日为主，以月为令

    【2026-08 修正】
    - 日柱：权威锚点 2000-01-01 0h = 戊午（原为 2000-01-01 辛巳，错 1 位且基准时刻差 1 天）
    - 年柱：按立春精确时刻分界（原按 (year-4) 不分界，立春前出生会错一年）
    - 月柱：以十二节定月支（原简化按公历月，(month+1)%12 错）

    Returns: (年柱, 月柱, 日柱, 时柱) 元组
    """
    # 日柱计算（基于儒略日，锚点 2000-01-01 0h = 戊午）
    target_jd = _julian_day(year, month, day)
    base_jd = 2451544.5  # 2000-01-01 0h
    base_day_gan = 4  # 戊
    base_day_zhi = 6  # 午
    days_diff = int(target_jd - base_jd)

    day_gan_index = (base_day_gan + days_diff) % 10
    day_zhi_index = (base_day_zhi + days_diff) % 12
    day_pillar = TIANGAN[day_gan_index] + DIZHI[day_zhi_index]

    # 年柱（《渊海子平》：立春为年柱分界，按精确时刻）
    birth_dt = datetime(year, month, day, hour)
    lichun = get_jieqi_datetime(year, '立春')
    eff_year = year if birth_dt >= lichun else year - 1
    year_gan_index = (eff_year - 4) % 10
    year_zhi_index = (eff_year - 4) % 12
    year_pillar = TIANGAN[year_gan_index] + DIZHI[year_zhi_index]

    # 月柱（以十二节定月支 + 五虎遁定月干）
    jq = check_jieqi_boundary(birth_dt)
    month_zhi = jq['di_zhi']
    month_num = jq['lunar_month']  # 寅=1 ... 丑=12
    month_zhi_index = (DIZHI.index(month_zhi)) % 12
    # 五虎遁起月法：甲己之年丙作首，乙庚之年戊为头，丙辛必定寻庚起，丁壬壬位顺行流，戊癸之年何方发，甲寅之上好追求
    month_stem_table = {
        0: 2, 5: 2,  # 甲、己 -> 丙寅
        1: 4, 6: 4,  # 乙、庚 -> 戊寅
        2: 6, 7: 6,  # 丙、辛 -> 庚寅
        3: 8, 8: 8,  # 丁、壬 -> 壬寅
        4: 0, 9: 0   # 戊、癸 -> 甲寅
    }
    month_stem_index = (month_stem_table[year_gan_index] + (month_num - 1)) % 10
    month_pillar = TIANGAN[month_stem_index] + month_zhi

    # 时柱（五鼠遁起时法）
    # 甲己还加甲，乙庚丙作初，丙辛从戊起，丁壬庚子居，戊癸何方发，壬子是真途
    # 时辰分界：23-1 子，1-3 丑…… 13-15 未，15-17 申（整点 = 新时辰起点）
    hour_zhi_index = int((hour + 1) / 2) % 12

    # 晚子时（夜子时 23:00-23:59）：时支仍为子，时干须按「次日」日干遁。
    # 【流派声明】子时有「换日 / 不换日」两派，本实现采夜子时通例：
    #   日柱仍属当日，时柱用次日子时遁干。文档已声明，勿在未告知的情况下更改。
    if hour >= 23:
        next_days_diff = days_diff + 1
        gan_for_hour = (base_day_gan + next_days_diff) % 10   # 次日日干
    else:
        gan_for_hour = day_gan_index

    hour_stem_table = {
        0: 0, 5: 0,  # 甲、己 -> 甲子
        1: 2, 6: 2,  # 乙、庚 -> 丙子
        2: 4, 7: 4,  # 丙、辛 -> 戊子
        3: 6, 8: 6,  # 丁、壬 -> 庚子
        4: 8, 9: 8   # 戊、癸 -> 壬子
    }
    hour_stem_index = (hour_stem_table[gan_for_hour] + hour_zhi_index) % 10
    hour_pillar = TIANGAN[hour_stem_index] + DIZHI[hour_zhi_index]

    return year_pillar, month_pillar, day_pillar, hour_pillar


def calculate_day_master_strength(bazi: Dict, birth_date: datetime) -> Dict:
    """
    计算日主强弱
    《滴天髓》核心：论命以日主为核心，辨其旺衰

    Returns: 日主五行、强弱、旺相休囚死、用神建议
    """
    day_gan = bazi['日柱'][0]
    day_zhi = bazi['日柱'][1]
    day_wuxing = WUXING_TIAN[day_gan]

    # 出生月份（节气月）
    birth_month = birth_date.month

    # 月令旺衰表（《穷通宝鉴》体系）
    # 月令五行与日主五行关系
    # 同我者为旺，我生者为相，生我者为休，克我者为囚，我克者为死

    wuxing_cycle = ['木', '火', '土', '金', '水']
    wuxing_relations = {
        '木': {'木': '旺', '火': '相', '水': '休', '金': '囚', '土': '死'},
        '火': {'木': '死', '火': '旺', '土': '相', '水': '休', '金': '囚'},
        '土': {'木': '囚', '火': '死', '土': '旺', '金': '相', '水': '休'},
        '金': {'木': '休', '火': '囚', '土': '死', '金': '旺', '水': '相'},
        '水': {'木': '相', '火': '休', '土': '囚', '金': '死', '水': '旺'}
    }

    # 月令五行
    month_wuxing_map = {2: '木', 3: '木', 4: '火', 5: '火', 6: '火',
                         7: '土', 8: '土', 9: '金', 10: '金', 11: '金', 12: '水', 1: '水'}
    month_wuxing = month_wuxing_map[birth_month]

    # 计算得令程度
    # 月令得令 + 地支通根 + 天干透出
    strength = 0

    # 1. 月令（最重要）
    if wuxing_relations[day_wuxing][month_wuxing] == '旺':
        strength += 40
    elif wuxing_relations[day_wuxing][month_wuxing] == '相':
        strength += 30
    elif wuxing_relations[day_wuxing][month_wuxing] == '休':
        strength += 20
    elif wuxing_relations[day_wuxing][month_wuxing] == '囚':
        strength += 10
    else:  # 死
        strength += 0

    # 2. 时支
    hour_zhi = bazi['时柱'][1]
    if WUXING_ZHI[hour_zhi] == day_wuxing:
        strength += 15

    # 3. 日支
    if WUXING_ZHI[day_zhi] == day_wuxing:
        strength += 20

    # 4. 天干得地支生扶
    for pillar_name in ['年柱', '月柱', '时柱']:
        pillar_gan = bazi[pillar_name][0]
        pillar_zhi = bazi[pillar_name][1]
        if WUXING_TIAN[pillar_gan] == day_wuxing:
            strength += 10
        if WUXING_ZHI[pillar_zhi] == day_wuxing:
            strength += 5

    # 5. 克泄耗
    for pillar_name in ['年柱', '月柱', '时柱']:
        pillar_gan = bazi[pillar_name][0]
        pillar_zhi = bazi[pillar_name][1]
        wuxing = WUXING_TIAN[pillar_gan]
        # 木克土，土克水，水克火，火克金，金克木
        ke_zhi = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
        xie_zhi = {'木': '水', '土': '木', '金': '土', '火': '金', '水': '火'}
        if ke_zhi[day_wuxing] == wuxing:
            strength -= 10
        elif xie_zhi[day_wuxing] == wuxing:
            strength -= 5

    # 判断强弱
    if strength >= 60:
        level = '强'
        need = '克泄耗'
        suggest = '用神宜泄不宜补'
    elif strength >= 40:
        level = '偏强'
        need = '克泄'
        suggest = '用神宜克泄'
    elif strength >= 25:
        level = '中和'
        need = '平衡'
        suggest = '用神需视全局而定'
    elif strength >= 10:
        level = '偏弱'
        need = '生扶'
        suggest = '用神宜生扶'
    else:
        level = '弱'
        need = '生扶助'
        suggest = '用神宜生扶助'

    return {
        '日主': day_gan,
        '日主五行': day_wuxing,
        '日主阴阳': YINYANG_TIAN[day_gan],
        '月令': month_wuxing,
        '得令程度': strength,
        '强弱判断': level,
        '用神需求': need,
        '用神建议': suggest
    }


def calculate_shishen(bazi: Dict) -> Dict:
    """
    计算十神
    《渊海子平》核心：十神体系
    """
    day_gan = bazi['日柱'][0]

    shishen = {}
    for pillar_name in ['年柱', '月柱', '时柱']:
        stem = bazi[pillar_name][0]
        stem_wuxing = WUXING_TIAN[stem]
        day_wuxing = WUXING_TIAN[day_gan]

        # 生我者为印，我生者为食伤
        # 克我者为官，我克者为财
        # 同我者为比劫

        if stem_wuxing == day_wuxing:
            # 比肩/劫财
            if YINYANG_TIAN[stem] == YINYANG_TIAN[day_gan]:
                relation = '比肩'
            else:
                relation = '劫财'
        elif (stem_wuxing == '木' and day_wuxing == '火') or (stem_wuxing == '火' and day_wuxing == '土') or \
             (stem_wuxing == '土' and day_wuxing == '金') or (stem_wuxing == '金' and day_wuxing == '水') or \
             (stem_wuxing == '水' and day_wuxing == '木'):
            # 食神/伤官
            if (stem_wuxing == '木' and YINYANG_TIAN[stem] == '阴') or \
               (stem_wuxing == '火' and YINYANG_TIAN[stem] == '阴') or \
               (stem_wuxing == '土' and YINYANG_TIAN[stem] == '阴') or \
               (stem_wuxing == '金' and YINYANG_TIAN[stem] == '阴') or \
               (stem_wuxing == '水' and YINYANG_TIAN[stem] == '阴'):
                relation = '伤官'
            else:
                relation = '食神'
        elif (stem_wuxing == '木' and day_wuxing == '土') or (stem_wuxing == '火' and day_wuxing == '金') or \
             (stem_wuxing == '土' and day_wuxing == '水') or (stem_wuxing == '金' and day_wuxing == '木') or \
             (stem_wuxing == '水' and day_wuxing == '火'):
            # 正财/偏财
            if (stem_wuxing == '木' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '火' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '土' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '金' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '水' and YINYANG_TIAN[stem] == '阳'):
                relation = '偏财'
            else:
                relation = '正财'
        elif (stem_wuxing == '木' and day_wuxing == '金') or (stem_wuxing == '火' and day_wuxing == '水') or \
             (stem_wuxing == '土' and day_wuxing == '木') or (stem_wuxing == '金' and day_wuxing == '火') or \
             (stem_wuxing == '水' and day_wuxing == '土'):
            # 正官/七杀
            if (stem_wuxing == '木' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '火' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '土' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '金' and YINYANG_TIAN[stem] == '阳') or \
               (stem_wuxing == '水' and YINYANG_TIAN[stem] == '阳'):
                relation = '七杀'
            else:
                relation = '正官'
        else:  # 生我者
            if YINYANG_TIAN[stem] == YINYANG_TIAN[day_gan]:
                relation = '偏印'
            else:
                relation = '正印'

        shishen[pillar_name] = {
            '天干': stem,
            '十神': relation,
            '五行': stem_wuxing,
            '阴阳': YINYANG_TIAN[stem],
            '藏干': ZANGGAN[bazi[pillar_name][1]]
        }

    # 日支藏干十神
    day_zhi = bazi['日柱'][1]
    day_zhi_gans = ZANGGAN[day_zhi]
    day_zhi_shishen = []
    for i, zg in enumerate(day_zhi_gans):
        zg_wuxing = WUXING_TIAN[zg]
        # 判断藏干与日主关系
        if zg_wuxing == day_wuxing:
            rel = '比肩' if YINYANG_TIAN[zg] == YINYANG_TIAN[day_gan] else '劫财'
        elif (zg_wuxing == '木' and day_wuxing == '火') or (zg_wuxing == '火' and day_wuxing == '土') or \
             (zg_wuxing == '土' and day_wuxing == '金') or (zg_wuxing == '金' and day_wuxing == '水') or \
             (zg_wuxing == '水' and day_wuxing == '木'):
            rel = '伤官' if YINYANG_TIAN[zg] == '阴' else '食神'
        elif (zg_wuxing == '木' and day_wuxing == '土') or (zg_wuxing == '火' and day_wuxing == '金') or \
             (zg_wuxing == '土' and day_wuxing == '水') or (zg_wuxing == '金' and day_wuxing == '木') or \
             (zg_wuxing == '水' and day_wuxing == '火'):
            rel = '偏财' if YINYANG_TIAN[zg] == '阳' else '正财'
        elif (zg_wuxing == '木' and day_wuxing == '金') or (zg_wuxing == '火' and day_wuxing == '水') or \
             (zg_wuxing == '土' and day_wuxing == '木') or (zg_wuxing == '金' and day_wuxing == '火') or \
             (zg_wuxing == '水' and day_wuxing == '土'):
            rel = '七杀' if YINYANG_TIAN[zg] == '阳' else '正官'
        else:
            rel = '偏印' if YINYANG_TIAN[zg] == YINYANG_TIAN[day_gan] else '正印'
        day_zhi_shishen.append({'藏干': zg, '十神': rel})

    shishen['日支藏干'] = day_zhi_shishen

    return shishen


def calculate_dayun(bazi: Dict, birth_year: int, current_year: int, gender: str) -> List[Dict]:
    """
    计算大运
    《子平真诠》：大运以月柱为基础，顺逆排布
    """
    month_zhi = bazi['月柱'][1]
    month_zhi_index = DIZHI.index(month_zhi)

    # 大运起始年龄（简化：通常从3-8岁开始）
    # 根据月柱地支确定大运方向
    # 阳年男/阴年女：顺排（地支顺序）
    # 阴年男/阳年女：逆排（地支逆序）

    year_yang = YINYANG_TIAN[bazi['年柱'][0]] == '阳'

    if (gender == '男' and year_yang) or (gender == '女' and not year_yang):
        # 顺行
        direction = 1
    else:
        # 逆行
        direction = -1

    # 大运起运年龄（简化计算）
    start_age = 3  # 默认3岁起运

    dayun_list = []
    gan_index_base = TIANGAN.index(bazi['月柱'][0])
    zhi_index_base = month_zhi_index

    for i in range(0, 10):
        zhi_index = (zhi_index_base + (i + 1) * direction) % 12
        zhi = DIZHI[zhi_index]

        # 天干顺逆排
        gan_index = (gan_index_base + (i + 1) * direction) % 10
        gan = TIANGAN[gan_index]

        dayun_list.append({
            '序号': i + 1,
            '年龄': f'{start_age + i * 10}-{start_age + i * 10 + 9}岁',
            '大运': gan + zhi,
            '天干': gan,
            '地支': zhi,
            '天干五行': WUXING_TIAN[gan],
            '地支五行': WUXING_ZHI[zhi]
        })

    return dayun_list


def calculate_liunian(bazi: Dict, target_year: int, current_year: int) -> Dict:
    """
    计算流年
    《滴天髓》：流年重在天干与命局的生克冲合
    """
    year_gan = TIANGAN[(target_year - 4) % 10]
    year_zhi = DIZHI[(target_year - 4) % 12]
    year_wuxing = WUXING_TIAN[year_gan]

    # 流年与命局的关系
    day_gan = bazi['日柱'][0]

    # 天干生克
    sheng_ke = calculate_shengke(WUXING_TIAN[year_gan], WUXING_TIAN[day_gan])

    return {
        '流年': year_gan + year_zhi,
        '天干': year_gan,
        '地支': year_zhi,
        '天干五行': year_wuxing,
        '天干阴阳': YINYANG_TIAN[year_gan],
        '地支阴阳': YINYANG_ZHI[year_zhi],
        '与日主生克': sheng_ke
    }


def calculate_shengke(w1: str, w2: str) -> str:
    """计算五行生克关系"""
    # 木生火，火生土，土生金，金生水，水生木
    # 木克土，土克水，水克火，火克金，金克木
    sheng = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

    if sheng.get(w1) == w2:
        return '生'
    elif ke.get(w1) == w2:
        return '克'
    elif sheng.get(w2) == w1:
        return '被生'
    elif ke.get(w2) == w1:
        return '被克'
    else:
        return '同'


def format_bazi_report(bazi: Dict, day_master: Dict, shishen: Dict, dayun: List, liunian: Dict) -> str:
    """
    格式化输出八字报告
    整合《渊海子平》《三命通会》《滴天髓》理论
    """
    report = []
    report.append("=" * 60)
    report.append("【八字命盘】")
    report.append("=" * 60)
    report.append(f"年柱：{bazi['年柱']}（{YINYANG_TIAN[bazi['年柱'][0]]}）")
    report.append(f"月柱：{bazi['月柱']}（{YINYANG_TIAN[bazi['月柱'][0]]}）")
    report.append(f"日柱：{bazi['日柱']}（{YINYANG_TIAN[bazi['日柱'][0]]}）")
    report.append(f"时柱：{bazi['时柱']}（{YINYANG_TIAN[bazi['时柱'][0]]}）")
    report.append("")

    report.append("【十神体系】《渊海子平》")
    for pillar in ['年柱', '月柱', '时柱']:
        info = shishen[pillar]
        report.append(f"  {pillar}：{info['天干']} → {info['十神']}（{info['五行']}{info['阴阳']}）")
    report.append("  日支藏干：")
    for info in shishen['日支藏干']:
        report.append(f"    {info['藏干']} → {info['十神']}")
    report.append("")

    report.append("【日主分析】《滴天髓》")
    report.append(f"  日主：{day_master['日主']}{day_master['日主阴阳']}")
    report.append(f"  五行：{day_master['日主五行']}")
    report.append(f"  月令：{day_master['月令']}")
    report.append(f"  得令程度：{day_master['得令程度']}分")
    report.append(f"  强弱判断：{day_master['强弱判断']}")
    report.append(f"  用神建议：{day_master['用神建议']}")
    report.append("")

    report.append("【大运走势】《子平真诠》")
    for d in dayun[:5]:  # 只显示前5步大运
        report.append(f"  {d['年龄']}：{d['大运']}（{d['天干五行']}/{d['地支五行']}）")
    report.append("")

    report.append("【流年分析】")
    report.append(f"  {liunian['流年']}年（{liunian['天干']}{liunian['地支']}）")
    report.append(f"  天干{liunian['天干']}（{liunian['天干五行']}{liunian['天干阴阳']}）")
    report.append(f"  与日主关系：{liunian['与日主生克']}")
    report.append("")

    return "\n".join(report)


def main():
    """主函数：接收用户输入，输出八字命盘"""
    import sys

    # 统一错误输出格式
    def error_response(code, details):
        return {"success": False, "error": {"code": code, "details": details if isinstance(details, list) else [details]}}

    # 帮助信息
    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("八字排盘工具 v2.0")
        print("用法: python bazi.py <年> <月> <日> <时> [性别:男/女]")
        print("示例:")
        print("  python bazi.py 1993 6 18 15 女")
        print("  python bazi.py 2000 1 1 12 男")
        print("\n参数:")
        print("  年   出生年份（1900-2100）")
        print("  月   出生月份（1-12）")
        print("  日   出生日期（1-31）")
        print("  时   出生时辰（0-23）")
        print("  性别 男/女（默认男）")
        sys.exit(0)

    if len(sys.argv) < 5:
        print(json.dumps(error_response("MISSING_ARGUMENTS", "用法: python bazi.py <年> <月> <日> <时> [性别:男/女]"), ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
    except ValueError as e:
        print(json.dumps(error_response("INVALID_NUMBER", f"参数必须为整数: {e}"), ensure_ascii=False, indent=2))
        sys.exit(2)

    gender = sys.argv[5] if len(sys.argv) > 5 else '男'

    # 输入校验（返回结构化错误）
    from p0_validators import _valid_date
    verrs = _valid_date(year, month, day, hour)
    if verrs:
        print(json.dumps(error_response("INVALID_INPUT", verrs), ensure_ascii=False, indent=2))
        sys.exit(2)
    if gender not in ('男', '女'):
        print(json.dumps(error_response("INVALID_GENDER", f"性别必须为男或女，收到 {gender}"), ensure_ascii=False, indent=2))
        sys.exit(2)

    birth_date = datetime(year, month, day, hour)

    # 计算四柱
    nianzhu, yuezhu, rizhu, shizhu = calculate_day_gz(year, month, day, hour)

    bazi = {
        '年柱': nianzhu,
        '月柱': yuezhu,
        '日柱': rizhu,
        '时柱': shizhu
    }

    # 计算日主强弱
    day_master = calculate_day_master_strength(bazi, birth_date)

    # 计算十神
    shishen = calculate_shishen(bazi)

    # 计算大运
    dayun = calculate_dayun(bazi, year, datetime.now().year, gender)

    # 计算流年
    current_year = datetime.now().year
    liunian = calculate_liunian(bazi, current_year, year)

    # 输出报告
    report = format_bazi_report(bazi, day_master, shishen, dayun, liunian)
    print(report)

    # 输出JSON格式（统一格式）
    result = {
        'bazi': bazi,
        'day_master': day_master,
        'shishen': {k: v for k, v in shishen.items() if k != '日支藏干'},
        'dayun': dayun,
        'liunian': liunian,
        'day_zhi_gans': shishen.get('日支藏干', [])
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
