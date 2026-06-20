"""
McKinsey-style PDF generator for ai_vibecoding_report_2026.md
Korean font: Malgun Gothic (bundled with Windows)
"""

import os, re, math
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.graphics.shapes import (
    Drawing, Wedge, String, Rect, Line, Group
)
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── Register Korean fonts ─────────────────────────────────────────────────────
FONT_DIR = "C:/Windows/Fonts"
pdfmetrics.registerFont(TTFont("MalgunGothic",   f"{FONT_DIR}/malgun.ttf"))
pdfmetrics.registerFont(TTFont("MalgunGothicBd", f"{FONT_DIR}/malgunbd.ttf"))
pdfmetrics.registerFontFamily(
    "MalgunGothic",
    normal="MalgunGothic",
    bold="MalgunGothicBd",
    italic="MalgunGothic",
    boldItalic="MalgunGothicBd",
)

KO   = "MalgunGothic"
KO_B = "MalgunGothicBd"

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE       = os.path.dirname(os.path.abspath(__file__))
REPORT_MD  = os.path.join(BASE, "ai_vibecoding_report_2026.md")
OUTPUT_PDF = os.path.join(BASE, "ai_vibecoding_report_2026.pdf")

# ── McKinsey colour palette ────────────────────────────────────────────────────
NAVY     = colors.HexColor("#002060")
BLUE     = colors.HexColor("#0070C0")
LTBLUE   = colors.HexColor("#4BACC6")
ROW_EVEN = colors.HexColor("#EEF3FA")
ROW_ODD  = colors.white
GRAY     = colors.HexColor("#888888")
BORDER   = colors.HexColor("#D0D8E8")
BG_QUOTE = colors.HexColor("#F0F4FA")
BG_CHART = colors.HexColor("#F8FAFD")
TEXT_COL = colors.HexColor("#1A1A1A")
SILVER   = colors.HexColor("#C0C0C0")

W, H = A4


# ── Page event (header/footer) ────────────────────────────────────────────────
def on_page(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(NAVY)
    canvas.setLineWidth(2)
    canvas.line(20*mm, H - 15*mm, W - 20*mm, H - 15*mm)
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.5)
    canvas.line(20*mm, 14*mm, W - 20*mm, 14*mm)
    canvas.setFont(KO, 8)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(W/2, 9*mm, str(doc.page))
    canvas.drawString(20*mm, 9*mm,
        "AI 바이브코딩 시장 현황 및 2027년 전망  ·  2026.05.07")
    canvas.restoreState()


# ── Styles ────────────────────────────────────────────────────────────────────
def S(name, **kw):
    s = ParagraphStyle(name)
    for k, v in kw.items(): setattr(s, k, v)
    return s

S_H1 = S("H1", fontName=KO_B, fontSize=20, textColor=NAVY,
          leading=28, spaceBefore=0, spaceAfter=10)
S_H2 = S("H2", fontName=KO_B, fontSize=13, textColor=NAVY,
          leading=18, spaceBefore=16, spaceAfter=6,
          leftIndent=10, borderPadding=(4,0,4,8),
          borderLeftColor=BLUE, borderLeftWidth=3)
S_H3 = S("H3", fontName=KO_B, fontSize=11, textColor=BLUE,
          leading=16, spaceBefore=10, spaceAfter=4)
S_BODY = S("Body", fontName=KO, fontSize=10, textColor=TEXT_COL,
           leading=16, spaceBefore=2, spaceAfter=5, alignment=TA_JUSTIFY)
S_QUOTE = S("Quote", fontName=KO, fontSize=9, textColor=colors.HexColor("#444"),
            leading=14, spaceBefore=4, spaceAfter=6,
            leftIndent=10, rightIndent=8, backColor=BG_QUOTE,
            borderLeftColor=BLUE, borderLeftWidth=3, borderLeftPadding=7,
            borderPadding=(5,8,5,8))
S_BULLET = S("Bullet", fontName=KO, fontSize=10, textColor=TEXT_COL,
             leading=15, spaceBefore=1, spaceAfter=2,
             leftIndent=16, bulletIndent=6)
S_SRC = S("Source", fontName=KO, fontSize=8, textColor=GRAY,
          leading=12, spaceBefore=2, spaceAfter=4)
S_TH = S("TH", fontName=KO_B, fontSize=9, textColor=colors.white, leading=13)
S_TD = S("TD", fontName=KO,   fontSize=9, textColor=TEXT_COL, leading=13)
S_CHART_TITLE = S("CT", fontName=KO_B, fontSize=10, textColor=NAVY,
                  leading=14, spaceBefore=0, spaceAfter=6,
                  alignment=TA_CENTER)


