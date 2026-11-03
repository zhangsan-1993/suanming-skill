#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
手相面相推演工具 v1.0

典籍依据（SKILL.md「八、风水堪舆 — 典籍规则表」相关相法部分）：
- 《麻衣神相》    面部总诀、眉相诀、鼻相诀、三停五岳六府
- 《冰鉴》（曾国藩） 神骨篇、刚柔篇、容貌篇
- 《柳庄相法》    手相掌型、三线、手丘
- 《神相全编》    综合相法大全

说明：本模块依赖 AI 模型的图片分析能力。
工作流程：
  1. 运行本脚本，获取相法典籍规则和分析框架
  2. AI 模型使用 Read 工具读取用户提供的手相/面相图片
  3. AI 模型结合图片分析结果和典籍规则，给出相法解读

用法：
  python xiangfa.py hand     # 输出手相分析框架与典籍规则
  python xiangfa.py face     # 输出面相分析框架与典籍规则
  python xiangfa.py both     # 输出手相+面相完整框架
"""

import json
import sys
from typing import Dict

# ==================== 手相规则 ====================

HAND_RULES = {
    '掌型': {
        '金型掌': '掌方而厚，指短而坚，色白润。主刚毅果断，适合金融、法律。',
        '木型掌': '掌窄长，指长而秀，色清润。主文雅智慧，适合文艺、教育。',
        '水型掌': '掌圆而软，指细而长，色黑润。主聪明灵活，适合商贸、外交。',
        '火型掌': '掌尖而红，指露节高，色赤润。主热情急躁，适合技术、创业。',
        '土型掌': '掌厚而方，指短粗壮，色黄润。主稳重踏实，适合农业、建筑。',
    },
    '三线': {
        '生命线': '起点在拇指与食指之间，呈弧形包绕大拇指根部。长而深者体质健壮；短浅者体质较弱；链状者易患慢性病。',
        '智慧线': '起点与生命线相近，横向延伸。长而清晰者思维敏捷；弯向月丘者想象力丰富；分叉者多才多艺。',
        '感情线': '起点在小指下方，横向延伸至食指或中指下方。长而深者重感情；短者理性；链状者多愁善感。',
    },
    '手丘': {
        '金星丘': '拇指根部隆起处。发达者感情丰富、有爱心；扁平者冷静理性。',
        '木星丘': '食指根部。发达者有野心、领导力；扁平者缺乏自信。',
        '土星丘': '中指根部。发达者谨慎、内省；扁平者缺乏责任感。',
        '太阳丘': '无名指根部。发达者有艺术才华、乐观；扁平者缺乏自信。',
        '水星丘': '小指根部。发达者善于交际、聪明；扁平者社交能力弱。',
        '月丘': '手腕上方外侧。发达者想象力丰富、直觉强；扁平者缺乏创造力。',
    },
    '特殊纹路': {
        '十字纹': '由两条短线交叉成X形。出现在智慧线上主直觉力强；出现在感情线上主感情波折。',
        '星纹': '由三条以上短线交叉成星形。出现在太阳丘主名利双收；出现在木星丘主权力。',
        '岛纹': '纹路中出现椭圆形空洞。出现在生命线主体弱多病；出现在智慧线主思维混乱。',
        '链状纹': '纹路呈锁链状。出现在感情线主多愁善感；出现在生命线主体弱。',
    },
}

# ==================== 面相规则 ====================

FACE_RULES = {
    '三停': {
        '上停': '额头至眉毛。主早年运势（15-30岁）。额头饱满宽阔者早年顺遂。',
        '中停': '眉毛至鼻尖。主中年运势（31-50岁）。鼻梁挺直者中年发达。',
        '下停': '鼻尖至下巴。主晚年运势（51岁后）。下巴圆润者晚年安康。',
    },
    '五官': {
        '眉': '眉为兄弟宫，主情谊、名声。眉清秀而长者重情义；眉粗浓者性急；眉低压目者性格压抑。',
        '目': '目为心之窗，主心性、智慧。眼大有神者自信；眼小细长者深沉；三角眼者精明但薄情。',
        '鼻': '鼻为财帛宫，主财运、事业。鼻梁挺直者有主见；鼻头圆润者聚财；鼻孔外露者破财。',
        '口': '口为出纳宫，主食禄、言辞。口大者能言善道；口小者谨慎保守；唇厚者重情。',
        '耳': '耳为采听宫，主少年运、智慧。耳大厚者有福；耳薄小者劳碌；贴脑耳者内敛。',
    },
    '五岳': {
        '南岳（额）': '额头为南岳。饱满者贵，凹陷者贱。',
        '北岳（颏）': '下巴为北岳。方圆者有晚福，尖削者晚年孤。',
        '东岳（鼻）': '鼻子为东岳。高隆者发达，塌陷者平庸。',
        '左颧': '左颧为东辅。丰满者有权势，低陷者无助力。',
        '右颧': '右颧为西辅。与左颧对称者吉，不对称者运势波动。',
    },
    '气色': {
        '明润': '面部气色明亮润泽，主运势通达、诸事顺遂。',
        '暗滞': '面部气色暗淡滞涩，主运势阻滞、需谨慎行事。',
        '赤色': '面部泛红，主有口舌是非或喜事（需结合具体部位判断）。',
        '青色': '面部泛青，主有惊恐、忧虑。',
        '黄色': '面部泛黄（明黄），主有喜庆、财运。',
        '白色': '面部苍白，主有丧事或健康问题。',
    },
    '《冰鉴》神骨篇要义': {
        '精神': '一身精神，具乎两目。目清而有神者聪慧；目浊而无神者愚钝。',
        '骨相': '一身骨相，具乎面部。骨格清奇者贵，骨格粗俗者贱。',
        '刚柔': '内刚外柔者心刚面柔，内柔外刚者心柔面刚。刚柔得宜者成事。',
    },
}

# ==================== 输出 ====================

def format_hand_rules() -> str:
    out = []
    out.append("=" * 58)
    out.append("【手相分析框架】《麻衣神相》《柳庄相法》")
    out.append("=" * 58)
    out.append("")
    for section, items in HAND_RULES.items():
        out.append(f"【{section}】")
        for name, desc in items.items():
            out.append(f"  {name}：{desc}")
        out.append("")
    out.append("【分析要点】")
    out.append("  1. 先看掌型定性格基调")
    out.append("  2. 再看三线定健康、智慧、感情")
    out.append("  3. 手丘辅助判断各领域倾向")
    out.append("  4. 特殊纹路作为补充信号")
    out.append("")
    out.append("【AI分析指引】")
    out.append("  请提供手相照片（掌心向上，光线充足）。")
    out.append("  AI 将结合以上典籍规则和图片分析，给出解读。")
    return "\n".join(out)


def format_face_rules() -> str:
    out = []
    out.append("=" * 58)
    out.append("【面相分析框架】《麻衣神相》《冰鉴》")
    out.append("=" * 58)
    out.append("")
    for section, items in FACE_RULES.items():
        out.append(f"【{section}】")
        for name, desc in items.items():
            out.append(f"  {name}：{desc}")
        out.append("")
    out.append("【分析要点】")
    out.append("  1. 先看三停定早中晚运")
    out.append("  2. 再看五官定性格、财运、情谊")
    out.append("  3. 五岳辅助判断贵贱格局")
    out.append("  4. 气色判断当前运势")
    out.append("")
    out.append("【AI分析指引】")
    out.append("  请提供正面面部照片（光线充足、表情自然）。")
    out.append("  AI 将结合以上典籍规则和图片分析，给出解读。")
    return "\n".join(out)


# ==================== 主函数 ====================

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    if len(sys.argv) < 2 or sys.argv[1] in ('--help', '-h'):
        print("手相面相推演工具 v1.0（《麻衣神相》《冰鉴》）")
        print("用法:")
        print("  python xiangfa.py hand     # 手相分析框架与典籍规则")
        print("  python xiangfa.py face     # 面相分析框架与典籍规则")
        print("  python xiangfa.py both     # 手相+面相完整框架")
        print("")
        print("说明：本模块输出典籍规则和分析框架，")
        print("      AI模型使用 Read 工具读取用户图片进行实际分析。")
        sys.exit(0)

    mode = sys.argv[1].lower()

    if mode == 'hand':
        print(format_hand_rules())
        result = {'mode': 'hand', 'rules': HAND_RULES}
    elif mode == 'face':
        print(format_face_rules())
        result = {'mode': 'face', 'rules': FACE_RULES}
    elif mode == 'both':
        print(format_hand_rules())
        print("")
        print(format_face_rules())
        result = {'mode': 'both', 'hand_rules': HAND_RULES, 'face_rules': FACE_RULES}
    else:
        print(json.dumps(error_response("INVALID_MODE",
                                        f"未知模式：{mode}，支持 hand/face/both"),
                         ensure_ascii=False, indent=2))
        sys.exit(1)

    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
