#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奇门遁甲排盘工具 v1.0

典籍依据（SKILL.md「六、奇门遁甲 — 典籍规则表」）：
- 《烟波钓叟歌》          定局：阳遁冬至→芒种顺排，阴遁夏至→大雪逆排
- 《奇门遁甲全书·超神接气章》 符头定局：三元分上中下（子午卯酉上元，寅申巳亥中元，辰戌丑未下元）
- 《烟波钓叟歌·八门章》    八门：休生伤杜景死惊开，各有吉凶方位
- 《奇门遁甲全书·九星章》  九星：天蓬(兵)天芮(师)天冲(战)天辅(教)天禽(中)天心(医)天柱(守)天任(官)天英(火)
- 《烟波钓叟歌·三奇章》   三奇：乙奇日奇(主文)、丙奇月奇(主武)、丁奇星奇(主冥)

实现说明：
  1. 阳遁/阴遁按节气日历定；每节气分上中下三元，每元5天
  2. 地盘按局数排六仪三奇（阳遁顺排、阴遁逆排）
  3. 天盘值符随时干
  4. 八门值使随时支
  5. 超神接气暂不实现（基础版不处理符头偏移）
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple

from p0_validators import get_jieqi_datetime

# ==================== 常量 ====================

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 九宫（后天八卦数）：1坎 2坤 3震 4巽 5中 6乾 7兑 8艮 9离
JIUGONG = {1: '坎', 2: '坤', 3: '震', 4: '巽', 5: '中', 6: '乾', 7: '兑', 8: '艮', 9: '离'}
JIUGONG_WX = {1: '水', 2: '土', 3: '木', 4: '木', 5: '土', 6: '金', 7: '金', 8: '土', 9: '火'}

# 六仪三奇顺序（甲子→甲戌→甲申→甲午→甲辰→甲寅→丁→丙→乙）
LIUYI_SQI = ['戊', '己', '庚', '辛', '壬', '癸', '丁', '丙', '乙']

# 八门：门名 → 固定原始宫位
BAMEN_ORIGINAL = {'休': 1, '死': 2, '伤': 3, '杜': 4, '景': 9, '惊': 7, '开': 6, '生': 8}
BAMEN_LIST = ['休', '生', '伤', '杜', '景', '死', '惊', '开']
BAMEN_JIXIONG = {'休': '吉', '生': '大吉', '伤': '凶', '杜': '平',
                 '景': '平', '死': '大凶', '惊': '凶', '开': '吉'}

# 九星：星名 → 固定原始宫位
JIUXING_ORIGINAL = {'天蓬': 1, '天芮': 2, '天冲': 3, '天辅': 4,
                     '天禽': 5, '天心': 6, '天柱': 7, '天任': 8, '天英': 9}
JIUXING_LIST = ['天蓬', '天芮', '天冲', '天辅', '天禽', '天心', '天柱', '天任', '天英']
JIUXING_JIXIONG = {'天蓬': '凶', '天芮': '凶', '天冲': '平', '天辅': '吉',
                   '天禽': '吉', '天心': '大吉', '天柱': '凶', '天任': '吉', '天英': '平'}

# 八神
BASHEN = ['值符', '螣蛇', '太阴', '六合', '白虎', '玄武', '九地', '九天']

# ==================== 节气局数表 ====================
# 格式：{节气: (遁类型, 上元局, 中元局, 下元局)}
# 阳遁=1, 阴遁=-1

JIEQI_JU = {
    # 阳遁
    '冬至': (1, 1, 4, 7), '小寒': (1, 2, 5, 8), '大寒': (1, 3, 6, 9),
    '立春': (1, 8, 5, 2), '雨水': (1, 9, 6, 3), '惊蛰': (1, 1, 4, 7),
    '春分': (1, 3, 6, 9), '清明': (1, 4, 7, 1), '谷雨': (1, 5, 8, 2),
    '立夏': (1, 4, 7, 1), '小满': (1, 5, 8, 2), '芒种': (1, 6, 9, 3),
    # 阴遁
    '夏至': (-1, 9, 3, 6), '小暑': (-1, 8, 2, 5), '大暑': (-1, 7, 1, 4),
    '立秋': (-1, 2, 5, 8), '处暑': (-1, 1, 4, 7), '白露': (-1, 9, 3, 6),
    '秋分': (-1, 7, 1, 4), '寒露': (-1, 6, 9, 3), '霜降': (-1, 5, 8, 2),
    '立冬': (-1, 6, 9, 3), '小雪': (-1, 5, 8, 2), '大雪': (-1, 4, 7, 1),
}