# ── Inline markdown → XML-safe for Paragraph ─────────────────────────────────
def inline(text):
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.+?)\*",     r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`",     r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)  # strip links
    return text


# ── Generic markdown table ────────────────────────────────────────────────────
def parse_md_table(lines):
    rows = []
    for line in lines:
        if re.match(r"^\|[-: |]+\|$", line.strip()):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        rows.append(cells)
    return rows

def build_md_table(rows):
    if not rows: return None
    n = max(len(r) for r in rows)
    avail = W - 44*mm
    cw = [avail / n] * n

    def cell(t, hdr=False):
        return Paragraph(inline(t), S_TH if hdr else S_TD)

    data = []
    for i, row in enumerate(rows):
        padded = row + [""]*(n-len(row))
        data.append([cell(c, i==0) for c in padded])

    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  NAVY),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [ROW_ODD, ROW_EVEN]),
        ("GRID",           (0,0),(-1,-1), 0.4, BORDER),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("LEFTPADDING",    (0,0),(-1,-1), 7),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t


# ── Timeline table ────────────────────────────────────────────────────────────
def build_timeline_table():
    def td(t, bold=False): return Paragraph(inline(t), S_TH if bold else S_TD)
    rows = [
        [td("시기", True),   td("이벤트", True)],
        [td("2024년 12월"),   td("Cursor **Series B $2.6억** 유치")],
        [td("2025년 5월"),    td("Cursor **Series C $9억** 유치")],
        [td("2025년 7월"),    td("Lovable **Series A $2억** (기업가치 $18억)  ·  Windsurf → Cognition 인수 ($2.5억)")],
        [td("2025년 8월"),    td("Cognition(Devin) **Series B ~$5억** (기업가치 $9.8억)")],
        [td("2025년 11월"),   td("Cursor **Series D $23억** (기업가치 $29.3억)")],
        [td("2025년 12월"),   td("Lovable **Series B $3.3억** (기업가치 $66억)")],
    ]
    avail = W - 44*mm
    t = Table(rows, colWidths=[95, avail-95], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0),(-1,0),  BLUE),
        ("ROWBACKGROUNDS", (0,1),(-1,-1), [ROW_ODD, ROW_EVEN]),
        ("GRID",           (0,0),(-1,-1), 0.4, BORDER),
        ("TOPPADDING",     (0,0),(-1,-1), 5),
        ("BOTTOMPADDING",  (0,0),(-1,-1), 5),
        ("LEFTPADDING",    (0,0),(-1,-1), 7),
        ("FONTNAME",       (0,1),(0,-1),  KO_B),
        ("TEXTCOLOR",      (0,1),(0,-1),  NAVY),
        ("VALIGN",         (0,0),(-1,-1), "MIDDLE"),
    ]))
    return t


# ── Pie chart (Drawing-based, rendered at build time) ─────────────────────────
def build_pie_drawing(dw=430, dh=195):
    d = Drawing(dw, dh)
    d.add(Rect(0, 0, dw, dh, fillColor=BG_CHART,
               strokeColor=BORDER, strokeWidth=0.5))
    pie = Pie()
    pie.x, pie.y = 25, 30
    pie.width = pie.height = 140
    pie.data   = [42, 25, 24, 9]
    pie.labels = ["42%", "25%", "24%", "9%"]
    pie.sideLabels = False
    pie.slices[0].fillColor = NAVY
    pie.slices[1].fillColor = BLUE
    pie.slices[2].fillColor = LTBLUE
    pie.slices[3].fillColor = SILVER
    pie.slices.strokeWidth  = 1
    pie.slices.strokeColor  = colors.white
    for idx in range(4):
        pie.slices[idx].labelRadius = 0.68
    d.add(pie)
    d.add(String(dw/2, dh - 14,
                 "AI 바이브코딩 도구 시장 점유율 (2026년 5월 추정)",
                 fontName=KO_B, fontSize=9.5,
                 fillColor=NAVY, textAnchor="middle"))
    items = [
        (NAVY,   "GitHub Copilot  42%"),
        (BLUE,   "Cursor                25%"),
        (LTBLUE, "Claude Code     24%"),
        (SILVER, "기타                    9%"),
    ]
    lx, ly = 195, 150
    for i, (col, lbl) in enumerate(items):
        d.add(Rect(lx, ly - i*26, 13, 13, fillColor=col, strokeWidth=0))
        d.add(String(lx+17, ly - i*26 + 2, lbl,
                     fontName=KO, fontSize=9, fillColor=TEXT_COL))
    return d


