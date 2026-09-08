#!/usr/bin/env python3
"""生成讲义的打印安全版 Markdown。

三件事：
1) 符号替换 —— LibreOffice 对 emoji 以及 ▶ ⚠ ✔ 无字形，导出后**静默消失**（不是
   豆腐块，是什么都不剩），统一换成 CJK 字体自带的几何符号。源文件保持 emoji 不变。
2) 字形校验 —— 因为缺字形是静默的，替换后必须逐字复查：凡是落在装饰符号区、
   又不在 SAFE_DECOR 白名单里的字符，一律报错退出，不让缺字符的产物流到 PDF。
   新加装饰符号时，先确认它能渲染，再同时补 GLYPH_MAP 或 SAFE_DECOR。
3) 实体目录 —— pandoc --toc 在 docx 里只是个待更新的域，转 PDF 后是空白，
   因此从二级标题自行生成一份可见目录，插到【导读】之前。
"""
import sys

# 短语优先：带语义标签的整条先替，剩下的裸 emoji 由后面的兜底条目接住。
GLYPH_MAP = [
    ("📖 词汇注释", "■ 词汇注释"),
    ("📖 精读",     "◎ 精读"),
    ("🧩 语法聚焦", "★ 语法聚焦"),
    ("🎓 高考迁移", "※ 高考迁移"),
    ("🎓 IELTS 使用提醒", "※ IELTS 使用提醒"),
    ("🖊 续写素材", "❖ 续写素材"),
    # ⇢ 在 10.5pt 下与因果链用的 → 几乎分不开（→ 全文出现 58 次），换成 »
    ("⇢ 题型对接", "» 题型对接"), ("⇢", "»"),
    # 裸 emoji 兜底
    ("📖", "■"), ("📚", "■"), ("📝", "◇"), ("📌", "◇"), ("📊", "◇"),
    ("🎓", "※"), ("💡", "※"), ("🔑", "※"), ("🧩", "★"), ("🎯", "★"),
    ("🖊", "❖"), ("✍️", "❖"), ("✍", "❖"), ("📐", "◉"), ("📏", "◉"),
    ("✅", "★"), ("⭐", "★"), ("🌟", "★"), ("👉", "⇒"), ("➡️", "⇒"),
    ("❌", "✗"), ("⛔", "✗"), ("🚫", "✗"),
    ("⚠️", "▲"), ("⚠", "▲"), ("❗", "▲"), ("‼️", "▲"), ("❓", "◇"),
    ("❝", "「"), ("❞", "」"), ("▶", "●"), ("▷", "○"), ("✔", "✓"), ("✘", "✗"),
]

# 白名单里的每个字符都是**实测渲染过**的（探针页导出 PDF 再看像素），不是查字体
# cmap 判定的——LibreOffice 的回退链比 style-spec 声明的四个字族宽得多：
# ✦ ✗ ⇢ ✧ 在 Georgia / Noto Serif CJK / Carlito / YaHei 里全都查不到，实测却正常显示。
# 所以往这里加字符的唯一判据是「在探针页上看见它」，查字体表会误判两个方向。
SAFE_DECOR = set(
    "←↑→↓↔⇐⇒⇔"                     # 箭头：因果链与逻辑图（⇢ 已映射为 »，不在白名单）
    "①②③④⑤⑥⑦⑧⑨⑩"                 # 释义分层
    "─│┌┐└┘├┤┬┴┼"                   # 制表符：树形结构
    "■□▪▫●○◆◇◎◉❖△▲▽▼"            # 几何符号：模块标记
    "★☆✦✧✓✗"                        # 星形与勾叉：迁移分级
    "≈≠≤≥±×÷»"                       # 数学与引导符号
)
# 装饰符号区：这个区间内的字符要么在白名单里，要么必须被 GLYPH_MAP 替换掉。
DECOR_LO, DECOR_HI = 0x2190, 0x2BFF
VS16 = "️"

DECOR = "◆■★◎※✦◇● "
TOC_ANCHOR = "【 导读"


def check(text: str) -> None:
    """替换后复查：任何可能缺字形的字符都要在这里被拦下。"""
    bad = {}
    for ln, line in enumerate(text.split("\n"), 1):
        for ch in line:
            o = ord(ch)
            risky = o >= 0x1F000 or (DECOR_LO <= o <= DECOR_HI and ch not in SAFE_DECOR)
            if risky:
                bad.setdefault(ch, ln)
    if not bad:
        return
    print("字形校验失败：以下字符 LibreOffice 无字形，导出后会静默消失。", file=sys.stderr)
    for ch, ln in sorted(bad.items()):
        print(f"  第 {ln} 行  {ch}  U+{ord(ch):04X}", file=sys.stderr)
    print("请在 scripts/print_variant.py 的 GLYPH_MAP 里加替换条目；"
          "确认能渲染的话，加进 SAFE_DECOR 并同步 references/style-spec.md。",
          file=sys.stderr)
    sys.exit(1)


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    for a, b in GLYPH_MAP:
        s = s.replace(a, b)
    s = s.replace(VS16, "")   # 落单的变体选择符，去掉不影响字形
    check(s)

    lines = s.split("\n")
    toc = ["## 目录", ""]
    for ln in lines:
        if ln.startswith("## ") and ln[3:].strip() != "目录":
            toc.append("- " + ln[3:].strip().lstrip(DECOR))
    toc += ["", "---", ""]

    for i, ln in enumerate(lines):
        if TOC_ANCHOR in ln:
            lines[i:i] = toc
            break
    else:
        print(f"找不到目录插入点「{TOC_ANCHOR}」，讲义缺少【导读】块。", file=sys.stderr)
        sys.exit(1)

    open(dst, "w", encoding="utf-8").write("\n".join(lines))
    print(f"  打印版已生成（目录 {len(toc) - 4} 条）")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
