# 排版样式规格

从《外刊精读02/03_纸质阅读版》原件的 OOXML 逐项提取。**这是排版的唯一权威**，`make_ref.py` / `postprocess.py` 的取值都以本文件为准。

改样式的顺序：先改这里，再改脚本。

## 提取时的三个前提

原件是 Mac Word 14 存的 .docx，拆开后有三件事决定了脚本的写法：

1. **零命名样式。** 1681 / 807 个段落里 `pStyle` 出现 0 次，`styles.xml` 是未改动的 Word 样板。全部视觉靠直接格式化（每个 `w:p` 自带 `pPr`、每个 `w:r` 自带 `rPr`）。所以参考模板只能定基线，逐段的差异必须在导出后由 `postprocess.py` 写进 XML。
2. **零横线。** 全篇 `pBdr` 只有 `left` 一种（264 + 13 + 2 处），`top` / `bottom` / `between` 在正文中一次都没有；页眉段也没有下边框。方框的视觉是**左侧竖条 + 浅色底**，不是描边盒子。
3. **02 是配色权威。** 03 的 run 颜色全部塌成 `000000`，02 才带完整色板。两篇的段落几何完全一致，取 02 的颜色 + 02 的页边距。

## 页面

| 项 | 值 |
|---|---|
| `pgSz` | 11909 × 16834（A4） |
| `pgMar` | 上右下左均 1037，`header` 720，`footer` 720 |
| 正文宽 | 9835 twips（= 11909 − 2×1037） |
| `docGrid` | `linePitch` 360；`cols space` 720 |

> 03 用的是页边距 720 / header 283。取 02 的 1037 / 720——留白更舒展，纸质阅读更好。

## 字体

四个字族，按**语义**而非按语言分工：

| 角色 | ascii / hAnsi / cs | eastAsia |
|---|---|---|
| 正文 | `Georgia` | `Noto Serif CJK SC Medium` |
| 加粗 | `Georgia` | `Noto Serif CJK SC SemiBold` |
| 标签/模块标题 | `Calibri` | `Noto Serif CJK SC SemiBold` |
| 页眉页脚 · 封面 | `Calibri` 或 `Georgia` | `Microsoft YaHei` |

关键一条：**中文的粗细靠切字族实现**（Medium → SemiBold），不是只给 `w:b`。原件两者都给，缺了字族切换中文的粗体会由渲染器合成，笔画会脏。

原件写的是 `Noto Serif SC Medium/SemiBold`，本机实际装的是 `Noto Serif CJK SC` 系列（Medium / SemiBold 两个字重都在），按后者写。`Calibri` 由 Carlito 代替，度量兼容。

字号统一 `sz 21`（10.5pt）；例外只有封面三行和页脚（见下表）。

## 色板

| token | 值 | 用在 |
|---|---|---|
| BODY | `#475569` | 正文、译文 |
| BOLD | `#1E293B` | 加粗、原句回填、导读正文 |
| HEAD | `#1A365D` | `En:` 行、`◆` 块标题、方框标题、封面主标题、左竖条 |
| NOTE | `#8B1E1E` | 模块标题（词汇注释 / 精读）、`▶` 词条头 |
| MUTED | `#64748B` | 页眉、页脚、封面署名 |
| TINT-A | `#F8FAFC` | 导读 / 写在最后 的底色 |
| TINT-B | `#F1F5F9` | 精读 的底色（比 A 略深，用来区分两类方框） |

左竖条统一 `single sz16 space6 #1A365D`，**只有 left**。

## 段落几何

`spacing` 三个数依次是 before / after / line（`lineRule="auto"`，`—` 表示不给 line）。`widowControl` 除空段外全部开启。

