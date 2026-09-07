#!/usr/bin/env bash
# 精读讲义构建：Markdown → Word(.docx) → PDF
#
# 用法: build.sh <讲义.md>
# 产物: 与源文件同目录的 .docx 与 .pdf
# 依赖: pandoc, libreoffice(soffice), python3
#
# 页眉/页脚取自讲义 YAML front matter 的 header / footer 字段；
# 缺省时按文件名 <册>_<Unit>_<课文名>_精读讲义.md 推导。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC="${1:?用法: build.sh <讲义.md>}"
[ -f "$SRC" ] || { echo "找不到源文件: $SRC" >&2; exit 1; }
DIR="$(cd "$(dirname "$SRC")" && pwd)"
BASE="$(basename "$SRC" .md)"

for dep in pandoc soffice python3; do
  command -v "$dep" >/dev/null || { echo "缺少依赖: $dep" >&2; exit 1; }
done

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

read_fm() { sed -n '2,10p' "$SRC" | sed -n "s/^$1: *//p" | head -1; }
HEADER="$(read_fm header)"
FOOTER="$(read_fm footer)"
[ -n "$HEADER" ] || HEADER="双语深度精读讲义"
if [ -z "$FOOTER" ]; then
  IFS='_' read -r _book _unit _text _rest <<< "$BASE"
  FOOTER="$(echo "${_book} ${_unit}" | sed 's/Unit\([0-9]\)/Unit \1/')  ·  ${_text}"
fi

python3 "$HERE/make_ref.py"       "$WORK/ref.docx" "$HEADER" "$FOOTER"
python3 "$HERE/print_variant.py"  "$SRC" "$WORK/print.md"
pandoc  "$WORK/print.md" --reference-doc="$WORK/ref.docx" -o "$DIR/$BASE.docx"
python3 "$HERE/postprocess.py"    "$DIR/$BASE.docx"
soffice --headless --convert-to pdf --outdir "$DIR" "$DIR/$BASE.docx" >/dev/null 2>&1

echo "✓ $BASE.docx"
echo "✓ $BASE.pdf   ($(pdfinfo "$DIR/$BASE.pdf" | awk '/^Pages/{print $2}') 页, A4)"