# ── Markdown parser → story ───────────────────────────────────────────────────
def parse_markdown(md_text):
    lines = md_text.splitlines()
    i, n  = 0, len(lines)
    in_table    = False
    table_buf   = []
    in_mermaid  = False
    mermaid_type = ""
    quote_buf   = []

    def flush_table():
        nonlocal in_table, table_buf
        if table_buf:
            rows = parse_md_table(table_buf)
            t = build_md_table(rows)
            if t:
                yield Spacer(1, 4)
                yield t
                yield Spacer(1, 6)
        in_table, table_buf = False, []

    def flush_quote():
        nonlocal quote_buf
        if quote_buf:
            txt = " ".join(inline(l) for l in quote_buf)
            yield Paragraph(txt, S_QUOTE)
        quote_buf.clear()

    while i < n:
        raw = lines[i].rstrip()

        # ── mermaid fence open ──────────────────────────────────────────
        if raw.strip().startswith("```mermaid"):
            yield from flush_table()
            yield from flush_quote()
            in_mermaid = True
            mermaid_type = lines[i+1].strip().split()[0] if i+1 < n else ""
            i += 1; continue

        if in_mermaid:
            if raw.strip() == "```":
                in_mermaid = False
                if mermaid_type == "pie":
                    yield Spacer(1, 6)
                    drw = build_pie_drawing()
                    yield drw
                    yield Spacer(1, 8)
                elif mermaid_type == "timeline":
                    yield Spacer(1, 6)
                    yield Paragraph(
                        "주요 AI 바이브코딩 도구 투자 타임라인 (2024~2025)",
                        S_CHART_TITLE)
                    yield Spacer(1, 4)
                    yield build_timeline_table()
                    yield Spacer(1, 8)
            i += 1; continue

        # ── other fences ────────────────────────────────────────────────
        if raw.strip().startswith("```"):
            yield from flush_table()
            yield from flush_quote()
            i += 1; continue

        # ── blockquote ──────────────────────────────────────────────────
        if raw.startswith(">"):
            yield from flush_table()
            content = raw.lstrip("> ").strip()
            if content: quote_buf.append(content)
            i += 1; continue
        else:
            yield from flush_quote()

        # ── HR ──────────────────────────────────────────────────────────
        if re.match(r"^---+$", raw.strip()):
            yield from flush_table()
            yield Spacer(1, 4)
            yield HRFlowable(width="100%", thickness=0.5,
                             color=BORDER, spaceAfter=4)
            i += 1; continue

        # ── table line ──────────────────────────────────────────────────
        if raw.strip().startswith("|"):
            in_table = True
            table_buf.append(raw)
            i += 1; continue
        else:
            yield from flush_table()

        # ── image (skip) ────────────────────────────────────────────────
        if raw.strip().startswith("!["):
            i += 1; continue

        # ── heading ──────────────────────────────────────────────────────
        m = re.match(r"^(#{1,4})\s+(.*)", raw)
        if m:
            lvl  = len(m.group(1))
            text = inline(m.group(2))
            if lvl == 1:
                yield Paragraph(text, S_H1)
                yield HRFlowable(width="100%", thickness=2,
                                 color=NAVY, spaceBefore=2, spaceAfter=10)
            elif lvl == 2:
                yield Spacer(1, 4)
                yield Paragraph(text, S_H2)
            elif lvl == 3:
                yield Paragraph(text, S_H3)
            else:
                yield Paragraph(f"<b>{text}</b>", S_BODY)
            i += 1; continue

        # ── bullet list ──────────────────────────────────────────────────
        m = re.match(r"^\s*[-*+]\s+(.*)", raw)
        if m:
            yield Paragraph(f"• {inline(m.group(1))}", S_BULLET)
            i += 1; continue

        m = re.match(r"^\s*\d+\.\s+(.*)", raw)
        if m:
            yield Paragraph(f"• {inline(m.group(1))}", S_BULLET)
            i += 1; continue

        # ── blank line ────────────────────────────────────────────────────
        if raw.strip() == "":
            yield Spacer(1, 3)
            i += 1; continue

        # ── normal paragraph ─────────────────────────────────────────────
        text = inline(raw.strip())
        if text:
            yield Paragraph(text, S_BODY)
        i += 1

    yield from flush_table()
    yield from flush_quote()


# ── Build PDF ──────────────────────────────────────────────────────────────────
def main():
    with open(REPORT_MD, encoding="utf-8") as f:
        md = f.read()

    doc = SimpleDocTemplate(
        OUTPUT_PDF, pagesize=A4,
        leftMargin=24*mm, rightMargin=20*mm,
        topMargin=22*mm,  bottomMargin=22*mm,
        title="AI 바이브코딩 도구 시장 현황 및 2027년 전망",
        author="Research Report 2026-05-07",
    )
    story = list(parse_markdown(md))
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
    size_kb = os.path.getsize(OUTPUT_PDF) // 1024
    print(f"PDF saved ({size_kb} KB): {OUTPUT_PDF}")


if __name__ == "__main__":
    main()
