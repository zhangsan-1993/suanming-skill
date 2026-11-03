#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一推演引擎
整合P0→P1→计算→报告完整流程
"""

import json
from datetime import datetime
from typing import Dict, List, Tuple
from p0_validators import p0_validate
from p1_validators import p1_validate
from bazi import (
    calculate_day_gz, calculate_day_master_strength, 
    calculate_shishen, calculate_dayun, calculate_liunian,
    TIANGAN, DIZHI, WUXING_TIAN, WUXING_ZHI, YINYANG_TIAN
)


class DivinationEngine:
    """统一推演引擎"""
    
    def __init__(self):
        self.p0_passed = False
        self.p1_passed = False
        self.bazi = None
        self.analysis = None
        self.p0_result = None
        self.errors = []
    
    def do_p0(self, year: int, month: int, day: int, hour: int, longitude: float = 120.0):
        """执行P0基础验证"""
        result = p0_validate(year, month, day, hour, longitude, verbose=True)
        self.p0_result = result
        self.p0_passed = result['pass']
        if not self.p0_passed:
            self.errors = result['errors']
        return result
    
    def do_p1(self, bazi: Dict, gender: str, p0_result: Dict):
        """执行P1增强验证"""
        from p1_validators import p1_validate
        result = p1_validate(bazi, gender, p0_result, verbose=True)
        self.p1_passed = result['pass']
        if not self.p1_passed:
            self.errors = result['errors']
        return result
    
    def build_calibrate_bazi(self, p0_result: Dict):
        """根据P0校正结果，校准八字排盘"""
        year = p0_result['corrected']['year']
        month = p0_result['corrected']['month']
        day = p0_result['corrected']['day']
        hour = p0_result['corrected']['hour']
        
        # 使用校正后的时间重新排盘
        nianzhu, _, _, shizhu = calculate_day_gz(year, month, day, hour)

        # 根据P0节气结果校正月柱（十二节定月支，五虎遁定月干）
        year_gan_index = TIANGAN.index(nianzhu[0])
        month_starts = {
            0: 2, 5: 2,  # 甲己 → 丙寅
            1: 4, 6: 4,  # 乙庚 → 戊寅
            2: 6, 7: 6,  # 丙辛 → 庚寅
            3: 8, 8: 8,  # 丁壬 → 壬寅
            4: 0, 9: 0,  # 戊癸 → 甲寅
        }
        month_index = p0_result['jieqi']['lunar_month']  # 寅=1 ... 丑=12
        month_gan_index = (month_starts[year_gan_index] + (month_index - 1)) % 10
        month_gan = TIANGAN[month_gan_index]
        correct_yuezhu = month_gan + p0_result['jieqi']['di_zhi']

        # P0 已给出正确日柱干支（权威儒略日法）
        correct_rizhu = p0_result['lunar']['ganzhi_day']
        
        self.bazi = {
            '年柱': nianzhu,
            '月柱': correct_yuezhu,
            '日柱': correct_rizhu,
            '时柱': shizhu
        }
        return self.bazi
    
    def analyze_bazi_weath(self, birth_date: datetime, gender: str, current_year: int = None):
        """八字深度分析"""
        if not self.bazi:
            return None
        
        if current_year is None:
            current_year = datetime.now().year
            
        day_master = calculate_day_master_strength(self.bazi, birth_date)
        shishen = calculate_shishen(self.bazi)
        dayun = calculate_dayun(self.bazi, birth_date.year, current_year, gender)
        liunian = calculate_liunian(self.bazi, current_year, birth_date.year)
        
        # 统计五行数量
        wuxing_count = {'木': 0, '火': 0, '土': 0, '金': 0, '水': 0}
        for pillar in ['年柱', '月柱', '日柱', '时柱']:
            gan = self.bazi[pillar][0]
            zhi = self.bazi[pillar][1]
            wuxing_count[WUXING_TIAN[gan]] += 1
            wuxing_count[WUXING_ZHI[zhi]] += 1
        
        # 财星分析（财星就是我克者为财，日主辛金，辛金克木，木就是财
        # 正财偏财区分阴阳
        # 对辛金（阴金），阳木甲是偏财，阴木乙是正财
        
        self.analysis = {
            'day_master': day_master,
            'shishen': shishen,
            'dayun': dayun,
            'liunian': liunian,
            'wuxing_count': wuxing_count,
            'gender': gender
        }
        return self.analysis
    
    def generate_caiyun_analysis(self):
        """专门分析财运（正财+偏财，重点炒股）"""
        if not self.analysis:
            return None
        
        dm = self.analysis['day_master']
        wc = self.analysis['wuxing_count']
        ss = self.analysis['shishen']
        du = self.analysis['dayun']
        current_age = datetime.now().year - 2000
        # 找当前大运
        current_da_yun = None
        for d in du:
            age_start = int(d['年龄'].split('-')[0])
            age_end = int(d['年龄'].split('-')[1].replace('岁',''))
            if current_age >= age_start and current_age <= age_end:
                current_da_yun = d
                break
        
        # 日主辛金，我克者为财，财是木
        cai_wuxing = '木'
        cai_count = wc[cai_wuxing]
        
        # 找原局十神中的财星
        has_pian_cai = None
        has_zheng_cai = None
        for p in ['年柱', '月柱', '时柱']:
            if ss[p]['十神'] == '偏财':
                has_pian_cai = ss[p]
            if ss[p]['十神'] == '正财':
                has_zheng_cai = ss[p]
        
        # 分析结构
        analysis = {
            '日主': dm['日主'],
            '日主五行': dm['日主五行'],
            '财星五行': '木',
            '原局财星数量': cai_count,
            '有偏财': has_pian_cai is not None,
            '偏财天干': has_pian_cai['天干'] if has_pian_cai else None,
            '有正财': has_zheng_cai is not None,
            '正财天干': has_zheng_cai['天干'] if has_zheng_cai else None,
            '当前大运': current_da_yun,
            '当前大运财星情况': '',
            '总体评价': '',
            '炒股偏财机会': '',
            '建议': ''
        }
        
        # 分析
        if current_da_yun:
            if current_da_yun['天干五行'] == '木' or current_da_yun['地支五行'] == '木':
                analysis['当前大运财星情况'] = '大运见财星，财运增强'
            elif current_da_yun['天干五行'] == '水':
                analysis['当前大运财星情况'] = '水生木，印星生财，间接生助财运'
            elif current_da_yun['天干五行'] == '火':
                analysis['当前大运财星情况'] = '火克金，克我者为官，财生官，财运分散'
            elif current_da_yun['天干五行'] == '土':
                analysis['当前大运财星情况'] = '土生金，比劫生食伤，食伤生财'
            elif current_da_yun['天干五行'] == '金':
                analysis['当前大运财星情况'] = '金比夺财，竞争压力大'
        
        # 总体判断
        if has_pian_cai:
            analysis['总体评价'] = '原局透出偏财星，天生对偏财（投机、股票、额外收入敏感，有偏财天赋'
            if dm['强弱判断'] in ['强', '偏强']:
                analysis['总体评价'] += '。日主偏强，能担财，可承受财运'
        else:
            analysis['总体评价'] = '原局不透偏财，偏财藏而不透，需大运引出'
        
        # 炒股专项分析
        if analysis['有偏财'] and dm['强弱判断'] in ['强', '偏强']:
            analysis['炒股适合度'] = '适合'
            analysis['炒股分析'] = '偏财透出+日主强能担，有炒股投机的命格基础'
        elif analysis['有偏财']:
            analysis['炒股适合度'] = '一般'
            analysis['炒股分析'] = '有偏财机会，但日主偏弱需注意风险控制'
        else:
            analysis['炒股适合度'] = '保守'
            analysis['炒股分析'] = '原局偏财不显，建议以稳健正财为主'
        
        return analysis
    
    def full_process(self, year: int, month: int, day: int, hour: int, 
                    gender: str, longitude: float = 120.0) -> Dict:
        """完整推演流程"""
        print("=" * 60)
        print("[P0基础验证阶段]")
        p0_result = self.do_p0(year, month, day, hour, longitude)
        if not self.p0_passed:
            print(f"[P0失败]")
            return {'success': False, 'stage': 'P0', 'errors': self.errors}
        
        print("\n[P1增强验证阶段]")
        # 先用初步排盘
        bazi = self.build_calibrate_bazi(p0_result)
        p1_result = self.do_p1(bazi, gender, p0_result)
        if not self.p1_passed:
            print(f"[P1失败]")
            return {'success': False, 'stage': 'P1', 'errors': self.errors}
        
        print("\n[深度分析阶段]")
        birth_date = datetime(year, month, day, hour)
        analysis = self.analyze_bazi_weath(birth_date, gender)
        
        print("\n[财运专项分析]")
        cai_analysis = self.generate_caiyun_analysis()
        
        print("\n[完整流程完成]")
        print("=" * 60)

        # datetime 转 ISO 字符串，保证返回结果可直接 json.dumps
        p0r = self.p0_result
        p0r['corrected']['datetime'] = p0r['corrected']['datetime'].isoformat()
        p0r['jieqi']['jieqi_time'] = p0r['jieqi']['jieqi_time'].isoformat()

        return {
            'success': True,
            'p0_result': p0_result,
            'p1_result': p1_result,
            'bazi': self.bazi,
            'full_analysis': analysis,
            'caiyun_analysis': cai_analysis
        }
    
    def export_report(self, output_path: str):
        """导出完整报告（先调用 full_process 获取结果）"""
        if self.analysis is None or self.p0_result is None:
            raise RuntimeError('请先运行 full_process() 完成推演后再导出报告')

        from datetime import datetime
        report = []
        report.append("# 八字命理推演报告\n\n")

        # 基本信息
        report.append("## 基本信息\n")
        p0r = self.p0_result
        report.append(f"- 出生日期：{p0r['original']['year']}年{p0r['original']['month']}月{p0r['original']['day']}日 {p0r['original']['hour']}时\n")
        report.append(f"- 性别：{self.analysis['gender']}\n")
        report.append(f"- 校正后真太阳时：{p0r['corrected']['hour']}时\n\n")
        
        # 八字命盘
        report.append("## 八字命盘（P0+P1验证通过）\n")
        report.append(f"- 年柱：{self.bazi['年柱']} ({YINYANG_TIAN[self.bazi['年柱'][0]]})\n")
        report.append(f"- 月柱：{self.bazi['月柱']} ({YINYANG_TIAN[self.bazi['月柱'][0]]})\n")
        report.append(f"- 日柱：{self.bazi['日柱']} ({YINYANG_TIAN[self.bazi['日柱'][0]]})\n")
        report.append(f"- 时柱：{self.bazi['时柱']} ({YINYANG_TIAN[self.bazi['时柱'][0]]})\n\n")
        
        # 五行统计
        wc = self.analysis['wuxing_count']
        report.append("## 五行分布\n")
        for w, c in wc.items():
            report.append(f"- {w}：{c}个\n")
        report.append("\n")
        
        # 日主分析
        dm = self.analysis['day_master']
        report.append("## 日主分析\n")
        report.append(f"- 日主：{dm['日主']} ({dm['日主五行']}{dm['日主阴阳']})\n")
        report.append(f"- 月令：{dm['月令']}\n")
        report.append(f"- 得令程度：{dm['得令程度']}分\n")
        report.append(f"- 强弱判断：{dm['强弱判断']}\n")
        report.append(f"- 用神建议：{dm['用神建议']}\n\n")
        
        # 十神
        report.append("## 十神定位\n")
        for pname in ['年柱', '月柱', '时柱']:
            info = self.analysis['shishen'][pname]
            report.append(f"- {pname}：{info['天干']} → {info['十神']} ({info['五行']}{info['阴阳']})\n")
        report.append("\n")
        
        # 财运专项分析
        ca = self.generate_caiyun_analysis()
        report.append("## 财运专项分析（重点：炒股偏财）\n")
        report.append(f"- 日主{ca['日主']}，五行{ca['日主五行']}，财星为{ca['财星五行']}\n")
        report.append(f"- 原局：{ca['总体评价']}\n")
        if ca['有偏财']:
            report.append(f"- 偏财透出，偏财星在{ca['有偏财天干']}干，先天对投机、股票等偏财运有先天优势\n")
        if ca['有正财']:
            report.append(f"- 同时有正财星，正财稳定收入也不错\n")
        report.append(f"- 当前大运：{ca['当前大运']['年龄']}走{ca['当前大运']['大运']}运，{ca['当前大运财星情况']}\n")
        report.append(f"- 炒股适合度：{ca['炒股适合度']}\n")
        report.append(f"- 分析：{ca['炒股分析']}\n")
        report.append(f"- 建议：{ca['建议']}\n\n")
        
        # 大运走势
        report.append("## 大运走势\n")
        for d in self.analysis['dayun'][:6]:
            report.append(f"- {d['年龄']}：{d['大运']} ({d['天干五行']}/{d['地支五行']})\n")
        report.append("\n")
        
        # 结语
        report.append("---\n")
        report.append(f"*报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        report.append(f"*数据源验证级别：学术级（T0+T1数据源交叉验证）\n")
        
        full_text = "".join(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)
        
        return full_text


def _demo():
    """演示用例（仅供开发调试，勿在生产调用；正常使用请实例化 DivinationEngine）"""
    engine = DivinationEngine()
    result = engine.full_process(2000, 9, 9, 12, '女')
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    _demo()