JIEQI_ORDER = [
    '冬至', '小寒', '大寒', '立春', '雨水', '惊蛰',
    '春分', '清明', '谷雨', '立夏', '小满', '芒种',
    '夏至', '小暑', '大暑', '立秋', '处暑', '白露',
    '秋分', '寒露', '霜降', '立冬', '小雪', '大雪',
]

JIEQI_FENJIE = {
    '冬至': 12, '小寒': 1, '大寒': 1,
    '立春': 2, '雨水': 2, '惊蛰': 3,
    '春分': 3, '清明': 4, '谷雨': 4,
    '立夏': 5, '小满': 5, '芒种': 6,
    '夏至': 6, '小暑': 7, '大暑': 7,
    '立秋': 8, '处暑': 8, '白露': 9,
    '秋分': 9, '寒露': 10, '霜降': 10,
    '立冬': 11, '小雪': 11, '大雪': 12,
}


# ==================== 定局 ====================

def _ganzhi_index(gan: str, zhi: str) -> int:
    g, z = TIANGAN.index(gan), DIZHI.index(zhi)
    for i in range(60):
        if i % 10 == g and i % 12 == z:
            return i
    return -1


def _day_ganzhi(year: int, month: int, day: int) -> Tuple[str, str]:
    from liuyao import calculate_day_ganzhi
    return calculate_day_ganzhi(year, month, day)


def get_jieqi_and_yuan(year: int, month: int, day: int) -> Tuple[str, int, int]:
    """
    确定当前日期所在节气及元。
    返回 (节气名, 元序号0/1/2, 局数)
    """
    target = datetime(year, month, day)
    jieqi_times = []
    for name in JIEQI_ORDER:
        try:
            dt = get_jieqi_datetime(year, name)
            if dt:
                jieqi_times.append((name, dt))
        except:
            pass
        # 也查上一年末尾的节气（冬至/大雪可能在上一年12月）
        try:
            dt_prev = get_jieqi_datetime(year - 1, name)
            if dt_prev and dt_prev.year == year - 1:
                jieqi_times.append((name + '_prev', dt_prev))
        except:
            pass

    jieqi_times.sort(key=lambda x: x[1])

    # 找当前所在的节气区间
    current_jieqi = None
    for i, (name, dt) in enumerate(jieqi_times):
        clean_name = name.replace('_prev', '')
        if i + 1 < len(jieqi_times):
            next_dt = jieqi_times[i + 1][1]
            if dt <= target < next_dt:
                current_jieqi = clean_name
                break
        else:
            if dt <= target:
                current_jieqi = clean_name
                break

    if current_jieqi is None:
        # 默认：阳遁1局
        return '冬至', 0, 1

    dun_type, ju_up, ju_mid, ju_low = JIEQI_JU[current_jieqi]

    # 计算日柱符头，确定三元
    gan_zhi = _day_ganzhi(year, month, day)
    gt_idx = _ganzhi_index(gan_zhi[0], gan_zhi[1])
    # 子午卯酉=上元(0)，寅申巳亥=中元(1)，辰戌丑未=下元(2)
    zhi = gan_zhi[1]
    if zhi in ('子', '午', '卯', '酉'):
        yuan = 0
    elif zhi in ('寅', '申', '巳', '亥'):
        yuan = 1
    else:
        yuan = 2

    ju = [ju_up, ju_mid, ju_low][yuan]
    return current_jieqi, yuan, ju


def get_dun_type(year: int, month: int, day: int) -> int:
    """返回遁类型：1=阳遁，-1=阴遁"""
    jieqi, _, _ = get_jieqi_and_yuan(year, month, day)
    return JIEQI_JU[jieqi][0]


# ==================== 排盘 ====================

def pai_dipan(dun_type: int, ju: int) -> Dict[int, str]:
    """
    排地盘：按局数排六仪三奇到九宫。
    阳遁从ju宫起戊顺排；阴遁从ju宫起戊逆排。
    """
    gongs = list(range(1, 10))
    if dun_type == 1:  # 阳遁顺排
        ordered = []
        idx = ju - 1
        for _ in range(9):
            ordered.append(gongs[idx])
            idx = (idx + 1) % 9
    else:  # 阴遁逆排
        ordered = []
        idx = ju - 1
        for _ in range(9):
            ordered.append(gongs[idx])
            idx = (idx - 1) % 9

    result = {}
    for i, gong in enumerate(ordered):
        result[gong] = LIUYI_SQI[i]
    return result


