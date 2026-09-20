"""排版设计 token —— 唯一源。

取值全部来自 references/style-spec.md，那份文件是从《外刊精读02/03》原件
OOXML 里提取的权威规格。改样式请先改规格文件，再改这里。
"""

# ── 颜色 ────────────────────────────────────────────────────
BODY  = "475569"   # 正文、译文
BOLD  = "1E293B"   # 加粗、原句回填、导读正文
HEAD  = "1A365D"   # En: 行、◆ 块标题、方框标题、封面、左竖条
NOTE  = "8B1E1E"   # 模块标题、▶ 词条头
MUTED = "64748B"   # 页眉页脚、封面署名
TINT_A = "F8FAFC"  # 导读 / 写在最后 底色
TINT_B = "F1F5F9"  # 精读 底色（略深，用于区分两类方框）

# ── 字体：按语义而非按语言分工 ──────────────────────────────
SERIF = "Georgia"                      # 西文正文
LABEL = "Calibri"                      # 西文标签、模块标题
CJK   = "Noto Serif CJK SC Medium"     # 中文常规
CJKB  = "Noto Serif CJK SC SemiBold"   # 中文加粗（靠切字族，不只靠 w:b）
UI    = "Microsoft YaHei"              # 页眉页脚、封面

# ── 字号（半磅）─────────────────────────────────────────────
SZ = 21            # 正文；原件正文无字号层级，全篇 21
SZ_FOOTER = 18
SZ_COVER_EN, SZ_COVER_CN, SZ_COVER_EYEBROW = 30, 23, 20

# ── 几何 ────────────────────────────────────────────────────
PAGE_W, PAGE_H = 11909, 16834      # A4
MARGIN = 1037                      # 四周
HF_DIST = 720                      # 页眉 / 页脚距边
CONTENT_W = PAGE_W - 2 * MARGIN     # 9835

IND_LEVEL = 216                    # 词条正文、译文的层级缩进
IND_BOX = 140                      # 方框左右内缩（与竖条配合）

BAR_SZ, BAR_SPACE = 16, 6          # 左竖条：single sz16 space6 HEAD

# 段落 spacing：(before, after, line)；line=None 表示不给 w:line
SP = {
    "cover_eyebrow": (0, 40, None),
    "cover_en":      (40, 40, 276),
    "cover_cn":      (40, 60, None),
    "cover_by":      (40, 0, None),
    "spacer":        (20, 20, 40),      # lineRule=exact；--- 横线改成的竖向间隔空段
    "box_title_a":   (0, 50, None),     # 【导读】【写在最后】
    "box_body_a":    (24, 36, 283),
    "box_title_b":   (0, 40, None),     # 📖 精读
    "box_body_b":    (24, 36, 283),
    "epilogue":      (30, 40, 288),
    "block":         (140, 50, None),   # ◆ 段落块标题
    "en":            (44, 16, 283),     # En: 英文原句
    "zh":            (10, 50, 278),     # 译: 中文翻译
    "module":        (70, 24, None),    # 模块标题（除精读外的所有 ### 模块：表达清单 /
                                        # 词汇注释 / 短语与固定搭配 / 长难句拆解 / 语法聚焦）
    "entry":         (50, 24, 278),     # ▶ 词条头
    "entry_body":    (16, 24, 278),     # 词条正文
    "finis":         (160, 160, None),  # 完结线
}
