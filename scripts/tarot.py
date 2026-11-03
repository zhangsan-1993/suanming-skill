#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
塔罗牌自动抽牌脚本
运行方式：python tarot.py --question "王琳今天的面试情况" --spread three
支持牌阵：single(单张), three(三牌阵)
"""

import random
import argparse
import json
import sys
from datetime import datetime

# 大阿尔卡那 22张
MAJOR_ARCANA = [
    {"id": 0, "name": "愚者", "upright": "新开始、冒险、纯真出发", "reversed": "鲁莽、逃避责任、准备不足"},
    {"id": 1, "name": "魔术师", "upright": "意志力、技能运用、主动创造", "reversed": "操纵、才能未发挥、欺骗"},
    {"id": 2, "name": "女祭司", "upright": "直觉、潜意识、等待时机", "reversed": "隐藏秘密、直觉受阻、表面功夫"},
    {"id": 3, "name": "女皇", "upright": "丰收、创造力、母性、感官享受", "reversed": "依赖、创造力受阻、过度放纵"},
    {"id": 4, "name": "皇帝", "upright": "权威、稳固基础、掌控", "reversed": "控制欲过强、缺乏弹性、独裁"},
    {"id": 5, "name": "教皇", "upright": "传统、精神导师、信仰体系", "reversed": "墨守成规、迷信、错误建议"},
    {"id": 6, "name": "恋人", "upright": "选择、关系、价值观对齐", "reversed": "关系失调、错误选择、内心矛盾"},
    {"id": 7, "name": "战车", "upright": "意志胜利、前进、自我控制", "reversed": "失控、方向迷失、强迫推进"},
    {"id": 8, "name": "力量", "upright": "内在勇气、耐心、温柔克制", "reversed": "怀疑自我、软弱、失去信心"},
    {"id": 9, "name": "隐士", "upright": "沉思、内省、独处寻答案", "reversed": "孤立无援、拒绝帮助、过度退缩"},
    {"id": 10, "name": "命运之轮", "upright": "转机、命运轮转、好运来临", "reversed": "坏运循环、无法掌控、停滞不前"},
    {"id": 11, "name": "正义", "upright": "公平、因果、清醒判断", "reversed": "不公正、偏见、逃避责任"},
    {"id": 12, "name": "倒吊人", "upright": "暂停、换角度看问题、自我牺牲", "reversed": "延迟受苦无意义、固执不肯放手"},
    {"id": 13, "name": "死神", "upright": "结束与转化、告别旧章", "reversed": "拒绝改变、陈旧腐朽、强撑"},
    {"id": 14, "name": "节制", "upright": "平衡、耐心调和、中庸之道", "reversed": "极端、失衡、缺乏耐心"},
    {"id": 15, "name": "恶魔", "upright": "物质束缚、执念、欲望", "reversed": "摆脱束缚、觉醒、打破依赖"},
    {"id": 16, "name": "塔", "upright": "突变、崩塌、旧结构打破", "reversed": "避免灾难、震荡延缓、拒绝改变"},
    {"id": 17, "name": "星星", "upright": "希望、疗愈、平静信念", "reversed": "失望、不信任、自我怀疑"},
    {"id": 18, "name": "月亮", "upright": "幻觉、迷雾、潜意识恐惧", "reversed": "释放恐惧、拨云见日、真相浮现"},
    {"id": 19, "name": "太阳", "upright": "活力、喜悦、清晰成功", "reversed": "短暂快乐、过于乐观、活力受阻"},
    {"id": 20, "name": "审判", "upright": "觉醒、召唤、重生、清算", "reversed": "拒绝觉醒、自我怀疑、过去阴影"},
    {"id": 21, "name": "世界", "upright": "完成、整合、世界在手", "reversed": "未竟之事、拖延完成、闭门造车"},
]

# 小阿尔卡那 - 权杖组
WANDS = [
    {"name": "权杖1", "upright": "新项目启动、有创意冲劲", "reversed": "延迟出发、缺乏动力"},
    {"name": "权杖2", "upright": "规划未来、扩张视野", "reversed": "犹豫不决、计划受阻"},
    {"name": "权杖3", "upright": "进展顺利、等待成果归来", "reversed": "延误、沟通问题"},
    {"name": "权杖4", "upright": "成就庆祝、稳固家园", "reversed": "庆祝未到、不稳定"},
    {"name": "权杖5", "upright": "竞争、磨擦、各执己见", "reversed": "冲突避免、和解"},
    {"name": "权杖6", "upright": "胜利归来、公认成就", "reversed": "延迟认可、骄傲受损"},
    {"name": "权杖7", "upright": "坚守立场、迎挑战", "reversed": "放弃阵地、被压倒"},
    {"name": "权杖8", "upright": "快速进展、消息飞来", "reversed": "延误、消息混乱"},
    {"name": "权杖9", "upright": "坚韧、最后关头防守", "reversed": "疲惫放弃、过度防卫"},
    {"name": "权杖10", "upright": "责任重担、接近终点", "reversed": "放下重担、无谓承担"},
    {"name": "权杖侍者", "upright": "热情、勇于尝试、信使", "reversed": "鲁莽、三分钟热度"},
    {"name": "权杖骑士", "upright": "行动迅速、热忱冲劲", "reversed": "冲动鲁莽、虎头蛇尾"},
    {"name": "权杖王后", "upright": "自信活力、慷慨感召", "reversed": "嫉妒、善变、骄傲"},
    {"name": "权杖国王", "upright": "远见领袖、鼓励他人", "reversed": "独裁、好大喜功"},
]

# 小阿尔卡那 - 圣杯组
CUPS = [
    {"name": "圣杯1", "upright": "情感新开始、爱的涌现", "reversed": "情感受阻、内心空洞"},
    {"name": "圣杯2", "upright": "两情相悦、合作伙伴", "reversed": "关系不和、失衡"},
    {"name": "圣杯3", "upright": "庆祝友谊、喜事来临", "reversed": "过度放纵、三角关系"},
    {"name": "圣杯4", "upright": "内省、对机遇漠然", "reversed": "重新关注、接受馈赠"},
    {"name": "圣杯5", "upright": "失落哀伤、只见损失", "reversed": "接受失去、向前看"},
    {"name": "圣杯6", "upright": "怀旧、童年记忆、善意", "reversed": "活在过去、天真受害"},
    {"name": "圣杯7", "upright": "选择太多、幻想迷惑", "reversed": "意志清晰、决策落地"},
    {"name": "圣杯8", "upright": "放弃旧情况、追寻更深", "reversed": "放弃逃避、直面情感"},
    {"name": "圣杯9", "upright": "愿望成真、满足感", "reversed": "不满足、愿望延迟"},
    {"name": "圣杯10", "upright": "圆满幸福、家庭和谐", "reversed": "家庭矛盾、幸福破碎"},
    {"name": "圣杯侍者", "upright": "情感探索、创意信息", "reversed": "情绪不稳、逃避情感"},
    {"name": "圣杯骑士", "upright": "浪漫追求、感性行动", "reversed": "情绪化、承诺困难"},
    {"name": "圣杯王后", "upright": "共情、温柔智慧", "reversed": "情绪压抑、依赖"},
    {"name": "圣杯国王", "upright": "情感成熟、有担当", "reversed": "情感操控、压抑感受"},
]

# 小阿尔卡那 - 宝剑组
SWORDS = [
    {"name": "宝剑1", "upright": "清晰突破、真相大白", "reversed": "思维混乱、真相受阻"},
    {"name": "宝剑2", "upright": "左右为难、暂时回避", "reversed": "被迫抉择、僵局突破"},
    {"name": "宝剑3", "upright": "心碎、背叛、悲痛", "reversed": "从痛苦复原、释怀"},
    {"name": "宝剑4", "upright": "休息恢复、暂停沉淀", "reversed": "重返行动、无法休息"},
    {"name": "宝剑5", "upright": "冲突后的失败、恶性竞争", "reversed": "和解、妥协"},
    {"name": "宝剑6", "upright": "过渡期、离开困境", "reversed": "无法前进、带着包袱走"},
    {"name": "宝剑7", "upright": "策略行动、秘密进行", "reversed": "被揭穿、良心发现"},
    {"name": "宝剑8", "upright": "自我束缚、思维困境", "reversed": "解放自我、思维突破"},
    {"name": "宝剑9", "upright": "焦虑失眠、最坏想象", "reversed": "焦虑减轻、放下担忧"},
    {"name": "宝剑10", "upright": "痛苦终结、到底了", "reversed": "拒绝放下、延续痛苦"},
    {"name": "宝剑侍者", "upright": "好奇探索、敏锐观察", "reversed": "言语伤人、冒失"},
    {"name": "宝剑骑士", "upright": "直接行动、清晰沟通", "reversed": "草率决定、争辩"},
    {"name": "宝剑王后", "upright": "清醒智慧、看透人心", "reversed": "刻薄、以牙还牙"},
    {"name": "宝剑国王", "upright": "公正权威、理性决策", "reversed": "冷酷、滥用权力"},
]

# 小阿尔卡那 - 五角星组
PENTACLES = [
    {"name": "五角星1", "upright": "财富新开始、实际机会", "reversed": "机会错过、物质损失"},
    {"name": "五角星2", "upright": "平衡多件事、灵活应变", "reversed": "手忙脚乱、失衡"},
    {"name": "五角星3", "upright": "技能认可、团队合作", "reversed": "缺乏协作、工作质量差"},
    {"name": "五角星4", "upright": "守住资产、保守吝啬", "reversed": "放下执着、财务流动"},
    {"name": "五角星5", "upright": "物质困难、被排除在外", "reversed": "复原、重新得到支持"},
    {"name": "五角星6", "upright": "慷慨给予、财务平衡", "reversed": "施受不均、债务"},
    {"name": "五角星7", "upright": "等待收获、辛勤回报", "reversed": "缺乏耐心、徒劳投资"},
    {"name": "五角星8", "upright": "精进技艺、专注工作", "reversed": "完美主义、技能停滞"},
    {"name": "五角星9", "upright": "自给自足、独立富足", "reversed": "过度依赖、财务失控"},
    {"name": "五角星10", "upright": "家族财富、物质圆满", "reversed": "财务纠纷、家族压力"},
    {"name": "五角星侍者", "upright": "学习新技能、踏实机会", "reversed": "缺乏专注、目标不清"},
    {"name": "五角星骑士", "upright": "稳步前进、可靠负责", "reversed": "停滞不前、固执"},
    {"name": "五角星王后", "upright": "务实温暖、物质照顾", "reversed": "过度担忧、自我怀疑"},
    {"name": "五角星国王", "upright": "稳健财富、商业智慧", "reversed": "贪婪固执、物质执念"},
]

# 整副牌
ALL_CARDS = MAJOR_ARCANA + WANDS + CUPS + SWORDS + PENTACLES

def draw_cards(num_cards=3):
    """洗牌抽牌，随机决定正逆位"""
    # 洗牌
    shuffled = ALL_CARDS.copy()
    random.shuffle(shuffled)
    # 抽牌
    drawn = shuffled[:num_cards]
    # 随机决定正逆位（True=正位，False=逆位）
    orientations = [random.choice([True, False]) for _ in range(num_cards)]
    return list(zip(drawn, orientations))

def format_card(card, is_upright):
    """格式化单张牌信息"""
    orientation = "正位" if is_upright else "逆位"
    meaning = card["upright"] if is_upright else card["reversed"]
    return f"【{card['name']} {orientation}】- {meaning}"

def main():
    def error_response(code, details):
        return {"success": False,
                "error": {"code": code,
                          "details": details if isinstance(details, list) else [details]}}

    parser = argparse.ArgumentParser(description="塔罗抽牌")
    parser.add_argument("--question", "-q", type=str, default="", help="所测之事")
    parser.add_argument("--spread", "-s", type=str, default="three", help="牌阵: single(单张), three(三牌阵)")
    args = parser.parse_args()

    now = datetime.now()
    print("=" * 60)
    print(f"        塔罗牌占卜")
    print(f"  抽牌时间：{now.strftime('%Y年%m月%d日 %H:%M:%S')}")
    if args.question:
        print(f"  所问之事：{args.question}")
    print("=" * 60)

    # 确定抽牌数量
    if args.spread == "single":
        num = 1
        positions = ["结果"]
    elif args.spread == "three":
        num = 3
        positions = ["过去/根源", "现在/现状", "未来/结果"]
    else:
        num = 3
        positions = ["过去/根源", "现在/现状", "未来/结果"]

    # 抽牌
    drawn = draw_cards(num)

    print()
    cards_data = []
    for i, (card, is_upright) in enumerate(drawn):
        if num > 1:
            print(f"{positions[i]}：")
        print("  " + format_card(card, is_upright))
        print()
        cards_data.append({
            'position': positions[i],
            'name': card['name'],
            'upright': is_upright,
            'orientation': '正位' if is_upright else '逆位',
            'meaning': card['upright'] if is_upright else card['reversed'],
            'id': card.get('id', 22 + i)  # Minor arcana don't have id, use offset
        })

    if args.spread == "three":
        print("牌阵说明：三牌阵依次代表事情的根源背景、当前状态、最终走向")
    
    print("=" * 60)
    print("抽牌完成，请根据以上牌面进行解读。")
    print("=" * 60)

    # JSON输出
    result = {
        'time': now.isoformat(),
        'question': args.question,
        'spread': args.spread,
        'cards': cards_data
    }
    print("\n\n[JSON_OUTPUT]")
    print(json.dumps({"success": True, "data": result}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