def pai_tianpan(dun_type: int, ju: int, hour_gan: str,
                dipan: Dict[int, str]) -> Dict[int, str]:
    """
    排天盘：值符（时干）加临地盘时干所在宫。
    简化实现：时干在地盘哪宫，就把该宫干提到时干宫，其余按相对位置排。
    """
    # 找时干在地盘的宫位
    target_gong = None
    for gong, gan in dipan.items():
        if gan == hour_gan:
            target_gong = gong
            break
    if target_gong is None:
        target_gong = 1

    # 值符原始宫位（按地盘该宫对应九星）
    zhifu_gong = target_gong

    # 天盘：值符宫的干加到时干宫（target_gong），其余按相对位置顺/逆排
    result = {}
    if dun_type == 1:
        offset = target_gong - zhifu_gong
        for gong in range(1, 10):
            src = ((gong - 1 - offset) % 9) + 1
            result[gong] = dipan.get(src, '戊')
    else:
        offset = zhifu_gong - target_gong
        for gong in range(1, 10):
            src = ((gong - 1 + offset) % 9) + 1
            result[gong] = dipan.get(src, '戊')
    return result


def pai_bamen(dun_type: int, ju: int, hour_zhi_idx: int) -> Dict[int, str]:
    """
    排八门：值使门（开门）按局数和时支排布。
    简化：值使门随局数起始宫，按时支数顺/逆排到时支宫。
    """
    # 值使门=开门，原始宫6
    start_gong = 6
    if dun_type == 1:
        gong = ((start_gong - 1 + hour_zhi_idx) % 9) + 1
    else:
        gong = ((start_gong - 1 - hour_zhi_idx) % 9) + 1

    # 八门依次从值使宫排起
    result = {}
    for i, men in enumerate(BAMEN_LIST):
        g = ((gong - 1 + i) % 9) + 1 if dun_type == 1 else ((gong - 1 - i) % 9) + 1
        result[g] = men
    return result


def pai_jiuxing(dun_type: int, ju: int, hour_zhi_idx: int) -> Dict[int, str]:
    """
    排九星：值符星（天蓬）按局数和时支排布。
    """
    start_gong = 1  # 天蓬原始宫1
    if dun_type == 1:
        gong = ((start_gong - 1 + hour_zhi_idx) % 9) + 1
    else:
        gong = ((start_gong - 1 - hour_zhi_idx) % 9) + 1

    result = {}
    for i, star in enumerate(JIUXING_LIST):
        g = ((gong - 1 + i) % 9) + 1 if dun_type == 1 else ((gong - 1 - i) % 9) + 1
        result[g] = star
    return result


def pai_bashen(dun_type: int, ju: int, hour_zhi_idx: int) -> Dict[int, str]:
    """排八神：值符起始宫按局数排"""
    start_gong = ju
    if dun_type == 1:
        gong = ((start_gong - 1 + hour_zhi_idx) % 9) + 1
    else:
        gong = ((start_gong - 1 - hour_zhi_idx) % 9) + 1

    result = {}
    for i, shen in enumerate(BASHEN):
        g = ((gong - 1 + i) % 9) + 1 if dun_type == 1 else ((gong - 1 - i) % 9) + 1
        result[g] = shen
    return result


# ==================== 排盘主函数 ====================

def pan(year: int, month: int, day: int, hour: int) -> Dict:
    """奇门遁甲完整排盘"""
    hour_zhi_idx = int((hour + 1) / 2) % 12   # 子=0
    hour_zhi = DIZHI[hour_zhi_idx]

    jieqi, yuan, ju = get_jieqi_and_yuan(year, month, day)
    dun_type = JIEQI_JU[jieqi][0]
    dun_name = '阳遁' if dun_type == 1 else '阴遁'
    yuan_name = ['上元', '中元', '下元'][yuan]

    from liuyao import calculate_day_ganzhi
    day_gan, day_zhi = calculate_day_ganzhi(year, month, day)
    hour_gan_idx = (TIANGAN.index(day_gan) % 5 * 2 + hour_zhi_idx) % 10
    hour_gan = TIANGAN[hour_gan_idx]

    dipan = pai_dipan(dun_type, ju)
    tianpan = pai_tianpan(dun_type, ju, hour_gan, dipan)
    bamen = pai_bamen(dun_type, ju, hour_zhi_idx)
    jiuxing = pai_jiuxing(dun_type, ju, hour_zhi_idx)
    bashen = pai_bashen(dun_type, ju, hour_zhi_idx)

    return {
        'dun_type': dun_name, 'ju': ju, 'yuan': yuan_name,
        'jieqi': jieqi,
        'year_ganzhi': f"{TIANGAN[(year - 4) % 10]}{DIZHI[(year - 4) % 12]}",
        'day_ganzhi': day_gan + day_zhi,
        'hour_ganzhi': hour_gan + hour_zhi,
        'hour_zhi': hour_zhi,
        'dipan': dipan, 'tianpan': tianpan,
        'bamen': bamen, 'jiuxing': jiuxing, 'bashen': bashen,
    }


