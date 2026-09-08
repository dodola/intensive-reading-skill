#!/usr/bin/env python3
"""生成精读讲义的 Word 参考模板（pandoc --reference-doc）。

只负责**基线**：字体、字号、色板、页面、页眉页脚，以及 pandoc 需要的全套样式 ID。
逐段的间距 / 缩进 / 底色 / 竖条由 postprocess.py 写入——原件用的是直接格式化，
命名样式表达不了那种粒度（见 references/style-spec.md）。

用法: make_ref.py <输出.docx> <页眉文字> <页脚前缀>
"""
import subprocess, sys, tempfile, zipfile, re
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).parent))
from tokens import *

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'


def rfonts(ascii_=SERIF, ea=CJK):
    return f'<w:rFonts w:ascii="{ascii_}" w:hAnsi="{ascii_}" w:eastAsia="{ea}" w:cs="{ascii_}"/>'


def bar():
    """左侧竖条——原件唯一的边框形态，只有 left。"""
    return (f'<w:pBdr><w:left w:val="single" w:sz="{BAR_SZ}" '
            f'w:space="{BAR_SPACE}" w:color="{HEAD}"/></w:pBdr>')


def spacing(key):
    before, after, line = SP[key]
    rule = ' w:lineRule="exact"' if key == "spacer" else ' w:lineRule="auto"'
    ln = f' w:line="{line}"{rule}' if line else ""
    return f'<w:spacing w:before="{before}" w:after="{after}"{ln}/>'


def style(sid, name, *, based="Normal", nxt="BodyText", ppr="", rpr=""):
    return (f'<w:style w:type="paragraph" w:styleId="{sid}">'
            f'<w:name w:val="{name}"/><w:basedOn w:val="{based}"/><w:next w:val="{nxt}"/>'
            f'<w:qFormat/><w:pPr><w:widowControl/>{ppr}</w:pPr><w:rPr>{rpr}</w:rPr></w:style>')


