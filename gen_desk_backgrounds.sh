#!/bin/bash
# 生成小黑盒封面用的两个书桌场景背景(可长期复用, 文字用HTML叠加)
# 风格参照用户上传的"软件推荐封面"参考图: 明亮书桌+清新科技感
set -e
OUT=/home/z/my-project/github-hot-heybox/assets
mkdir -p $OUT

# 背景A: GitHub榜单帖用(屏幕显示代码/图表)
z-ai image -p "Bright fresh tech-style 3D render of a cozy work desk scene, isometric-ish front view. A desktop monitor on the right side displaying colorful code editor and star charts, mechanical keyboard, white mouse, white ceramic mug, a neat stack of books, small green potted plant, large window behind showing clear blue sky and soft clouds. Light sky-blue and cream color palette, soft daylight from window, clean and airy atmosphere, upper-left area of the image is clean empty sky-blue wall space for text overlay, high quality, detailed, C4D blender style, no text, no words, no letters" -o $OUT/desk_bg_github.png -s 1344x768

# 背景B: AGI日报帖用(屏幕显示AI神经网络, 色调偏紫蓝科技)
z-ai image -p "Bright fresh tech-style 3D render of a cozy work desk scene, isometric-ish front view. A desktop monitor on the right side displaying glowing neural network visualization with nodes and connections in violet and cyan, mechanical keyboard, white mouse, white ceramic mug, a neat stack of books, small green potted plant, a cute small robot figurine beside the monitor, large window behind showing clear blue sky and soft clouds. Light sky-blue and cream color palette with subtle violet accents, soft daylight, clean airy atmosphere, upper-left area of the image is clean empty wall space for text overlay, high quality, detailed, C4D blender style, no text, no words, no letters" -o $OUT/desk_bg_agi.png -s 1344x768

echo "=== 生成完成 ==="
ls -la $OUT/
