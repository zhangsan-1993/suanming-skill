# 算命-skill

专业命理推演 Skill（WorkBuddy / Agent 技能包）。覆盖八字、紫微斗数、六爻、梅花易数、周易义理、奇门遁甲、太乙神数、大六壬、风水堪舆、星座占星、手相面相、塔罗等体系。

核心特点：**本地天文算法排盘（不依赖外部网站）+ P0/P1 双重验证 + 典籍规则标注**。

## 功能

| 体系 | 能力 | 脚本 |
|------|------|------|
| 八字命理 | 四柱/十神/旺衰/用神/大运/流年 | `scripts/bazi.py` |
| 紫微斗数 | 十二宫/十四主星/四化 | `scripts/ziwei.py` |
| 六爻 | 摇钱起卦/时间起卦、纳甲、六亲六神 | `scripts/liuyao.py` / `scripts/qigua.py` |
| 梅花易数 | 时间/数字/物象起卦、体用生克 | `scripts/meihua.py` |
| 周易义理 | 六十四卦卦辞爻辞解读 | `scripts/yijing.py` |
| 奇门遁甲 | 定局/八门/九星/三奇 | `scripts/qimen.py` |
| 大六壬 | 四课三传 | `scripts/liuren.py` |
| 星座占星 | 星盘（依赖 ephem） | `scripts/astrology.py` |
| 手相面相 | 三停/五官/气色判读 | `scripts/xiangfa.py` |
| 塔罗 | 抽牌解读 | `scripts/tarot.py` |

## 安装

```bash
pip install -r requirements.txt   # ephem、lunardate
```

- `ephem`：仅星座占星需要
- `lunardate`：仅农历日期展示需要，缺失不影响排盘

## 使用

命令行直调（输出为"人读报告 + `[JSON_OUTPUT]` 后的 JSON"）：

```bash
python scripts/bazi.py 1993 6 18 15 女        # 八字排盘
python scripts/ziwei.py 1993 6 18 15 女       # 紫微排盘
python scripts/liuyao.py auto "何时跳槽"        # 六爻起卦
python scripts/tarot.py                       # 塔罗抽牌
```

库接口：

```python
from divination_engine import DivinationEngine
engine = DivinationEngine()
result = engine.full_process(1993, 6, 18, 15, '女', longitude=120.0)
engine.export_report('/tmp/report.md')
```

完整工作流（P0 验证 → 典籍规则匹配 → P1 验证 → 推演 → 报告）见 `SKILL.md`。

## 计算口径

- 二十四节气：Meeus 太阳视黄经公式，1900–2100 精度 ±1 分钟
- 干支：儒略日法，锚点 2000-01-01 戊午（已对照 lunar_python 权威库验证）
- 年柱以立春精确时刻为界；月柱按十二节 + 五虎遁；时柱按五鼠遁

## 测试

```bash
python -m pytest tests/ -v
```

## 免责声明

本项目输出的命理推演**仅供娱乐与文化参考**，不构成对任何人的性格、心理、医疗、法律或命运的判断。重要决策请基于事实与专业人士意见。

## License

[MIT](LICENSE)
