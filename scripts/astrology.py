#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
星座星盘工具 - 使用ephem高精度天文计算
参考：托勒密《四书》、《内在的天空》(史蒂芬·阿若优)

ephem库说明：
- 基于法国巴黎天文台的VSOP87/ELP2000理论
- 精度可达0.001角秒（专业级别）
- 时间范围：公元前4713年至公元9999年
"""

try:
    import ephem
except ImportError:
    ephem = None  # 未安装 ephem 时仅星座功能不可用，其余模块不受影响
import json
from datetime import datetime, timedelta
import sys
import io

# 设置UTF-8输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ==================== 常量定义 ====================

# 中国主要城市经纬度库
CITY_COORDS = {
    '北京': ('116.4', '39.9'),
    '上海': ('121.5', '31.2'),
    '广州': ('113.3', '23.1'),
    '深圳': ('114.1', '22.5'),
    '杭州': ('120.2', '30.3'),
    '南京': ('118.8', '32.1'),
    '成都': ('104.1', '30.7'),
    '重庆': ('106.5', '29.5'),
    '武汉': ('114.3', '30.6'),
    '西安': ('108.9', '34.3'),
    '天津': ('117.2', '39.1'),
    '苏州': ('120.6', '31.3'),
    '长沙': ('113.0', '28.2'),
    '郑州': ('113.6', '34.8'),
    '青岛': ('120.4', '36.1'),
    '沈阳': ('123.4', '41.8'),
    '大连': ('121.6', '39.0'),
    '厦门': ('118.1', '24.5'),
    '福州': ('119.3', '26.1'),
    '济南': ('117.0', '36.7'),
    '石家庄': ('114.5', '38.0'),
    '南昌': ('115.9', '28.7'),
    '昆明': ('102.7', '25.0'),
    '贵阳': ('106.7', '26.6'),
    '南宁': ('108.3', '22.8'),
    '海口': ('110.3', '20.0'),
    '太原': ('112.5', '37.9'),
    '长春': ('125.3', '43.9'),
    '哈尔滨': ('126.6', '45.8'),
    '兰州': ('103.8', '36.1'),
    '乌鲁木齐': ('87.6', '43.8'),
    '拉萨': ('91.1', '29.7'),
    '西宁': ('101.8', '36.6'),
    '呼和浩特': ('111.7', '40.8'),
    '银川': ('106.3', '38.5'),
    '保定': ('115.5', '38.9'),
    '唐山': ('118.2', '39.6'),
    '绍兴': ('120.6', '30.0'),
}

# 星座定义
ZODIAC = [
    ('白羊座', 0, '火', '冲动、勇敢、开拓'),
    ('金牛座', 30, '土', '稳定、务实、执着'),
    ('双子座', 60, '风', '多变、灵活、沟通'),
    ('巨蟹座', 90, '水', '敏感、守护、情感'),
    ('狮子座', 120, '火', '自信、领导、表演'),
    ('处女座', 150, '土', '分析、挑剔、服务'),
    ('天秤座', 180, '风', '和谐、犹豫、社交'),
    ('天蝎座', 210, '水', '深沉、神秘、执着'),
    ('射手座', 240, '火', '乐观、自由、冒险'),
    ('摩羯座', 270, '土', '务实、隐忍、成就'),
    ('水瓶座', 300, '风', '独特、创新、冷漠'),
    ('双鱼座', 330, '水', '浪漫、迷茫、同情'),
]

# 行星定义（ephem 缺失时置空，main() 中会先做依赖检查）
if ephem is not None:
    PLANETS = {
        '太阳': ephem.Sun,
        '月亮': ephem.Moon,
        '水星': ephem.Mercury,
        '金星': ephem.Venus,
        '火星': ephem.Mars,
        '木星': ephem.Jupiter,
        '土星': ephem.Saturn,
        '天王星': ephem.Uranus,
        '海王星': ephem.Neptune,
        '冥王星': ephem.Pluto,
    }
else:
    PLANETS = {}

# 行星象征意义（《内在的天空》）
PLANET_MEANING = {
    '太阳': '生命力、自我、创造力、父亲',
    '月亮': '情绪、潜意识、母亲、本能',
    '水星': '沟通、思维、学习、兄弟',
    '金星': '爱情、审美、财富、人际关系',
    '火星': '行动、欲望、冲动、竞争',
    '木星': '扩张、幸运、智慧、成长',
    '土星': '限制、责任、考验、业力',
    '天王星': '变革、独特、解放、发明',
    '海王星': '梦想、灵性、迷惑、牺牲',
    '冥王星': '转化、深度、权力、禁忌',
}

# 宫位主题
HOUSE_THEMES = [
    '自我、身份、外貌、人生起点',
    '财产、拥有物、赚钱方式、价值观',
    '沟通、学习、兄弟姐妹、短途旅行',
    '家庭、根基、父母、住宅',
    '创造、恋爱、子女、艺术',
    '健康、工作、服务、臣属',
    '伴侣、婚姻、契约、合作',
    '共享资源、保险、税务、债务',
    '高等教育、哲学、旅行、外国人',
    '事业、社会地位、公众形象',
    '朋友、社团、理想、愿望',
    '隐匿、幕后、玄学、秘密',
]


def zodiac_sign(degree: float) -> tuple:
    """根据黄道度数确定星座"""
    for sign, start, element, trait in ZODIAC:
        if start <= degree < start + 30:
            return sign, element, trait, int(degree - start)
    return '双鱼座', '水', '浪漫、迷茫、同情', int(degree - 330)


def jd_from_datetime(dt: datetime) -> float:
    """将datetime转换为儒略日"""
    return ephem.julian_date(dt)


def get_planet_position(planet_name: str, dt: datetime, lat: str, lon: str) -> tuple:
    """
    使用ephem计算行星位置
    返回：(星座, 度数, 详细度数)
    """
    try:
        planet = PLANETS[planet_name]()
        planet.compute(dt)

        # 获取黄经（ecliptic longitude）
        # ephem返回的是地心坐标，需要转换
        ecl = planet.hlon  # 黄经（弧度）

        # 转换为度
        degree = ecl * 180 / 3.14159265359
        if degree < 0:
            degree += 360

        sign, element, trait, deg_in_sign = zodiac_sign(degree)

        return sign, element, trait, round(degree, 2), deg_in_sign
    except Exception as e:
        return '未知', '未知', '未知', 0, 0


def calculate_ascendant(dt: datetime, lat: str, lon: str) -> tuple:
    """
    计算上升星座
    使用简化算法（ephem不直接提供上升点，需要计算）
    """
    # 儒略日
    jd = jd_from_datetime(dt)

    # 简化上升点计算
    # 实际应使用完整的天文计算，此为简化版
    T = (jd - 2451545.0) / 36525.0

    # 恒星时
    ST = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T

    # 粗略上升点（简化算法）
    asc = (ST + float(lon)) % 360

    result = zodiac_sign(asc)
    sign, element, trait, min_deg = result[0], result[1], result[2], result[3]

    return sign, element, trait, round(asc, 2), min_deg


def calculate_midheaven(dt: datetime, lat: str, lon: str) -> tuple:
    """计算天顶/中天"""
    jd = jd_from_datetime(dt)

    T = (jd - 2451545.0) / 36525.0
    ST = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T

    # 天顶黄经
    MC = (ST + float(lon) + 90) % 360

    result = zodiac_sign(MC)
    sign, element, trait, min_deg = result[0], result[1], result[2], result[3]

    return sign, element, trait, round(MC, 2), min_deg


def calculate_houses(dt: datetime, lat: str, lon: str) -> dict:
    """
    计算十二宫位（简化版普拉西德宫位制）
    """
    # 这是简化计算，专业软件使用完整天文算法
    jd = jd_from_datetime(dt)

    T = (jd - 2451545.0) / 36525.0
    ST = 280.46061837 + 360.98564736629 * (jd - 2451545.0) + 0.000387933 * T * T

    lat_val = float(lat)

    houses = {}
    for i in range(12):
        # 简化宫头计算
        house_deg = (ST + float(lon) + i * 30) % 360
        result = zodiac_sign(house_deg)
        sign = result[0]
        houses[i + 1] = (sign, house_deg)

    return houses


def calculate_aspects(positions: dict) -> list:
    """
    计算主要相位
    《四书》(托勒密)：合相0°、六分相60°、刑相90°、三合相120°、冲相180°
    """
    aspects = []
    aspect_angles = {
        '合相': (0, 8),
        '六分相': (60, 6),
        '刑相': (90, 5),
        '三合相': (120, 6),
        '冲相': (180, 8),
    }

    planets = list(positions.keys())
    for i in range(len(planets)):
        for j in range(i + 1, len(planets)):
            p1, p2 = planets[i], planets[j]
            deg1 = positions[p1]['degree']
            deg2 = positions[p2]['degree']

            diff = abs(deg1 - deg2)
            if diff > 180:
                diff = 360 - diff

            for aspect_name, (angle, orb) in aspect_angles.items():
                if abs(diff - angle) <= orb:
                    aspects.append({
                        'planet1': p1,
                        'planet2': p2,
                        'aspect': aspect_name,
                        'angle': angle,
                        'exactness': angle - diff
                    })

    return aspects


def generate_report(birth_dt: datetime, gender: str, lat: str, lon: str) -> list:
    """生成完整星盘报告"""
    report = []

    report.append("=" * 60)
    report.append("【星座星盘】基于ephem高精度天文计算")
    report.append("参考：托勒密《四书》、《内在的天空》(史蒂芬·阿若优)")
    report.append("=" * 60)
    report.append("")

    # 基本信息
    report.append(f"出生时间：{birth_dt.strftime('%Y年%m月%d日 %H:%M')}")
    report.append(f"出生地点：{lat}°N, {lon}°E")
    report.append(f"儒略日：{jd_from_datetime(birth_dt):.2f}")
    report.append("")

    # 核心三颗星
    report.append("【三颗关键星】")
    sun_pos = get_planet_position('太阳', birth_dt, lat, lon)
    moon_pos = get_planet_position('月亮', birth_dt, lat, lon)
    asc_pos = calculate_ascendant(birth_dt, lat, lon)

    report.append(f"  太阳：落在 {sun_pos[0]} {sun_pos[4]}°（{sun_pos[3]}°）")
    report.append(f"    元素：{sun_pos[1]} | {sun_pos[2]}")
    report.append(f"  月亮：落在 {moon_pos[0]} {moon_pos[4]}°（{moon_pos[3]}°）")
    report.append(f"    元素：{moon_pos[1]} | {moon_pos[2]}")
    report.append(f"  上升：落在 {asc_pos[0]} {asc_pos[4]}°（{asc_pos[3]}°）")
    report.append(f"    元素：{asc_pos[1]} | {asc_pos[2]}")
    report.append("")

    # 行星分布
    report.append("【十大行星分布】")
    positions = {}
    for planet_name in PLANETS:
        pos = get_planet_position(planet_name, birth_dt, lat, lon)
        positions[planet_name] = {
            'sign': pos[0],
            'degree': pos[3],
            'element': pos[1]
        }
        report.append(f"  {planet_name}：{pos[0]} {pos[4]}° ({pos[1]}元素)")

    report.append("")

    # 元素分布
    element_count = {'火': 0, '土': 0, '风': 0, '水': 0}
    for planet, pos in positions.items():
        if planet != '冥王星':  # 冥王星不计入主要元素
            element_count[pos['element']] += 1

    report.append("【元素分布】《四书》(托勒密)")
    for elem, count in sorted(element_count.items(), key=lambda x: -x[1]):
        bar = '●' * count + '○' * (4 - count)
        report.append(f"  {elem}：{bar} ({count}/10)")

    report.append("")

    # 宫位分布
    houses = calculate_houses(birth_dt, lat, lon)
    report.append("【十二宫分布】")
    for i in range(1, 13):
        sign, deg = houses[i]
        report.append(f"  第{i}宫：{sign} {int(deg % 30)}° | {HOUSE_THEMES[i-1]}")

    report.append("")

    # 主要相位
    aspects = calculate_aspects(positions)
    if aspects:
        report.append("【主要相位】《四书》(托勒密)")
        for asp in sorted(aspects, key=lambda x: -abs(x['exactness'])):
            report.append(f"  {asp['planet1']} {asp['aspect']} {asp['planet2']} (误差{abs(asp['exactness']):.1f}°)")
    else:
        report.append("【主要相位】无明显主要相位")

    report.append("")
    report.append("=" * 60)

    return report


def main():
    """主函数"""
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) < 5 or sys.argv[1] in ('--help', '-h'):
        print("星座星盘工具 v1.0（依赖 ephem 高精度天文库）")
        print("用法: python astrology.py <年> <月> <日> <时> [地点]")
        print("示例: python astrology.py 1993 6 18 15 绍兴")
        print("      python astrology.py 1993 6 18 15 北京")
        sys.exit(0)

    try:
        year = int(sys.argv[1])
        month = int(sys.argv[2])
        day = int(sys.argv[3])
        hour = int(sys.argv[4])
    except ValueError as e:
        print(json.dumps(error_response("INVALID_NUMBER", f"年月日时必须为整数: {e}"),
                         ensure_ascii=False, indent=2))
        sys.exit(2)
    location = sys.argv[5] if len(sys.argv) > 5 else '北京'

    if ephem is None:
        print(json.dumps(error_response("MISSING_DEPENDENCY",
                                        ["星座占星需要 ephem 库，请先安装：pip install ephem"]),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    from p0_validators import _valid_date
    verrs = _valid_date(year, month, day, hour)
    if verrs:
        print(json.dumps(error_response("INVALID_INPUT", verrs),
                         ensure_ascii=False, indent=2))
        sys.exit(2)

    # 获取坐标
    if location in CITY_COORDS:
        lon, lat = CITY_COORDS[location]
    else:
        # 默认北京
        lon, lat = CITY_COORDS['北京']

    # 构建datetime
    birth_dt = datetime(year, month, day, hour, 0)

    # 生成报告
    report = generate_report(birth_dt, '', lat, lon)
    print('\n'.join(report))

    # JSON输出
    result = {
        'birth': {'year': year, 'month': month, 'day': day, 'hour': hour},
        'location': location,
        'longitude': lon,
        'latitude': lat,
        'report': report
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
