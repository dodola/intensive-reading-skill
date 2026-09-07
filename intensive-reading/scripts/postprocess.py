#!/usr/bin/env python3
"""按 references/style-spec.md 把逐段几何写进 pandoc 生成的 docx。

原件零命名样式、全靠直接格式化，命名样式表达不了这种粒度，所以分工是：
make_ref.py 定基线（字体 / 字号 / 色板 / 页面），这里定逐段的间距、缩进、底色、竖条。

四项修正：
1) 段落角色 —— 两类方框（导读 TINT_A / 精读 TINT_B）、En: 行、译: 行、▶ 词条头。
2) 加粗着色 —— pandoc 用内联 <w:b/>，样式表管不到；补加粗色并切中文粗体字族。
3) 表格列宽 —— pandoc 对管道表格输出空 <w:tblGrid/> 且 tblW=0，
   LibreOffice 会把整行宽度分给第一列。按内容宽度重新分配。
4) 页面设置 —— pandoc 丢弃参考模板的 sectPr，在此补回并接上页眉页脚。
"""
import shutil, sys, re, zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).parent))
from tokens import *

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("w", W)
def q(t): return f"{{{W}}}{t}"

MIN_SHARE, MAX_SHARE = 0.10, 0.55
HEADINGS = {f"Heading{n}" for n in range(1, 10)}


# ── 小工具 ───────────────────────────────────────────────────
def ppr(p):
    el = p.find(q("pPr"))
    if el is None:
        el = ET.Element(q("pPr")); p.insert(0, el)
    return el


def drop(el, *tags):
    for t in tags:
        for e in el.findall(q(t)):
            el.remove(e)


def para_style(p):
    st = p.find(q("pPr"))
    st = st.find(q("pStyle")) if st is not None else None
    return st.get(q("val")) if st is not None else None


def text_of(p):
    return "".join(t.text or "" for t in p.iter(q("t"))).strip()


def recolor(p, color, *, bold=False):
    for r in p.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is None:
            rpr = ET.Element(q("rPr")); r.insert(0, rpr)
        drop(rpr, "color")
        ET.SubElement(rpr, q("color"), {q("val"): color})
        if bold and rpr.find(q("b")) is None:
            rpr.insert(0, ET.Element(q("b")))


def geometry(p, key, *, ind_left=None, ind_right=None, tint=None, bar=False, keep=False):
    """写入一个角色的完整几何，覆盖样式表给的值。"""
    el = ppr(p)
    drop(el, "spacing", "ind", "shd", "pBdr", "keepNext", "widowControl")
    before, after, line = SP[key]
    attrs = {q("before"): str(before), q("after"): str(after)}
    if line:
        attrs[q("line")] = str(line)
        attrs[q("lineRule")] = "exact" if key == "spacer" else "auto"
    if keep:
        ET.SubElement(el, q("keepNext"))
    ET.SubElement(el, q("widowControl"))
    ET.SubElement(el, q("spacing"), attrs)
    if ind_left is not None:
        ind = {q("left"): str(ind_left)}
        if ind_right is not None:
            ind[q("right")] = str(ind_right)
        ET.SubElement(el, q("ind"), ind)
    if tint:
        ET.SubElement(el, q("shd"), {q("val"): "clear", q("color"): "auto", q("fill"): tint})
    if bar:
        bd = ET.SubElement(el, q("pBdr"))
        ET.SubElement(bd, q("left"), {q("val"): "single", q("sz"): str(BAR_SZ),
                                      q("space"): str(BAR_SPACE), q("color"): HEAD})


def is_rule(p):
    """pandoc 把 Markdown 的 --- 渲染成 VML 横线；原件全篇无横线。"""
    return not text_of(p) and p.find(f".//{q('pict')}") is not None


def to_spacer(p):
    """横线改成原件的竖向间隔空段：去掉 pict，只留间距。"""
    for r in list(p.findall(q("r"))):
        p.remove(r)
    el = ppr(p)
    drop(el, "spacing", "ind", "shd", "pBdr", "keepNext", "pStyle")
    ET.SubElement(el, q("spacing"), {q("before"): "20", q("after"): "20",
                                     q("line"): "40", q("lineRule"): "exact"})


def is_bold_para(p):
    runs = [r for r in p.findall(q("r")) if r.find(q("t")) is not None]
    return bool(runs) and all(
        r.find(q("rPr")) is not None and r.find(q("rPr")).find(q("b")) is not None
        for r in runs)