def build_styles() -> str:
    S = [
        "<w:docDefaults><w:rPrDefault><w:rPr>"
        f'{rfonts()}<w:color w:val="{BODY}"/><w:sz w:val="{SZ}"/><w:szCs w:val="{SZ}"/>'
        "</w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:widowControl/>"
        f'{spacing("entry_body")}</w:pPr></w:pPrDefault></w:docDefaults>',
        '<w:style w:type="paragraph" w:default="1" w:styleId="Normal">'
        '<w:name w:val="Normal"/><w:qFormat/></w:style>',
        '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont">'
        '<w:name w:val="Default Paragraph Font"/></w:style>',
    ]
    for sid, nm in (("BodyText", "Body Text"), ("FirstParagraph", "First Paragraph"),
                    ("Compact", "Compact")):
        S.append(style(sid, nm))

    # 封面：眉标 / 英文主标题 / 中文标题 / 署名
    S.append(style("Title", "Title", nxt="Subtitle",
                   ppr=f'<w:jc w:val="center"/>{spacing("cover_en")}',
                   rpr=f'{rfonts(SERIF, UI)}<w:b/><w:color w:val="{HEAD}"/>'
                       f'<w:sz w:val="{SZ_COVER_EN}"/>'))
    S.append(style("Subtitle", "Subtitle",
                   ppr=f'<w:jc w:val="center"/>{spacing("cover_cn")}',
                   rpr=f'{rfonts(LABEL, UI)}<w:b/><w:color w:val="{NOTE}"/>'
                       f'<w:sz w:val="{SZ_COVER_CN}"/>'))
    for sid, nm in (("Author", "Author"), ("Date", "Date")):
        S.append(style(sid, nm, ppr=f'<w:jc w:val="center"/>{spacing("cover_by")}',
                       rpr=f'{rfonts(LABEL, UI)}<w:color w:val="{MUTED}"/>'))

    # H1 = 封面眉标；H2 = ◆ 段落块；H3 = 模块标题（暗红）
    # 原件正文无字号层级，全部 SZ——层级靠颜色 / 粗细 / 间距 / 底色区分
    S.append(style("Heading1", "heading 1",
                   ppr=f'<w:jc w:val="center"/>{spacing("cover_eyebrow")}'
                       '<w:outlineLvl w:val="0"/>',
                   rpr=f'{rfonts(LABEL, UI)}<w:b/><w:color w:val="{HEAD}"/>'
                       f'<w:sz w:val="{SZ_COVER_EYEBROW}"/>'))
    S.append(style("Heading2", "heading 2",
                   ppr=f'<w:keepNext/>{spacing("block")}<w:outlineLvl w:val="1"/>',
                   rpr=f'{rfonts(SERIF, CJKB)}<w:b/><w:color w:val="{HEAD}"/>'
                       f'<w:sz w:val="{SZ}"/>'))
    S.append(style("Heading3", "heading 3",
                   ppr=f'<w:keepNext/>{spacing("module")}<w:outlineLvl w:val="2"/>',
                   rpr=f'{rfonts(LABEL, CJKB)}<w:b/><w:color w:val="{NOTE}"/>'
                       f'<w:sz w:val="{SZ}"/>'))
    for n in range(4, 10):
        S.append(style(f"Heading{n}", f"heading {n}",
                       ppr=f'<w:keepNext/>{spacing("entry")}<w:outlineLvl w:val="{n-1}"/>',
                       rpr=f'{rfonts(LABEL, CJKB)}<w:b/><w:color w:val="{HEAD}"/>'
                           f'<w:sz w:val="{SZ}"/>'))

    # 引用块 = 译文 / 词条正文：层级缩进
    S.append(style("BlockText", "Block Text",
                   ppr=f'<w:ind w:left="{IND_LEVEL}"/>{spacing("entry_body")}'))

    # 代码块 = 箭头逻辑图：按精读方框处理（原件无等宽字体）
    S.append(style("SourceCode", "Source Code", nxt="SourceCode",
                   ppr=f'<w:shd w:val="clear" w:fill="{TINT_B}"/>{bar()}'
                       f'<w:ind w:left="{IND_BOX}" w:right="{IND_BOX}"/>'
                       '<w:spacing w:before="0" w:after="0" w:line="278" w:lineRule="auto"/>',
                   rpr=f'<w:color w:val="{BOLD}"/>'))
    S.append('<w:style w:type="character" w:styleId="VerbatimChar">'
             f'<w:name w:val="Verbatim Char"/><w:qFormat/>'
             f'<w:rPr>{rfonts(SERIF, CJKB)}<w:b/><w:color w:val="{HEAD}"/></w:rPr></w:style>')

    for sid, nm in (("Caption", "Caption"), ("TableCaption", "Table Caption"),
                    ("ImageCaption", "Image Caption"), ("Figure", "Figure"),
                    ("CaptionedFigure", "Captioned Figure"), ("Abstract", "Abstract"),
                    ("Bibliography", "Bibliography"), ("FootnoteText", "footnote text"),
                    ("DefinitionTerm", "Definition Term"), ("Definition", "Definition"),
                    ("TOCHeading", "TOC Heading")):
        S.append(style(sid, nm, rpr=f'<w:color w:val="{MUTED}"/>'))

    S.append('<w:style w:type="character" w:styleId="FootnoteReference">'
             '<w:name w:val="footnote reference"/>'
             '<w:rPr><w:vertAlign w:val="superscript"/></w:rPr></w:style>')
    S.append('<w:style w:type="character" w:styleId="Hyperlink">'
             f'<w:name w:val="Hyperlink"/><w:rPr><w:color w:val="{HEAD}"/>'
             '<w:u w:val="single"/></w:rPr></w:style>')
    S.append('<w:style w:type="character" w:styleId="BodyTextChar">'
             '<w:name w:val="Body Text Char"/></w:style>')

    # 表格：细竖条色描边 + 表头 TINT_B
    sides = ("top", "left", "bottom", "right", "insideH", "insideV")
    tb = "".join(f'<w:{s} w:val="single" w:sz="4" w:space="0" w:color="{HEAD}"/>' for s in sides)
    S.append('<w:style w:type="table" w:styleId="Table"><w:name w:val="Table"/><w:qFormat/>'
             f'<w:tblPr><w:tblBorders>{tb}</w:tblBorders>'
             '<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
             '<w:bottom w:w="60" w:type="dxa"/><w:right w:w="108" w:type="dxa"/>'
             '</w:tblCellMar></w:tblPr>'
             f'<w:tblStylePr w:type="firstRow"><w:rPr>{rfonts(LABEL, CJKB)}<w:b/>'
             f'<w:color w:val="{HEAD}"/></w:rPr>'
             f'<w:tcPr><w:shd w:val="clear" w:fill="{TINT_B}"/></w:tcPr></w:tblStylePr></w:style>')

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles {W}>' + "".join(S) + "</w:styles>")