| 角色 | before/after/line | ind | 底色 | 竖条 | 其他 | 字体 · 色 · 字号 |
|---|---|---|---|---|---|---|
| 封面眉标 | 0/40/— | | | | 居中 | Calibri+YaHei b · HEAD · 20 |
| 封面英文主标题 | 40/40/276 | | | | 居中 | Georgia+YaHei b · HEAD · 30 |
| 封面中文标题 | 40/60/— | | | | 居中 | Calibri+YaHei b · NOTE · 23 |
| 封面署名日期 | 40/0/— | | | | 居中 | Calibri+YaHei · MUTED · 21 |
| **竖向间隔空段** | 20/20/**40 exact** | | | | 无内容 | — |
| 方框标题〔导读·写在最后〕 | 0/50/— | 140/140 | TINT-A | ✓ | keepNext | Calibri+YaHei b · HEAD |
| 导读正文 | 24/36/283 | 140/140 | TINT-A | ✓ | | BOLD |
| `◆` 段落块标题 | 140/50/— | | | | keepNext | Georgia+SemiBold b · HEAD |
| `En:` 英文原句 | 44/16/283 | | | | keepNext | b · HEAD |
| `译:` 中文翻译 | 10/50/278 | 216 | | | | BODY |
| 模块标题〔词汇注释〕 | 70/24/— | | | | keepNext | Calibri+SemiBold b · NOTE |
| `▶` 词条头 / 子标记 | 50/24/278 | | | | keepNext | Calibri+SemiBold b · NOTE |
| 词条正文 | 16/24/278 | 216 | | | | BODY 或 BOLD |
| 模块标题〔精读〕 | 0/40/— | 140/140 | TINT-B | ✓ | keepNext | Calibri+SemiBold b · NOTE |
| 精读正文 | 24/36/283 | 140/140 | TINT-B | ✓ | | BODY |
| 结语正文 · `❝` 引文 | 30/40/288 | 140/140 | TINT-A | ✓ | | BODY |
| 完结线 | 160/160/— | | | | 居中 | MUTED |

行距不是一个全局值：正文段 278，方框段 283，结语 288，封面标题 276。差别很小但成体系——**越是需要慢读的块，行距越松**。

`ind` 只有两个值：**216**（词条正文、译文的层级缩进）和 **140/140**（方框的左右内缩，与竖条配合）。

## 页眉页脚

```
页眉  右对齐  spacing after=40   Calibri+Microsoft YaHei  #64748B  sz21  无边框
      文字：「THE ATLANTIC  ·  外刊双语精读讲义」

页脚  居中    spacing before=40  Georgia+Microsoft YaHei  #64748B  sz18
      文字：「外刊精读 02  ·  」+ PAGE + 「 / 」+ NUMPAGES
```

页码用 `fldSimple w:instr="PAGE"` / `"NUMPAGES"`，两侧的分隔文字是独立 run。

## 表格

原件每篇只有 **1 个**表格，且是 1 行 1 列、`tblW auto` + `jc center` + 单列 `gridCol 9835` 的满宽装饰框——不是数据表。

**词条在原件里是段落结构，不是表格**：`▶ 词条头`（无缩进、暗红、keepNext）+ 若干条 `ind 216` 的正文行。讲义源文若用 Markdown 管道表格写词条，导出后与原件形态不同；`postprocess.py` 会把表格按本规格描边着色，但形态差异需要知情。

## 导出期的三处主动偏离

Markdown 有原件没有的构件，按规格的精神就近处理，不新造视觉：

1. **`---` 分隔线 → 竖向间隔空段。** pandoc 把它渲染成 VML 横线（`<v:rect o:hr="t">`），而原件全篇无横线；改成规格里的 spacer（20/20/line 40 exact）。
2. **代码块 → 精读方框。** 原件没有等宽字体，箭头逻辑图按 TINT_B + 左竖条处理，与精读同一视觉家族。
3. **项目符号 → 悬挂缩进对齐栅格。** 原件无列表，pandoc 默认 `ind left=480 hanging=480` 空档过大；改到 `left=396 hanging=180`，落在 216 栅格上。

方框内一律齐 `IND_BOX`，不做嵌套缩进——`pBdr left` 画在段落缩进处，缩进不一致会把左竖条推出台阶。