def resize(p, sz, color, *, font_ea=CJKB, font_ascii=SERIF):
    for r in p.findall(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is None:
            rpr = ET.Element(q("rPr")); r.insert(0, rpr)
        drop(rpr, "sz", "szCs", "color", "rFonts")
        rpr.insert(0, ET.Element(q("rFonts"), {
            q("ascii"): font_ascii, q("hAnsi"): font_ascii,
            q("eastAsia"): font_ea, q("cs"): font_ascii}))
        ET.SubElement(rpr, q("color"), {q("val"): color})
        ET.SubElement(rpr, q("sz"), {q("val"): str(sz)})
        ET.SubElement(rpr, q("szCs"), {q("val"): str(sz)})


def style_cover(block):
    """封面：整块居中。加粗行的最后两行是主标题对（英文 / 中文），其余为标签与副信息。"""
    bolds = [p for p in block if is_bold_para(p)]
    main_en, main_cn = (bolds[-2], bolds[-1]) if len(bolds) >= 2 else (None, None)
    for p in block:
        if p is main_en:
            geometry(p, "cover_en"); resize(p, SZ_COVER_EN, HEAD, font_ea=UI)
        elif p is main_cn:
            geometry(p, "cover_cn"); resize(p, SZ_COVER_CN, NOTE, font_ea=UI, font_ascii=LABEL)
        elif p in bolds:
            geometry(p, "cover_eyebrow"); resize(p, SZ, HEAD, font_ea=UI, font_ascii=LABEL)
        else:
            geometry(p, "cover_by"); resize(p, SZ, MUTED, font_ea=UI, font_ascii=LABEL)
        ET.SubElement(ppr(p), q("jc"), {q("val"): "center"})
    return 1 if block else 0


def fix_list_indent(body):
    """项目符号：悬挂缩进对齐到 IND_LEVEL 栅格，避免 pandoc 默认的 480 大空档。"""
    n = 0
    for p in body.iter(q("p")):
        if p.find(f".//{q('numPr')}") is None:
            continue
        el = ppr(p)
        ind = el.find(q("ind"))
        base = int(ind.get(q("left"), IND_LEVEL)) if ind is not None else IND_LEVEL
        right = ind.get(q("right")) if ind is not None else None
        drop(el, "ind")
        attrs = {q("left"): str(base + 180), q("hanging"): "180"}
        if right:
            attrs[q("right")] = right
        ET.SubElement(el, q("ind"), attrs)
        n += 1
    return n


# ── 1. 段落角色 ──────────────────────────────────────────────
def callout(block, kind):
    """kind='a' 导读/写在最后（TINT_A，标题深蓝）；'b' 精读（TINT_B，标题暗红）。"""
    tint = TINT_A if kind == "a" else TINT_B
    geometry(block[0], f"box_title_{kind}", ind_left=IND_BOX, ind_right=IND_BOX,
             tint=tint, bar=True, keep=True)
    recolor(block[0], HEAD if kind == "a" else NOTE, bold=True)
    for para in block[1:]:
        # 全部齐方框内缩：竖条画在段落缩进处，缩进不一致会把左竖条推出台阶
        geometry(para, f"box_body_{kind}", ind_left=IND_BOX,
                 ind_right=IND_BOX, tint=tint, bar=True)


def apply_roles(body):
    kids = list(body)
    stats = {"cover": 0, "callout_a": 0, "callout_b": 0,
             "en": 0, "zh": 0, "entry": 0, "rule": 0}

    # 封面 = Heading1 之后到第一条横线 / 二级标题之前
    if kids and para_style(kids[0]) == "Heading1":
        j = 1
        while j < len(kids) and kids[j].tag == q("p") \
                and para_style(kids[j]) not in HEADINGS and not is_rule(kids[j]):
            j += 1
        stats["cover"] = style_cover(kids[1:j])

    i = 0
    while i < len(kids):
        p = kids[i]
        if p.tag != q("p"):
            i += 1; continue
        style, txt = para_style(p), text_of(p)

        if is_rule(p):
            to_spacer(p); stats["rule"] += 1; i += 1; continue

        # 方框：三级标题 + 其后同块段落
        if style == "Heading3" and ("【" in txt or "精读" in txt):
            kind = "a" if "【" in txt else "b"
            j = i + 1
            while j < len(kids):
                nxt = kids[j]
                if nxt.tag != q("p") or para_style(nxt) in HEADINGS or is_rule(nxt):
                    break
                j += 1
            if j > i + 1:
                callout(kids[i:j], kind)
                stats[f"callout_{kind}"] += 1
                i = j; continue

        if txt.startswith("En:") or txt.startswith("En："):
            geometry(p, "en", keep=True)
            recolor(p, HEAD, bold=True)
            stats["en"] += 1
        elif style == "BlockText" and (txt.startswith("译:") or txt.startswith("译：")):
            geometry(p, "zh", ind_left=IND_LEVEL)
            stats["zh"] += 1
        elif style not in HEADINGS and txt[:1] and txt[0] in "●▶":
            geometry(p, "entry", keep=True)
            recolor(p, NOTE, bold=True)
            stats["entry"] += 1
        i += 1
    return stats


# ── 2. 加粗着色 ──────────────────────────────────────────────
def style_bold_runs(root):
    """加粗补色，并把中文字族切到 SemiBold——原件靠切字族表达中文粗细。"""
    n = 0
    for r in root.iter(q("r")):
        rpr = r.find(q("rPr"))
        if rpr is None or rpr.find(q("b")) is None:
            continue
        if rpr.find(q("color")) is None:
            ET.SubElement(rpr, q("color"), {q("val"): BOLD})
        rf = rpr.find(q("rFonts"))
        if rf is None:
            rf = ET.Element(q("rFonts")); rpr.insert(0, rf)
        if not rf.get(q("eastAsia")):
            rf.set(q("eastAsia"), CJKB)
        n += 1
    return n


# ── 3. 表格列宽 ──────────────────────────────────────────────
def cell_width(tc):
    text = "".join(t.text or "" for t in tc.iter(q("t")))
    return sum(2 if ord(c) > 0x2E7F else 1 for c in text)


def fix_table(tbl):
    rows = tbl.findall(q("tr"))
    if not rows or not (ncols := len(rows[0].findall(q("tc")))):
        return False
    weights = [1.0] * ncols
    for tr in rows:
        for i, tc in enumerate(tr.findall(q("tc"))[:ncols]):
            weights[i] = max(weights[i], cell_width(tc))
    shares = [w / sum(weights) for w in weights]
    shares = [min(max(s, MIN_SHARE), MAX_SHARE) for s in shares]
    shares = [s / sum(shares) for s in shares]
    widths = [max(int(CONTENT_W * s), 500) for s in shares]

    pr = tbl.find(q("tblPr"))
    if pr is None:
        pr = ET.Element(q("tblPr")); tbl.insert(0, pr)
    for tag, attrs in (("tblW", {q("type"): "pct", q("w"): "5000"}),
                       ("tblLayout", {q("type"): "fixed"})):
        el = pr.find(q(tag))
        if el is None:
            el = ET.SubElement(pr, q(tag))
        el.attrib.clear(); el.attrib.update(attrs)

    grid = tbl.find(q("tblGrid"))
    if grid is None:
        grid = ET.Element(q("tblGrid")); tbl.insert(list(tbl).index(pr) + 1, grid)
    for c in list(grid):
        grid.remove(c)
    for wd in widths:
        ET.SubElement(grid, q("gridCol"), {q("w"): str(wd)})

    for tr in rows:
        for i, tc in enumerate(tr.findall(q("tc"))[:ncols]):
            tcpr = tc.find(q("tcPr"))
            if tcpr is None:
                tcpr = ET.Element(q("tcPr")); tc.insert(0, tcpr)
            tcw = tcpr.find(q("tcW"))
            if tcw is None:
                tcw = ET.Element(q("tcW")); tcpr.insert(0, tcw)
            tcw.attrib.clear()
            tcw.attrib.update({q("w"): str(widths[i]), q("type"): "dxa"})
    return True


# ── 4. 页面设置 ──────────────────────────────────────────────
def ensure_sectpr(items, body):
    rels = items["word/_rels/document.xml.rels"].decode()
    ids = {m.group(2): m.group(1) for m in
           re.finditer(r'<Relationship Id="([^"]+)"[^>]*?/(header|footer)"[^>]*/>', rels)}
    if (old := body.find(q("sectPr"))) is not None:
        body.remove(old)
    sect = ET.SubElement(body, q("sectPr"))
    for kind in ("header", "footer"):
        if kind in ids:
            ET.SubElement(sect, q(f"{kind}Reference"),
                          {q("type"): "default", f"{{{R}}}id": ids[kind]})
    ET.SubElement(sect, q("pgSz"), {q("w"): str(PAGE_W), q("h"): str(PAGE_H)})
    ET.SubElement(sect, q("pgMar"), {
        q("top"): str(MARGIN), q("right"): str(MARGIN), q("bottom"): str(MARGIN),
        q("left"): str(MARGIN), q("header"): str(HF_DIST),
        q("footer"): str(HF_DIST), q("gutter"): "0"})
    ET.SubElement(sect, q("docGrid"), {q("linePitch"): "360"})
    return len(ids)


def main(path):
    path = Path(path)
    with zipfile.ZipFile(path) as z:
        items = {n: z.read(n) for n in z.namelist()}

    root = ET.fromstring(items["word/document.xml"].decode("utf-8"))
    body = root.find(q("body"))

    roles = apply_roles(body)
    lists = fix_list_indent(body)
    bolds = style_bold_runs(root)
    tables = sum(fix_table(t) for t in root.iter(q("tbl")))
    hf = ensure_sectpr(items, body)

    items["word/document.xml"] = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    tmp = path.with_suffix(".tmp.docx")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for n, d in items.items():
            z.writestr(n, d)
    shutil.move(tmp, path)
    print(f"  角色排版：封面 {roles['cover']} / 导读方框 {roles['callout_a']} / "
          f"精读方框 {roles['callout_b']} / En 行 {roles['en']} / 译文 {roles['zh']} / "
          f"词条头 {roles['entry']}")
    print(f"  基础修正：{bolds} 处加粗 / {tables} 个表格列宽 / {roles['rule']} 条横线改间隔 / "
          f"{lists} 处列表缩进 / 页眉页脚 {hf}/2")


if __name__ == "__main__":
    main(sys.argv[1])