def hdr_ftr(header_text: str, footer_prefix: str):
    """页眉右对齐无边框，页脚居中带页码域——原件正文与页眉均无横线。

    页眉页脚来自讲义 front matter，是**外部输入**，必须转义：`&` 或 `<` 直接写进
    <w:t> 会产出格式错误的 XML，Word 与 LibreOffice 都打不开，而 soffice 加载失败
    时退出码仍是 0（只是不产 PDF）——build.sh 靠 PDF 存在性检查兜底。
    """
    def run(text, sz, font=UI):
        text = escape(text)
        return (f'<w:r><w:rPr>{rfonts(LABEL, font)}<w:color w:val="{MUTED}"/>'
                f'<w:sz w:val="{sz}"/></w:rPr>'
                f'<w:t xml:space="preserve">{text}</w:t></w:r>')

    def fld(instr, sz):
        rpr = f'<w:rPr>{rfonts(SERIF, UI)}<w:color w:val="{MUTED}"/><w:sz w:val="{sz}"/></w:rPr>'
        return (f'<w:r>{rpr}<w:fldChar w:fldCharType="begin"/></w:r>'
                f'<w:r><w:instrText xml:space="preserve"> {instr} </w:instrText></w:r>'
                f'<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
                f'<w:r>{rpr}<w:t>1</w:t></w:r>'
                f'<w:r><w:fldChar w:fldCharType="end"/></w:r>')

    hdr = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:hdr {W}><w:p><w:pPr>'
           f'<w:jc w:val="right"/><w:spacing w:after="40" w:line="240" w:lineRule="auto"/>'
           f'</w:pPr>{run(header_text, SZ)}</w:p></w:hdr>')
    ftr = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:ftr {W}><w:p><w:pPr>'
           f'<w:jc w:val="center"/><w:spacing w:before="40" w:line="240" w:lineRule="auto"/>'
           f'</w:pPr>{run(footer_prefix + "  ·  ", SZ_FOOTER, UI)}{fld("PAGE", SZ_FOOTER)}'
           f'{run(" / ", SZ_FOOTER)}{fld("NUMPAGES", SZ_FOOTER)}</w:p></w:ftr>')
    return hdr, ftr


def main(out, header_text, footer_prefix):
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / "base.docx"
        base.write_bytes(subprocess.run(
            ["pandoc", "--print-default-data-file", "reference.docx"],
            capture_output=True, check=True).stdout)
        with zipfile.ZipFile(base) as z:
            items = {n: z.read(n) for n in z.namelist()}

        items["word/styles.xml"] = build_styles().encode()
        hdr, ftr = hdr_ftr(header_text, footer_prefix)
        items["word/header1.xml"] = hdr.encode()
        items["word/footer1.xml"] = ftr.encode()

        ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
        rels = items["word/_rels/document.xml.rels"].decode()
        add = "".join(f'<Relationship Id="rId{900+i}" Type="{ns}/{k}" Target="{k}1.xml"/>'
                      for i, k in enumerate(("header", "footer")))
        items["word/_rels/document.xml.rels"] = rels.replace(
            "</Relationships>", add + "</Relationships>").encode()

        wml = "application/vnd.openxmlformats-officedocument.wordprocessingml"
        ct = items["[Content_Types].xml"].decode()
        add = (f'<Override PartName="/word/header1.xml" ContentType="{wml}.header+xml"/>'
               f'<Override PartName="/word/footer1.xml" ContentType="{wml}.footer+xml"/>')
        items["[Content_Types].xml"] = ct.replace("</Types>", add + "</Types>").encode()

        doc = re.sub(r"<w:sectPr>.*?</w:sectPr>", "",
                     items["word/document.xml"].decode(), flags=re.S)
        sect = (f'<w:sectPr><w:headerReference w:type="default" r:id="rId900"/>'
                f'<w:footerReference w:type="default" r:id="rId901"/>'
                f'<w:pgSz w:w="{PAGE_W}" w:h="{PAGE_H}"/>'
                f'<w:pgMar w:top="{MARGIN}" w:right="{MARGIN}" w:bottom="{MARGIN}"'
                f' w:left="{MARGIN}" w:header="{HF_DIST}" w:footer="{HF_DIST}" w:gutter="0"/>'
                f'<w:docGrid w:linePitch="360"/></w:sectPr>')
        items["word/document.xml"] = doc.replace("</w:body>", sect + "</w:body>").encode()

        with zipfile.ZipFile(Path(out), "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in items.items():
                z.writestr(name, data)
    print(f"  模板已生成 {Path(out).name}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