def format_report(p: Dict) -> str:
    out = []
    out.append("=" * 58)
    out.append("【奇门遁甲 · 排盘】")
    out.append("=" * 58)
    out.append(f"  {p['dun_type']}{p['ju']}局 · {p['yuan']}　节气：{p['jieqi']}")
    out.append(f"  年柱：{p['year_ganzhi']}　日柱：{p['day_ganzhi']}　时柱：{p['hour_ganzhi']}")
    out.append("")
    out.append("【九宫格局】")
    out.append(f"  {'宫':<4}{'地盘':<6}{'天盘':<6}{'八门':<6}{'九星':<8}{'八神':<6}")
    out.append("  " + "-" * 40)
    for gong in range(1, 10):
        name = JIUGONG[gong]
        dp = p['dipan'].get(gong, '')
        tp = p['tianpan'].get(gong, '')
        men = p['bamen'].get(gong, '')
        star = p['jiuxing'].get(gong, '')
        shen = p['bashen'].get(gong, '')
        men吉 = BAMEN_JIXIONG.get(men, '')
        star吉 = JIUXING_JIXIONG.get(star, '')
        out.append(f"  {gong}({name}) {dp:<6}{tp:<6}{men}({men吉}) {star}({star吉}) {shen}")
    out.append("")
    out.append("【吉门】" + '、'.join(
        f"{m}({BAMEN_JIXIONG[m]})" for m in ['休', '生', '开'] if BAMEN_JIXIONG[m] == '吉'))
    out.append("【凶门】" + '、'.join(
        f"{m}({BAMEN_JIXIONG[m]})" for m in BAMEN_LIST if '凶' in BAMEN_JIXIONG[m]))
    out.append("【吉星】" + '、'.join(
        f"{s}({JIUXING_JIXIONG[s]})" for s in JIUXING_LIST if '吉' in JIUXING_JIXIONG[s]))
    out.append("")
    out.append("【八门吉凶】《烟波钓叟歌·八门章》")
    out.append("  休门吉(求财)、生门大吉(创业)、开门吉(求职/出行)")
    out.append("  伤门凶(诉讼/索债)、杜门平(藏匿)、景门平(文书)")
    out.append("  死门大凶(丧葬/诉讼)、惊门凶(惊恐/官讼)")
    return "\n".join(out)


# ==================== 主函数 ====================

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("奇门遁甲排盘工具 v1.0（《烟波钓叟歌》定局排盘）")
        print("用法: python qimen.py <年> <月> <日> <时>")
        print("示例:")
        print("  python qimen.py 2026 9 3 10")
        print("  python qimen.py 2026 2 4 15")
        sys.exit(0)

    if len(sys.argv) < 5:
        print(json.dumps(error_response("MISSING_ARGUMENTS",
                                        "用法: python qimen.py <年> <月> <日> <时>"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        y, m, d, h = (int(sys.argv[i]) for i in (1, 2, 3, 4))
    except ValueError as e:
        print(json.dumps(error_response("INVALID_NUMBER", f"参数必须为整数: {e}"),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    from p0_validators import _valid_date
    verrs = _valid_date(y, m, d, h)
    if verrs:
        print(json.dumps(error_response("INVALID_INPUT", verrs),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    p = pan(y, m, d, h)
    print(format_report(p))

    result = {
        'dun_type': p['dun_type'], 'ju': p['ju'], 'yuan': p['yuan'],
        'jieqi': p['jieqi'],
        'hour_ganzhi': p['hour_ganzhi'],
        'dipan': {JIUGONG[g]: p['dipan'].get(g, '') for g in range(1, 10)},
        'tianpan': {JIUGONG[g]: p['tianpan'].get(g, '') for g in range(1, 10)},
        'bamen': {JIUGONG[g]: {'门': p['bamen'].get(g, ''),
                               '吉凶': BAMEN_JIXIONG.get(p['bamen'].get(g, ''), '')}
                  for g in range(1, 10)},
        'jiuxing': {JIUGONG[g]: {'星': p['jiuxing'].get(g, ''),
                                  '吉凶': JIUXING_JIXIONG.get(p['jiuxing'].get(g, ''), '')}
                    for g in range(1, 10)},
        'bashen': {JIUGONG[g]: p['bashen'].get(g, '') for g in range(1, 10)},
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
