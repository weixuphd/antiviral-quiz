#!/usr/bin/env python3
"""Build comprehensive index.html for all 46 pharmacology chapters."""
import json, os

PARTS = [
    ("第一篇  总论", [
        (1, "绪论", 50, "10+35+5"),
        (2, "药物效应动力学", 75, "15+52+8"),
        (3, "药物代谢动力学", 100, "20+70+10"),
        (4, "影响药物效应的因素及合理用药原则", 50, "10+35+5"),
    ]),
    ("第二篇  外周神经系统药理学", [
        (5, "神经系统药理概论", 100, "20+70+10"),
        (6, "胆碱受体激动药", 30, "6+21+3"),
        (7, "抗胆碱酯酶药和胆碱酯酶复活药", 50, "10+35+5"),
        (8, "胆碱受体阻断药", 50, "10+35+5"),
        (9, "肾上腺素受体激动药", 50, "10+35+5"),
        (10, "肾上腺素受体阻断药", 50, "10+35+5"),
        (11, "局部麻醉药", 30, "6+21+3"),
        (12, "全身麻醉药", 30, "6+21+3"),
    ]),
    ("第三篇  中枢神经系统药理学", [
        (13, "镇静催眠药和促觉醒药", 50, "10+35+5"),
        (14, "抗癫痫药与抗惊厥药", 50, "10+35+5"),
        (15, "治疗神经退行性变性疾病药物", 50, "10+35+5"),
        (16, "抗精神失常药", 50, "10+35+5"),
        (17, "阿片类镇痛药、药物依赖性与药物滥用", 75, "15+52+8"),
        (18, "解热镇痛抗炎药", 75, "15+52+8"),
        (19, "影响其他自身活性物质的药物", 75, "15+52+8"),
        (20, "免疫调节药", 50, "10+35+5"),
    ]),
    ("第四篇  心血管系统药理学", [
        (21, "利尿药与脱水药", 30, "6+21+3"),
        (22, "抗心律失常药", 75, "15+52+8"),
        (23, "抗心肌缺血药", 50, "10+35+5"),
        (24, "调血脂药和抗动脉粥样硬化药", 50, "10+35+5"),
        (25, "抗高血压药", 75, "15+52+8"),
        (26, "抗慢性心功能不全药", 75, "15+52+8"),
        (27, "作用于血液及造血器官的药物", 75, "15+52+8"),
        (28, "作用于呼吸系统的药物", 50, "10+35+5"),
        (29, "作用于消化系统的药物", 75, "15+52+8"),
    ]),
    ("第五篇  内分泌系统药理学", [
        (30, "子宫平滑肌兴奋药和抑制药", 30, "6+21+3"),
        (31, "肾上腺皮质激素类药物", 50, "10+35+5"),
        (32, "抗糖尿病药", 50, "10+35+5"),
        (33, "甲状腺激素和抗甲状腺药", 30, "6+21+3"),
        (34, "性激素类药与避孕药", 50, "10+35+5"),
        (35, "抗骨质疏松药", 30, "6+21+3"),
    ]),
    ("第七篇  化学治疗药物", [
        (36, "抗菌药物概论", 100, "20+70+10"),
        (37, "β-内酰胺类抗生素及其他作用于细胞壁的抗生素", 100, "20+70+10"),
        (38, "大环内酯类、林可霉素类及其他抗生素", 50, "10+35+5"),
        (39, "氨基糖苷类及多黏菌素类抗生素", 75, "15+52+8"),
        (40, "四环素类及氯霉素类抗生素", 50, "10+35+5"),
        (41, "人工合成抗菌药", 100, "20+70+10"),
        (42, "抗结核病药及抗麻风药", 50, "10+35+5"),
        (43, "抗真菌药", 50, "10+35+5"),
        (44, "抗病毒药", 100, "20+70+10"),
        (45, "抗寄生虫药", 50, "10+35+5"),
        (46, "抗恶性肿瘤药", 100, "20+70+10"),
    ]),
]

