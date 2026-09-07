#!/usr/bin/env python3
"""生成讲义的打印安全版 Markdown。

两件事：
1) 符号替换 —— LibreOffice 对 emoji 以及 ▶ ⚠ ✔ 无字形（导出后直接消失），
   统一换成 CJK 字体自带的几何符号。Markdown 源文件保持 emoji 不变。
2) 实体目录 —— pandoc --toc 在 docx 里只是个待更新的域，转 PDF 后是空白，
   因此从二级标题自行生成一份可见目录，插到【导读】之前。
"""
import sys

GLYPH_MAP = [
    ("📖 词汇注释", "■ 词汇注释"),
    ("📖 精读",     "◎ 精读"),
    ("🧩 语法聚焦", "★ 语法聚焦"),
    ("🎓 高考迁移", "※ 高考迁移"),
    ("📚", "■"), ("📌", "◇"), ("💡", "※"), ("✅", "★"), ("👉", "⇒"),
    ("⚠️", "▲"), ("⚠", "▲"), ("❝", "「"), ("▶", "●"), ("✔", "✓"),
]
DECOR = "◆■★◎※✦◇● "


def main(src, dst):
    s = open(src, encoding="utf-8").read()
    for a, b in GLYPH_MAP:
        s = s.replace(a, b)

    lines = s.split("\n")
    toc = ["## 目录", ""]
    for ln in lines:
        if ln.startswith("## ") and ln[3:].strip() != "目录":
            toc.append("- " + ln[3:].strip().lstrip(DECOR))
    toc += ["", "---", ""]

    for i, ln in enumerate(lines):
        if "【 导读" in ln:
            lines[i:i] = toc
            break
    open(dst, "w", encoding="utf-8").write("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
