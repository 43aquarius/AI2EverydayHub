# -*- coding: utf-8 -*-
"""双场景回归:13:40轮(年龄/星数/脑补超标,软推荐2处不超标)
         和 13:36轮(软推荐5处超标)"""
import sys
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
from summarizer import _detect_repetition

# ---- 场景A: 13:40 轮实际问题(年龄句8次/星数句5次/脑补4次/软推荐2次)
items_a = [
    {"rank": 1, "summary": "XERJ是个本地AI搜索工具。这个项目才4个月,已经攒了7360星,看来很多人都在寻找更高效的代码搜索方式。"},
    {"rank": 2, "summary": "ai-memory是个解决记忆断档问题的方案。5个月时间已经获得了9678星。"},
    {"rank": 3, "summary": "Android官方推出的技能库,是一系列AI优化的模块化指令和资源。"},
    {"rank": 4, "summary": "Laya是个多语言决策引擎。这个项目才29天,已经获得了33222星,看来大家对这种轻量级决策引擎很感兴趣。"},
    {"rank": 5, "summary": "Strata是个推理引擎。这个项目22天前创建,已经获得了26602星,说明很多人想在家用电脑上运行大模型。"},
    {"rank": 6, "summary": "dsh插件,这个项目22天前创建,已经获得了20668星。"},
    {"rank": 7, "summary": "Compositor是Mac上的Photoshop替代品。这个项目可能正适合你。"},
    {"rank": 8, "summary": "PdfCraft是一个用纯Rust写的开源PDF阅读器。这个工具值得一试。16天前创建,星数已经破万五了。"},
    {"rank": 9, "summary": "openai/math是数学手稿集合。才10天,已经获得了15069星,说明很多人对AI生成的数学研究很感兴趣。"},
    {"rank": 10, "summary": "Magpie是一个模型切换工具。23天前创建,星数已经超过一万四。"},
]
fa = _detect_repetition(items_a)
labels_a = " | ".join(p for p, _ in fa)
print("场景A(13:40轮) 检测到:")
for p, r in fa:
    print(f"  「{p}」→ {len(r)}条")
assert "年龄数据句" in labels_a and "星数获得句" in labels_a \
       and "脑补群众反应" in labels_a, "场景A三类未全抓到"

# ---- 场景B: 13:36 轮软推荐5处(应触发,其余不超标)
items_b = [
    {"rank": 1, "summary": "还在挨个文件翻代码?XERJ是个AI驱动的本地数据搜索工具,自动索引代码文档。"},
    {"rank": 2, "summary": "Android skills是个专门为AI优化的开发指导库。"},
    {"rank": 3, "summary": "ai-memory解决了不同AI编码助手之间的记忆共享问题。"},
    {"rank": 4, "summary": "支持100多种语言,一次前向传播只要33毫秒,处理大量非英语文本时特别有用。"},
    {"rank": 5, "summary": "想在家用电脑上运行大型AI模型,这个项目很合适。"},
    {"rank": 6, "summary": "想免费用前沿AI模型,这个项目很实用。"},
    {"rank": 7, "summary": "觉得Photoshop太贵,又觉得GIMP不够熟悉的,可以试试这个。"},
    {"rank": 8, "summary": "需要处理大量PDF文档,这个工具很合适。"},
    {"rank": 9, "summary": "719份手稿摆在那就是素材库,翻翻就知道哪些题能秒。"},
    {"rank": 10, "summary": "使用多个AI助手多个账户的用户会需要这个。"},
]
fb = _detect_repetition(items_b)
labels_b = " | ".join(p for p, _ in fb)
print("场景B(13:36轮软推荐) 检测到:")
for p, r in fb:
    print(f"  「{p}」→ {len(r)}条 {r}")
assert "结尾软推荐" in labels_b, "软推荐5处未触发"
assert "年龄数据句" not in labels_b and "星数获得句" not in labels_b, \
    "场景B误报年龄/星数"
print("✓ 双场景验证通过:该抓的抓到,不该抓的不误报")