COLORS = [
    ("#ebf4ff", "#2b6cb0"),  # blue
    ("#f0fff4", "#276749"),  # green
    ("#fffbeb", "#975a16"),  # amber
    ("#faf5ff", "#6b46c1"),  # purple
    ("#fff5f5", "#c53030"),  # red
    ("#f0fff4", "#276749"),  # green
    ("#ebf8ff", "#2c5282"),  # blue
    ("#fffbeb", "#975a16"),  # amber
    ("#faf5ff", "#6b46c1"),  # purple
    ("#fff5f5", "#c53030"),  # red
    ("#ebf4ff", "#2b6cb0"),  # blue
]

total_questions = 0

cards_html = ""
color_idx = 0
for part_title, chapters in PARTS:
    cards_html += f'\n<div class="section-title">{part_title}</div>\n'
    for ch_num, ch_title, q_count, q_types in chapters:
        color = COLORS[color_idx % len(COLORS)]
        cards_html += f'''<div class="card c{color_idx % 8 + 1}"><a href="ch{ch_num:02d}_cn.html">
<div class="card-num">{ch_num}</div>
<div class="card-info"><div class="card-title">{ch_title}</div><div class="card-meta"><span>{q_count}题</span><span>{q_types}</span></div></div>
<div class="arr">&#8250;</div>
</a></div>
'''
        color_idx += 1
        total_questions += q_count

FULL_HTML = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="药理学题库">
<meta itemprop="name" content="药理学题库">
<meta itemprop="description" content="药理学全教材题库训练 · 共46章 {total_questions}题">
<meta name="twitter:card" content="summary">
<title>药理学题库</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f0f4f8;color:#1a202c;min-height:100vh}}
.header{{background:linear-gradient(135deg,#2c5282,#38a169);color:#fff;padding:28px 16px 24px;text-align:center}}
.header h1{{font-size:1.5rem;font-weight:700;margin-bottom:5px}}
.header p{{font-size:.85rem;opacity:.85;margin-top:4px}}
.container{{max-width:680px;margin:0 auto;padding:12px}}
.section-title{{font-size:.82rem;font-weight:600;color:#4a5568;padding:14px 8px 6px;text-transform:uppercase;letter-spacing:.5px}}
.card{{background:#fff;border-radius:10px;margin-bottom:4px;box-shadow:0 1px 3px rgba(0,0,0,.06);overflow:hidden}}
.card a{{display:flex;align-items:center;padding:12px 16px;text-decoration:none;color:#1a202c;transition:background .15s}}
.card a:active{{background:#edf2f7}}
.card-num{{width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.8rem;margin-right:12px;flex-shrink:0}}
.card-info{{flex:1;min-width:0}}
.card-title{{font-size:.88rem;font-weight:600;margin-bottom:2px}}
.card-meta{{font-size:.7rem;color:#718096}}
.card-meta span{{margin-right:8px}}
.arr{{color:#a0aec0;font-size:1rem;margin-left:6px}}
.footer{{text-align:center;padding:20px;color:#a0aec0;font-size:.72rem}}
.c1 .card-num{{background:#ebf4ff;color:#2b6cb0}}
.c2 .card-num{{background:#f0fff4;color:#276749}}
.c3 .card-num{{background:#fffbeb;color:#975a16}}
.c4 .card-num{{background:#faf5ff;color:#6b46c1}}
.c5 .card-num{{background:#fff5f5;color:#c53030}}
.c6 .card-num{{background:#f0fff4;color:#276749}}
.c7 .card-num{{background:#ebf8ff;color:#2c5282}}
.c8 .card-num{{background:#fffbeb;color:#975a16}}
</style>
</head>
<body>
<div class="header">
<h1>药理学 · 题库训练</h1>
<p>全教材共46章 · 总计{total_questions}题 · 各章含是非题/单选题/简答题(多选)</p>
</div>
<div class="container">
{cards_html}
</div>
<div class="footer">药理学题库 &copy; 2026 · 仅供教学使用 · 有效期至2026-09-01</div>
</body>
</html>'''

output_path = os.path.join(os.path.dirname(__file__), "index.html")
with open(output_path, "w", encoding="utf-8") as f:
    f.write(FULL_HTML)
print(f"index.html written: {total_questions} questions across {color_idx} chapters")
