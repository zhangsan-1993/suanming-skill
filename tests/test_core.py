#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
算命 skill 回归测试
- 节气时刻 vs 公开已知值
- 干支排盘 vs 权威库 lunar_python（未安装则跳过交叉项）
- 全链路 engine / export_report
- 紫微 14 主星完整性
- test-prompts.json 场景冒烟

运行：cd scripts && python -m pytest ../tests -v
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from p0_validators import get_jieqi_datetime, solar_to_lunar, check_jieqi_boundary, p0_validate  # noqa: E402
from bazi import calculate_day_gz  # noqa: E402
from p1_validators import validate_sishu  # noqa: E402
from divination_engine import DivinationEngine  # noqa: E402


# ---------- 节气时刻（对照紫金山天文台公开数据） ----------

def test_jieqi_dates():
    cases = [
        (2024, '立春', (2, 4)), (2025, '立春', (2, 3)), (2000, '立春', (2, 4)),
        (1990, '立春', (2, 4)), (2024, '冬至', (12, 21)), (2024, '夏至', (6, 21)),
        (2000, '白露', (9, 7)), (2024, '惊蛰', (3, 5)), (1988, '清明', (4, 4)),
        (1984, '立春', (2, 4)), (2010, '芒种', (6, 6)),
    ]
    for y, name, expect in cases:
        dt = get_jieqi_datetime(y, name)
        assert dt is not None, f'{y} {name} 计算失败'
        assert (dt.month, dt.day) == expect, f'{y} {name}: 得{dt} 期望{expect}'


# ---------- 干支排盘 golden cases（人工核验过） ----------

def test_bazi_golden_cases():
    cases = [
        ((2000, 9, 9, 12), ('庚辰', '乙酉', '庚午', '壬午')),
        ((2000, 1, 1, 12), ('己卯', '丙子', '戊午', '戊午')),
        ((1984, 2, 2, 12), ('癸亥', '乙丑', '丙寅', '甲午')),   # 立春前 → 癸亥
        ((1984, 2, 5, 12), ('甲子', '丙寅', '己巳', '庚午')),   # 立春后 → 甲子
        ((1993, 6, 18, 15), ('癸酉', '戊午', '庚午', '甲申')),  # 15:00 = 申时起点
        ((1988, 5, 15, 12), ('戊辰', '丁巳', '庚午', '壬午')),
        ((2024, 2, 10, 10), ('甲辰', '丙寅', '甲辰', '己巳')),
        ((2025, 1, 28, 10), ('甲辰', '丁丑', '丁酉', '乙巳')),
    ]
    for args, exp in cases:
        got = calculate_day_gz(*args)
        assert got == exp, f'{args}: 得{got} 期望{exp}'


def test_bazi_cross_lunar_python():
    """与权威库 lunar_python 交叉验证（未安装则跳过）"""
    try:
        from lunar_python import Solar
    except ImportError:
        return  # 可选依赖
    for y, m, d, h in [(1990, 6, 15, 14), (1995, 11, 3, 20), (2005, 3, 8, 9),
                       (2010, 8, 25, 16), (2000, 9, 9, 12), (1993, 6, 18, 15)]:
        got = calculate_day_gz(y, m, d, h)
        l = Solar.fromYmdHms(y, m, d, h, 0, 0).getLunar()
        exp = (l.getYearInGanZhi(), l.getMonthInGanZhi(),
               l.getDayInGanZhi(), l.getTimeInGanZhi())
        assert got == exp, f'{y}-{m}-{d} {h}时: 得{got} 期望{exp}'


# ---------- P0 / P1 可执行自检 ----------

def test_p0_non_2000_years():
    for args in [(1993, 6, 18, 15), (1988, 5, 15, 12), (2024, 2, 10, 10), (1958, 11, 3, 8)]:
        r = p0_validate(*args)
        assert r['pass'], f'{args} P0 未通过: {r["errors"]}'
        assert r['lunar']['ganzhi_day'] in {g + z for g in '甲乙丙丁戊己庚辛壬癸' for z in '子丑寅卯辰巳午未申酉戌亥'}


def test_p0_invalid_inputs():
    assert not p0_validate(2000, 13, 1, 12)['pass']
    assert not p0_validate(2000, 2, 30, 12)['pass']
    assert not p0_validate(2000, 1, 1, 25)['pass']


def test_validate_sishu():
    ok, _ = validate_sishu({'年柱': '庚辰', '月柱': '乙酉', '日柱': '庚午', '时柱': '壬午'})
    assert ok
    bad, errs = validate_sishu({'年柱': '辛辰', '月柱': '乙酉', '日柱': '庚午', '时柱': '壬午'})
    assert not bad and any('六十甲子' in e for e in errs)


def test_ziwei_stars_complete():
    from ziwei import main  # noqa: F401  # 触发模块加载
    from ziwei import distribute_stars, validate_ziwei_stars
    # 用 2024-02-10 男 的命盘参数抽查（直接调用内部函数）
    for (y, m, d, h) in [(2024, 2, 10, 10), (1993, 6, 18, 15), (2000, 9, 9, 12)]:
        # 构造 ziwei 所需中间量
        from ziwei import calculate_shengxiao, get_minggong_position, DIZHI, TIANGAN
        shengxiao = calculate_shengxiao(y)
        hour_zhi_index = int((h + 1) / 2) % 12
        month_zhi_index = m % 12
        ming_gong, shen_gong = get_minggong_position(shengxiao, DIZHI[month_zhi_index], DIZHI[hour_zhi_index])
        year_gan = TIANGAN[(y - 4) % 10]
        palaces = distribute_stars(ming_gong, year_gan, DIZHI[month_zhi_index])
        ok, errs = validate_ziwei_stars(palaces)
        assert ok, f'{y}-{m}-{d}: {errs}'


# ---------- 全链路 engine ----------

def test_engine_full_flow():
    e = DivinationEngine()
    res = e.full_process(1993, 6, 18, 15, '女', longitude=120.0)
    assert res['success'], res.get('errors')
    assert res['bazi']['日柱'] == '庚午'
    # export_report 不再抛异常
    txt = e.export_report('/tmp/_suanming_test_report.md')
    assert txt.startswith('# 八字命理推演报告')


# ---------- test-prompts.json 场景冒烟 ----------

def test_prompts_json_smoke():
    root = os.path.dirname(os.path.dirname(__file__))
    with open(os.path.join(root, 'test-prompts.json'), encoding='utf-8') as f:
        prompts = json.load(f)
    assert len(prompts) == 3
    for p in prompts:
        assert p['id'] and p['prompt'] and p['expected']
    # 场景1：八字排盘
    e = DivinationEngine()
    assert e.full_process(1988, 5, 15, 12, '男')['success']
    # 场景2：合盘（双方八字均需能排）
    from bazi import calculate_day_gz
    assert calculate_day_gz(1990, 3, 8, 19)[0]
    assert calculate_day_gz(1992, 7, 15, 12)[0]
    # 场景3：起卦（qigua 铜钱起卦 + liuyao 时间起卦，验证输出合法）
    import qigua
    yao = qigua.shake_one_yao()
    assert yao in (6, 7, 8, 9), f'铜钱起卦爻值非法: {yao}'
    from liuyao import time_divination
    lines = time_divination(2026, 4, 2, 15)
    assert len(lines) == 6 and all(v in (6, 7, 8, 9) for v, _ in lines), f'时间起卦输出非法: {lines}'
    assert True
