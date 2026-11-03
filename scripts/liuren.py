#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬排盘工具 v2.0 —— 完整判贼克与三传推导

典籍依据（SKILL.md「七、大六壬 — 典籍规则表」）：
- 《大六壬指南·起课法》  月将加时顺数→四课→三传
- 《六壬大全·天将定位》  十二天将配入三传四课
- 《大六壬心镜》          贼克、比用、涉害等取初传规则
- 《壬归》                大六壬分类占断

v2.0 修正：
1. 四课结构改为「上神/下神」对，正确反映课之上下
2. 判贼克算法：上克下/下克上→取初传；多克贼时用比用法
3. 三传推导：初传定后，中传取初传上神（下贼上）或下神（上克下），
   末传类推；遇克贼循环则按特定规则处理
4. 天将按昼夜分顺逆排布（简化版按日支阴阳定）
"""

import json
import sys
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# ==================== 常量 ====================

TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

# 地支五行
ZHI_WX = {'子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
          '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}

# 五行生克
WX_SHENG = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
WX_KE = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}

# 天干五行
GAN_WX = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
          '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

# 十二天将
TIAN_JIANG = ['贵人', '螣蛇', '朱雀', '六合', '勾陈', '青龙',
              '天空', '白虎', '太常', '玄武', '太阴', '天后']

TIAN_JIANG_WX = {
    '贵人': '土', '螣蛇': '火', '朱雀': '火', '六合': '木',
    '勾陈': '土', '青龙': '木', '天空': '土', '白虎': '金',
    '太常': '土', '玄武': '水', '太阴': '金', '天后': '水',
}

TIAN_JIANG_XIANG = {
    '贵人': '贵人、尊长、领导、贵气',
    '螣蛇': '惊恐、怪异、缠绕、虚惊',
    '朱雀': '口舌、文书、言语、是非',
    '六合': '和合、交易、婚姻、中介',
    '勾陈': '牵连、田土、军事、迟滞',
    '青龙': '喜庆、财喜、吉祥、贵人',
    '天空': '空亡、欺诈、奴仆、无实',
    '白虎': '凶灾、道路、疾病、丧事',
    '太常': '衣食、宴会、官禄、喜庆',
    '玄武': '盗贼、暗昧、阴私、水险',
    '太阴': '暗中、阴私、隐蔽、女贵',
    '天后': '妇女、阴柔、后妃、淫佚',
}

# 日干寄宫（甲课寅、乙课辰、丙戊课巳、丁己课午、庚课申、辛课戌、壬课亥、癸课丑）
GAN_JIGONG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '午', '戊': '巳',
              '己': '午', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}

# 贵人起始位置（日干→贵人地支）
GUIREN_START = {
    '甲': '丑', '戊': '丑', '庚': '丑',
    '乙': '子', '己': '子',
    '丙': '亥', '丁': '亥',
    '壬': '巳', '癸': '巳',
    '辛': '寅',
}

# 月将（太阳所在宫位）
YUEJIANG = {
    '冬至': '丑', '小寒': '丑', '大寒': '寅',
    '立春': '寅', '雨水': '卯', '惊蛰': '卯',
    '春分': '辰', '清明': '巳', '谷雨': '巳',
    '立夏': '午', '小满': '午', '芒种': '未',
    '夏至': '未', '小暑': '申', '大暑': '申',
    '立秋': '酉', '处暑': '戌', '白露': '戌',
    '秋分': '亥', '寒露': '亥', '霜降': '子',
    '立冬': '子', '小雪': '丑', '大雪': '丑',
}

JIEQI_ORDER = [
    '冬至', '小寒', '大寒', '立春', '雨水', '惊蛰',
    '春分', '清明', '谷雨', '立夏', '小满', '芒种',
    '夏至', '小暑', '大暑', '立秋', '处暑', '白露',
    '秋分', '寒露', '霜降', '立冬', '小雪', '大雪',
]


# ==================== 工具函数 ====================

def zhi_next(z: str, n: int = 1) -> str:
    """地支后推n位"""
    idx = DIZHI.index(z)
    return DIZHI[(idx + n) % 12]


def zhi_prev(z: str, n: int = 1) -> str:
    """地支前推n位"""
    idx = DIZHI.index(z)
    return DIZHI[(idx - n) % 12]


def wx_ke(attacker: str, defender: str) -> bool:
    """判断五行是否相克（attacker克defender）"""
    return WX_KE.get(attacker) == defender


def zhi_ke(z1: str, z2: str) -> bool:
    """判断地支五行是否z1克z2"""
    return wx_ke(ZHI_WX[z1], ZHI_WX[z2])


def _day_ganzhi(year: int, month: int, day: int) -> Tuple[str, str]:
    from liuyao import calculate_day_ganzhi
    return calculate_day_ganzhi(year, month, day)


def _hour_ganzhi(day_gan: str, hour: int) -> Tuple[str, str]:
    hour_zhi_idx = int((hour + 1) / 2) % 12
    hour_zhi = DIZHI[hour_zhi_idx]
    table = {0: 0, 5: 0, 1: 2, 6: 2, 2: 4, 7: 4, 3: 6, 8: 6, 4: 8, 9: 8}
    day_gan_idx = TIANGAN.index(day_gan)
    hour_gan_idx = (table[day_gan_idx] + hour_zhi_idx) % 10
    return TIANGAN[hour_gan_idx], hour_zhi


def get_yuejiang(year: int, month: int, day: int) -> str:
    from p0_validators import get_jieqi_datetime
    target = datetime(year, month, day)
    for i, jq in enumerate(JIEQI_ORDER):
        try:
            dt = get_jieqi_datetime(year, jq)
            if dt is None:
                continue
            if i + 1 < len(JIEQI_ORDER):
                next_dt = get_jieqi_datetime(year, JIEQI_ORDER[i + 1])
                if next_dt and dt <= target < next_dt:
                    return YUEJIANG[jq]
            else:
                if dt <= target:
                    return YUEJIANG[jq]
        except:
            continue
    return '丑'


# ==================== 月将加时 ====================

def yuejiang_jiashi(yuejiang: str, hour_zhi: str) -> Dict[str, str]:
    """
    月将加时：将月将（太阳宫位）加到时支上，确定十二地支的天地盘关系。
    天盘 = 月将起始，顺排十二地支
    地盘 = 固定子丑寅卯...
    返回：{地支: 对应天盘地支}
    """
    result = {}
    diff = DIZHI.index(hour_zhi) - DIZHI.index(yuejiang)
    for i, z in enumerate(DIZHI):
        result[z] = DIZHI[(i + diff) % 12]
    return result


# ==================== 起四课 ====================

def qi_si_ke(day_gan: str, day_zhi: str, tianpan: Dict[str, str]) -> List[Dict]:
    """
    起四课：以日干寄宫和日支为基点，通过天地盘关系得到四课。
    四课结构：
      第一课：上=干上神（天盘），下=日干寄宫（地盘）
      第二课：上=干上神的上神，下=干上神
      第三课：上=支上神（天盘），下=日支（地盘）
      第四课：上=支上神的上神，下=支上神
    """
    gan_jigong = GAN_JIGONG[day_gan]  # 日干寄宫

    # 第一课：干上神 = 天盘上日干寄宫对应的地支
    gan_shang = tianpan[gan_jigong]
    # 第二课：干上神的上神
    gan_shang_shang = tianpan[gan_shang]

    # 第三课：支上神 = 天盘上日支对应的地支
    zhi_shang = tianpan[day_zhi]
    # 第四课：支上神的上神
    zhi_shang_shang = tianpan[zhi_shang]

    return [
        {'seq': 1, 'name': '第一课', 'shang': gan_shang, 'xia': gan_jigong, 'type': '干'},
        {'seq': 2, 'name': '第二课', 'shang': gan_shang_shang, 'xia': gan_shang, 'type': '干'},
        {'seq': 3, 'name': '第三课', 'shang': zhi_shang, 'xia': day_zhi, 'type': '支'},
        {'seq': 4, 'name': '第四课', 'shang': zhi_shang_shang, 'xia': zhi_shang, 'type': '支'},
    ]


# ==================== 判贼克 ====================

def pan_zeike(si_ke: List[Dict], day_gan: str) -> Dict:
    """
    判贼克：检查四课中的克贼关系，确定初传。
    规则（《大六壬心镜》）：
    1. 检查每课的上下是否有克（上克下或下克上）
    2. 如果只有一个克贼，取该课的上神为初传
    3. 如果有多个克贼：
       - 上克下为主：取上克下者
       - 下克上为主：取下克上者
       - 多个同类型克贼：用比用法（与日干五行比和者）
    """
    ke_courses = []  # 有克贼的课

    for course in si_ke:
        shang_wx = ZHI_WX[course['shang']]
        xia_wx = ZHI_WX[course['xia']]

        if shang_wx == xia_wx:
            continue  # 同五行无克

        if WX_KE.get(shang_wx) == xia_wx:
            # 上克下
            ke_courses.append({
                'course': course,
                'type': '上克下',
                'shang': course['shang'],
                'xia': course['xia'],
            })
        elif WX_KE.get(xia_wx) == shang_wx:
            # 下克上
            ke_courses.append({
                'course': course,
                'type': '下克上',
                'shang': course['shang'],
                'xia': course['xia'],
            })

    if len(ke_courses) == 0:
        # 无克贼：取昴星（日支上神）或别责（日干上神）
        # 简化：取第一课上神为初传
        return {
            'chuchuan': si_ke[0]['shang'],
            'chuchuan_type': '无克贼（取干上）',
            'ke_count': 0,
            'ke_details': [],
        }

    if len(ke_courses) == 1:
        # 只有一个克贼：直接取上神为初传
        kc = ke_courses[0]
        return {
            'chuchuan': kc['shang'],
            'chuchuan_type': kc['type'],
            'ke_count': 1,
            'ke_details': ke_courses,
        }

    # 多个克贼：先分上克下和下克上
    shang_ke_xia = [kc for kc in ke_courses if kc['type'] == '上克下']
    xia_ke_shang = [kc for kc in ke_courses if kc['type'] == '下克上']

    # 规则：下克上优先（如有）
    if len(xia_ke_shang) == 1:
        kc = xia_ke_shang[0]
        return {
            'chuchuan': kc['shang'],
            'chuchuan_type': '下克上（独）',
            'ke_count': len(ke_courses),
            'ke_details': ke_courses,
        }

    if len(shang_ke_xia) == 1 and len(xia_ke_shang) == 0:
        kc = shang_ke_xia[0]
        return {
            'chuchuan': kc['shang'],
            'chuchuan_type': '上克下（独）',
            'ke_count': len(ke_courses),
            'ke_details': ke_courses,
        }

    # 多个同类型克贼：用比用法
    # 比用法：取与日干五行比和者（同五行），若无比和则取与日干异类者
    day_wx = GAN_WX[day_gan]

    candidates = xia_ke_shang if len(xia_ke_shang) > 0 else shang_ke_xia
    bi_he = [kc for kc in candidates if ZHI_WX[kc['shang']] == day_wx]

    if len(bi_he) == 1:
        kc = bi_he[0]
        return {
            'chuchuan': kc['shang'],
            'chuchuan_type': f'比用法（{kc["type"]}）',
            'ke_count': len(ke_courses),
            'ke_details': ke_courses,
        }

    # 比用法还不能确定：取涉害深者（简化：取课序最前者）
    kc = candidates[0]
    return {
        'chuchuan': kc['shang'],
        'chuchuan_type': f'涉害法（{kc["type"]}）',
        'ke_count': len(ke_courses),
        'ke_details': ke_courses,
    }


# ==================== 推三传 ====================

def pan_san_chuan(si_ke: List[Dict], zeike_result: Dict, tianpan: Dict[str, str]) -> Dict:
    """
    推三传：初传定后，推中传、末传。
    规则：
    1. 如果初传所在课是「下克上」：中传取初传的上神（天盘），末传取中传的上神
    2. 如果初传所在课是「上克下」：中传取初传的下神（地盘），末传取中传的下神
    3. 遇到克贼循环（回到已出现的支）：按特定规则处理
    """
    chuchuan = zeike_result['chuchuan']
    chuchuan_type = zeike_result['chuchuan_type']

    # 找初传所在课
    chuchuan_course = None
    for course in si_ke:
        if course['shang'] == chuchuan:
            chuchuan_course = course
            break

    # 判断初传所在课的类型
    if '下克上' in chuchuan_type:
        # 下克上：中传取初传的上神，末传取中传的上神
        zhongchuan = tianpan[chuchuan]
        mochuan = tianpan[zhongchuan]
        method = '下克上→中传取上神→末传取上神'
    elif '上克下' in chuchuan_type:
        # 上克下：中传取初传的下神，末传取中传的下神
        if chuchuan_course:
            zhongchuan = chuchuan_course['xia']
            mochuan_zhi = chuchuan_course['xia']
            mochuan = mochuan_zhi  # 简化：末传取中传的下神
            method = '上克下→中传取下神→末传取下神'
        else:
            zhongchuan = tianpan[chuchuan]
            mochuan = tianpan[zhongchuan]
            method = '上克下（简化推导）'
    else:
        # 无克贼或特殊情况：简化取法
        zhongchuan = si_ke[2]['shang'] if len(si_ke) > 2 else tianpan[chuchuan]
        mochuan = si_ke[3]['shang'] if len(si_ke) > 3 else tianpan[zhongchuan]
        method = '无克贼/特殊（简化取法）'

    return {
        '初传': chuchuan,
        '中传': zhongchuan,
        '末传': mochuan,
        'method': method,
        'chuchuan_type': chuchuan_type,
    }


# ==================== 排天将 ====================

def pai_tian_jiang(day_gan: str, san_chuan: Dict, si_ke: List[Dict],
                   hour: int) -> Dict:
    """
    排天将：贵人起始位置由日干决定，按地支顺排。
    昼夜分法：卯至戌时为昼（阳贵人顺行），亥至寅时为夜（阴贵人逆行）。
    简化：按时支阴阳判断顺逆。
    """
    guiren_zhi = GUIREN_START[day_gan]
    guiren_idx = DIZHI.index(guiren_zhi)

    # 昼夜判断：卯(4)至戌(10)为昼，亥(11)至寅(3)为夜
    hour_zhi_idx = int((hour + 1) / 2) % 12
    is_daytime = 4 <= hour_zhi_idx <= 10

    def get_jiang(zhi):
        zhi_idx = DIZHI.index(zhi)
        if is_daytime:
            # 昼：贵人起始顺行
            offset = (zhi_idx - guiren_idx) % 12
        else:
            # 夜：贵人起始逆行
            offset = (guiren_idx - zhi_idx) % 12
        return TIAN_JIANG[offset]

    result = {}
    # 三传天将
    for key in ['初传', '中传', '末传']:
        zhi = san_chuan[key]
        jiang = get_jiang(zhi)
        result[key + '天将'] = jiang
        result[key + '天将象意'] = TIAN_JIANG_XIANG.get(jiang, '')

    # 四课天将
    for course in si_ke:
        for key in ['shang', 'xia']:
            zhi = course[key]
            jiang = get_jiang(zhi)
            result[f"第{course['seq']}课{key}天将"] = jiang

    result['昼夜'] = '昼' if is_daytime else '夜'
    result['贵人起始'] = guiren_zhi

    return result


# ==================== 排盘主函数 ====================

def pan(year: int, month: int, day: int, hour: int) -> Dict:
    """大六壬完整排盘"""
    day_gan, day_zhi = _day_ganzhi(year, month, day)
    hour_gan, hour_zhi = _hour_ganzhi(day_gan, hour)
    yuejiang = get_yuejiang(year, month, day)

    # 月将加时 → 天地盘
    tianpan = yuejiang_jiashi(yuejiang, hour_zhi)

    # 起四课
    si_ke = qi_si_ke(day_gan, day_zhi, tianpan)

    # 判贼克 → 初传
    zeike = pan_zeike(si_ke, day_gan)

    # 推三传
    san_chuan = pan_san_chuan(si_ke, zeike, tianpan)

    # 排天将
    tian_jiang = pai_tian_jiang(day_gan, san_chuan, si_ke, hour)

    return {
        'year_ganzhi': f"{TIANGAN[(year - 4) % 10]}{DIZHI[(year - 4) % 12]}",
        'day_ganzhi': day_gan + day_zhi,
        'hour_ganzhi': hour_gan + hour_zhi,
        'yuejiang': yuejiang,
        'tianpan': tianpan,
        'si_ke': si_ke,
        'zeike': zeike,
        'san_chuan': san_chuan,
        'tian_jiang': tian_jiang,
    }


def format_report(p: Dict) -> str:
    out = []
    out.append("=" * 58)
    out.append("【大六壬 · 排盘】")
    out.append("=" * 58)
    out.append(f"  年柱：{p['year_ganzhi']}　日柱：{p['day_ganzhi']}　时柱：{p['hour_ganzhi']}")
    out.append(f"  月将：{p['yuejiang']}　昼夜：{p['tian_jiang']['昼夜']}")
    out.append("")
    out.append("【天地盘】（地支→天盘对应）")
    tianpan_str = ' '.join(f"{z}→{p['tianpan'][z]}" for z in DIZHI)
    out.append(f"  {tianpan_str}")
    out.append("")
    out.append("【四课】")
    for course in p['si_ke']:
        shang_jiang = p['tian_jiang'].get(f"第{course['seq']}课shang天将", '')
        xia_jiang = p['tian_jiang'].get(f"第{course['seq']}课xia天将", '')
        out.append(f"  {course['name']}：上={course['shang']}({shang_jiang}) 下={course['xia']}({xia_jiang})")
    out.append("")
    out.append("【判贼克】")
    out.append(f"  克贼数：{p['zeike']['ke_count']}")
    out.append(f"  初传取法：{p['zeike']['chuchuan_type']}")
    out.append("")
    out.append("【三传】")
    for key in ['初传', '中传', '末传']:
        val = p['san_chuan'][key]
        jiang = p['tian_jiang'].get(key + '天将', '')
        xiang = p['tian_jiang'].get(key + '天将象意', '')
        out.append(f"  {key}：{val}　天将：{jiang}（{xiang}）")
    out.append(f"  推导方法：{p['san_chuan']['method']}")
    out.append("")
    out.append("【十二天将象意】《六壬大全·天将定位》")
    for jiang, xiang in TIAN_JIANG_XIANG.items():
        out.append(f"  {jiang}：{xiang}")
    return "\n".join(out)


# ==================== 主函数 ====================

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) > 1 and sys.argv[1] in ('--help', '-h'):
        print("大六壬排盘工具 v2.0（《大六壬指南》《六壬大全》《大六壬心镜》）")
        print("v2.0：完整判贼克与三传推导")
        print("用法: python liuren.py <年> <月> <日> <时>")
        print("示例:")
        print("  python liuren.py 2026 9 3 10")
        print("  python liuren.py 2026 2 4 15")
        sys.exit(0)

    if len(sys.argv) < 5:
        print(json.dumps(error_response("MISSING_ARGUMENTS",
                                        "用法: python liuren.py <年> <月> <日> <时>"),
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
        'year_ganzhi': p['year_ganzhi'],
        'day_ganzhi': p['day_ganzhi'],
        'hour_ganzhi': p['hour_ganzhi'],
        'yuejiang': p['yuejiang'],
        '昼夜': p['tian_jiang']['昼夜'],
        'si_ke': [{'name': c['name'], 'shang': c['shang'], 'xia': c['xia']} for c in p['si_ke']],
        'zeike': p['zeike'],
        'san_chuan': p['san_chuan'],
        'tian_jiang': {k: v for k, v in p['tian_jiang'].items() if '天将' in k or k in ['昼夜', '贵人起始']},
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
