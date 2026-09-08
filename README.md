# intensive-reading

一个 Claude Code skill：把一篇英文原文做成中英双语深度精读讲义，并导出为可打印的 Word / PDF。

体例与排版从两份《外刊精读》讲义原件逆向提取——分析方法见 `references/method.md`，
样式规格见 `references/style-spec.md`（从原件 OOXML 逐项提取，是排版的唯一权威）。

## 安装

```bash
git clone git@github.com:dodola/intensive-reading-skill.git
ln -s "$PWD/intensive-reading-skill/intensive-reading" ~/.claude/skills/
```

符号链接让仓库成为唯一副本：改完直接 `git commit`，不必再往 `~/.claude/skills/` 同步一次。
想要独立副本就把 `ln -s` 换成 `cp -r`。

skill 是 model-invoked 的：说「把这篇文章做成精读讲义」「Unit 2 也做一份」即可触发，不必打命令。

## 单独导出

已有讲义 Markdown 时，直接跑构建脚本：

```bash
bash ~/.claude/skills/intensive-reading/scripts/build.sh 讲义.md
# → 讲义.docx  讲义.pdf
```

页眉页脚取自讲义的 YAML front matter：

```yaml
---
header: 人教版 选择性必修 第二册  ·  双语深度精读讲义
footer: 选必二 Unit 1  ·  John Snow
---
```

依赖：`pandoc`、`libreoffice`（`soffice`）、`python3`（仅标准库）。
字体：Georgia、Noto Serif CJK SC（需 Medium 与 SemiBold 两个字重）、Microsoft YaHei、Carlito。

## 构建管线

```
讲义.md
  │
  ├─ print_variant.py   符号替换（emoji → CJK 几何符号）+ 字形校验 + 生成实体目录
  ├─ make_ref.py        按 tokens.py 生成 Word 参考模板：字体 / 色板 / 页面 / 页眉页脚
  ├─ pandoc             md → docx（--reference-doc）
  ├─ postprocess.py     逐段角色排版 + 表格列宽 + 加粗着色 + 页面设置 + 产物校验
  └─ soffice            docx → pdf
```

分工的原因：原件**零命名样式**，1681 个段落全是直接格式化，命名样式表达不了那种粒度。
所以 `make_ref.py` 只定基线，逐段的间距 / 缩进 / 底色 / 竖条由 `postprocess.py` 写进 XML。

`scripts/tokens.py` 是所有取值的唯一源。改样式：先改 `references/style-spec.md`，再改 `tokens.py`。

## 绕过的几个导出缺陷

| 现象 | 处理 |
|---|---|
| LibreOffice 丢彩色 emoji 与 `▶ ⚠ ✔` 字形 | 导出期替换为 CJK 字体内的几何符号，源文件保持 emoji |
| pandoc 对管道表格输出空 `tblGrid` 且 `tblW=0`，表格塌成一列 | 按内容宽度重算列宽并写 `tcW` |
| `--toc` 在 docx 里是需按 F9 才填充的域，导出为空白页 | 生成实体目录列表 |
| pandoc 丢弃参考模板的 `sectPr`，页眉页脚失效 | 导出后重建 `sectPr`，从 rels 里读真实 rId |
| pandoc 把 `---` 渲染成 VML 横线，而原件全篇无横线 | 改成规格里的竖向间隔空段 |
| 紧跟文字行的 `- ` 列表被并进上一段，搭配家族挤成一行连字符 | 开 pandoc `lists_without_preceding_blankline` 扩展 |

## 两处静默失败与对应的校验

这条管线有两类失败不会自己暴露——产物照样生成、页数照样对，只有逐页看才发现：

- **缺字形。** LibreOffice 对 emoji 与 `▶ ⚠ ✔` 无字形，渲染出来是**什么都没有**，
  不是豆腐块。`print_variant.py` 替换完会逐字复查，凡落在 U+2190–U+2BFF 或
  U+1F000 以上而不在 `SAFE_DECOR` 白名单里的字符，报出行号与码位后退出。
- **角色认错。** `postprocess.py` 靠文本特征认封面 / 方框 / `En:` / `译:` / 词条头，
  认不出来只是退回默认排版。所以最后核一遍「必然非零」的计数，缺了就非零退出。

两处都是非零退出，`build.sh` 的 `set -e` 会把整条管线停住。

## examples/

`选必二_Unit1_John Snow_精读讲义` —— 人教版选择性必修第二册 Unit 1 课文的完整讲义（24 页 A4）。
课文原文版权归人民教育出版社，此处仅作体例样例，请勿分发。
