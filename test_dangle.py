# -*- coding: utf-8 -*-
"""悬垂受众句 regex 验证"""
import sys, re
sys.path.insert(0, "/home/z/my-project/github-hot-heybox")
import py_compile
py_compile.compile("/home/z/my-project/github-hot-heybox/summarizer.py",
                   doraise=True)
print("✓ 语法检查通过")

from summarizer import _REGEX_PATTERNS
dangle = [rx for rx, label in _REGEX_PATTERNS if "悬垂" in label][0]

# 应命中(上轮 dry-run 实际出现的悬垂句)
hits = [
    "想免费使用先进AI模型又不想折腾API键的，它简化了模型接入流程。",
    "需要处理PDF文档的，这个工具完全用Rust编写，性能优异。",
    "需要快速处理多语言文本分类任务的，这个工具比传统方法快得多。",
    "研究数学或对AI在数学领域表现感兴趣的，它展示了AI的能力。",
    "使用多个AI代理或多个账户的，这个工具简化了代理切换流程。",
    "想在家用电脑上运行大型AI模型而不依赖云服务的，它完全在本地运行。",
]
# 不应命中(正常句子)
misses = [
    "在使用的时候，它会自动切换到下一个账户。",        # 的时候,它
    "如果你需要的话，这个功能可以关掉。",              # 的话,这个
    "想要省钱的，可以看看这个工具。",                  # 的,可以(非它/这个开头)
    "安装简单，一条命令就能完成索引和设置。",           # 无悬垂
    "它将每个代理的模型、密钥和URL统一管理，使用很方便。",
]
ok = True
for s in hits:
    if not re.search(dangle, s):
        print(f"  ✗ 未命中: {s[:30]}"); ok = False
for s in misses:
    if re.search(dangle, s):
        print(f"  ✗ 误报: {s[:30]}"); ok = False
assert ok
print("✓ 悬垂句检测:6命中/0误报")
