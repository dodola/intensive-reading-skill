#!/usr/bin/env bash
# 精读讲义构建：Markdown → Word(.docx) → PDF
#
# 用法: build.sh <讲义.md>
# 产物: 与源文件同目录的 .docx 与 .pdf
# 依赖: pandoc, libreoffice(soffice), python3
#
# 页眉/页脚取自讲义 YAML front matter 的 header / footer 字段；
# 缺省时按文件名 <册>_<Unit>_<课文名>_精读讲义.md 推导。
#
# 每一步都会在失败时非零退出：print_variant 校验字形，postprocess 校验角色识别，
# 成品 PDF 再查一遍反引号内嵌套加粗留下的字面星号。这三类都是静默失败——产物照样
# 生成、页数照样对，所以只能靠脚本拦。全部通过后才把产物移进源文件目录。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?用法: build.sh <讲义.md>}"
[ -f "$SRC" ] || { echo "找不到源文件: $SRC" >&2; exit 1; }
DIR="$(cd "$(dirname "$SRC")" && pwd)"
BASE="$(basename "$SRC" .md)"

for dep in pandoc soffice python3 pdftotext pdfinfo; do
  command -v "$dep" >/dev/null || { echo "缺少依赖: $dep" >&2; exit 1; }
done

# front matter：读到第二个 --- 为止，不限行数；顺手剥掉包裹的引号
read_fm() {
  awk -v key="$1" '
    NR == 1 { if ($0 !~ /^---[[:space:]]*$/) exit; next }
    /^(---|\.\.\.)[[:space:]]*$/ { exit }
    index($0, key ":") == 1 {
      v = substr($0, length(key) + 2)
      sub(/^[[:space:]]+/, "", v); sub(/[[:space:]]+$/, "", v)
      gsub(/^["\047]|["\047]$/, "", v)
      print v; exit
    }
  ' "$SRC"
}
HEADER="$(read_fm header)"
FOOTER="$(read_fm footer)"
[ -n "$HEADER" ] || HEADER="双语深度精读讲义"
if [ -z "$FOOTER" ]; then
  IFS='_' read -r _book _unit _text _rest <<< "$BASE"
  FOOTER="$(echo "${_book} ${_unit}" | sed 's/Unit\([0-9]\)/Unit \1/')  ·  ${_text}"
fi

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# lists_without_preceding_blankline：讲义里「常见搭配：」后面直接跟 - 列表，
# 标准 Markdown 会把整串并进上一段（渲染成一行连字符），开这个扩展才成列表。
python3 "$HERE/make_ref.py"       "$WORK/ref.docx" "$HEADER" "$FOOTER"
python3 "$HERE/print_variant.py"  "$SRC" "$WORK/print.md"
pandoc  "$WORK/print.md" -f markdown+lists_without_preceding_blankline \
        --reference-doc="$WORK/ref.docx" -o "$WORK/$BASE.docx"
python3 "$HERE/postprocess.py"    "$WORK/$BASE.docx"
# 独立 LibreOffice 用户配置：多个 build.sh 并发跑时，共享配置会抢锁互相失败
soffice --headless "-env:UserInstallation=file://$WORK/loprofile" \
        --convert-to pdf --outdir "$WORK" "$WORK/$BASE.docx" >/dev/null 2>&1
[ -f "$WORK/$BASE.pdf" ] || { echo "soffice 没产出 PDF" >&2; exit 1; }

# 反引号内嵌套加粗：pandoc 不解析 code span 内部的 **，成品留下字面星号。
# 不报错、产物照样生成，所以只能对成品 PDF 查（源码级 grep 反引号会误判）。
STARS="$(pdftotext "$WORK/$BASE.pdf" - | grep -oP '.{0,36}\*\*[^ ].{0,36}' || true)"
if [ -n "$STARS" ]; then
  echo "字面星号残留：反引号内嵌套了 **加粗**，pandoc 不解析 code span 内部。" >&2
  echo "$STARS" | head -20 >&2
  echo "改写成 *外层斜体 **内层加粗** *，或把加粗移出反引号；见 template.md 第六条约束。" >&2
  exit 1
fi

# 全部检查通过才落盘：失败时不留下与 PDF 不同步的半成品 docx
mv "$WORK/$BASE.docx" "$WORK/$BASE.pdf" "$DIR/"

echo "✓ $BASE.docx"
echo "✓ $BASE.pdf   ($(pdfinfo "$DIR/$BASE.pdf" | awk '/^Pages/{print $2}') 页, A4)"
