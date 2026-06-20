"use strict";
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, LevelFormat, ExternalHyperlink,
  TableOfContents, HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom,
} = require("docx");

// ── McKinsey colours (hex without #) ──────────────────────────────────────────
const NAVY   = "002060";
const BLUE   = "0070C0";
const LTBLUE = "4BACC6";
const SILVER = "C0C0C0";
const ROW_EVEN = "EEF3FA";
const WHITE  = "FFFFFF";
const GRAY   = "888888";
const TEXT   = "1A1A1A";

// A4 page (default for docx), 1" margins → content width = 11906 - 2880 = 9026 DXA
const CONTENT_W = 9026;
const M = 1440; // 1 inch in DXA

// ── Helpers ───────────────────────────────────────────────────────────────────
const thin = (color = "D0D8E8") => ({ style: BorderStyle.SINGLE, size: 4, color });
const noBorder = () => ({ style: BorderStyle.NONE, size: 0, color: "FFFFFF" });
const cellBorders = (color = "D0D8E8") => ({
  top: thin(color), bottom: thin(color),
  left: thin(color), right: thin(color),
});
const cellPad = { top: 80, bottom: 80, left: 120, right: 120 };

function thCell(text, widthDXA) {
  return new TableCell({
    width: { size: widthDXA, type: WidthType.DXA },
    borders: cellBorders("FFFFFF"),
    shading: { fill: NAVY, type: ShadingType.CLEAR },
    margins: cellPad,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: WHITE, font: "Arial", size: 18 })],
    })],
  });
}

function tdCell(text, widthDXA, shade = WHITE, bold = false, color = TEXT) {
  // Parse inline bold (**text**) and links [label](url)
  const runs = parseInline(text, bold, color);
  return new TableCell({
    width: { size: widthDXA, type: WidthType.DXA },
    borders: cellBorders(),
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: cellPad,
    verticalAlign: VerticalAlign.CENTER,
    children: [new Paragraph({ children: runs })],
  });
}

function parseInline(text, defaultBold = false, defaultColor = TEXT) {
  const runs = [];
  // Strip markdown links → keep label only
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  // Split on **bold** markers
  const parts = text.split(/(\*\*[^*]+\*\*)/);
  for (const part of parts) {
    if (part.startsWith("**") && part.endsWith("**")) {
      runs.push(new TextRun({
        text: part.slice(2, -2), bold: true, font: "Arial",
        size: 20, color: defaultColor,
      }));
    } else if (part) {
      runs.push(new TextRun({
        text: part, bold: defaultBold, font: "Arial",
        size: 20, color: defaultColor,
      }));
    }
  }
  return runs.length ? runs : [new TextRun({ text: "", font: "Arial", size: 20 })];
}

function hr() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D0D8E8", space: 1 } },
    spacing: { before: 160, after: 160 },
    children: [],
  });
}

function sp(pt = 6) {
  return new Paragraph({ spacing: { before: 0, after: pt * 20 }, children: [] });
}

// ── Section title row for visual timeline replacement ─────────────────────────
function makeTimelineTable() {
  const rows_data = [
    ["2024년 12월", "Cursor Series B $2.6억 유치"],
    ["2025년 5월",  "Cursor Series C $9억 유치"],
    ["2025년 7월",  "Lovable Series A $2억 (기업가치 $18억) · Windsurf → Cognition 인수 ($2.5억)"],
    ["2025년 8월",  "Cognition(Devin) Series B ~$5억 (기업가치 $9.8억)"],
    ["2025년 11월", "Cursor Series D $23억 (기업가치 $29.3억)"],
    ["2025년 12월", "Lovable Series B $3.3억 (기업가치 $66억)"],
  ];
  const c1 = 1400, c2 = CONTENT_W - c1;
  const headerRow = new TableRow({
    children: [
      thCell("시기", c1),
      thCell("이벤트", c2),
    ],
    tableHeader: true,
  });
  const bodyRows = rows_data.map((r, i) => new TableRow({
    children: [
      tdCell(r[0], c1, i % 2 === 0 ? WHITE : ROW_EVEN, true, NAVY),
      tdCell(r[1], c2, i % 2 === 0 ? WHITE : ROW_EVEN),
    ],
  }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: [c1, c2],
    rows: [headerRow, ...bodyRows],
  });
}

// ── Market share "chart" as styled info table ─────────────────────────────────
function makePieTable() {
  const data = [
    ["GitHub Copilot", "42%", "엔터프라이즈·대기업 개발팀 지배"],
    ["Cursor",         "25%", "고성능 개인·스타트업 개발자"],
    ["Claude Code",    "24%", "고급 추론·터미널 워크플로우"],
    ["기타(Windsurf·Tabnine 등)", "9%", "틈새 시장 점유"],
  ];
  const shades = [NAVY, BLUE, LTBLUE, SILVER];
  const cw = [Math.floor(CONTENT_W*0.28), Math.floor(CONTENT_W*0.12), Math.floor(CONTENT_W*0.60)];
  const headerRow = new TableRow({
    children: [thCell("도구", cw[0]), thCell("점유율", cw[1]), thCell("특징", cw[2])],
    tableHeader: true,
  });
  const bodyRows = data.map((r, i) => new TableRow({
    children: [
      tdCell(r[0], cw[0], i % 2 === 0 ? WHITE : ROW_EVEN, true, NAVY),
      new TableCell({
        width: { size: cw[1], type: WidthType.DXA },
        borders: cellBorders(),
        shading: { fill: shades[i], type: ShadingType.CLEAR },
        margins: cellPad,
        verticalAlign: VerticalAlign.CENTER,
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [new TextRun({ text: r[1], bold: true, color: i < 3 ? WHITE : TEXT, font: "Arial", size: 20 })],
        })],
      }),
      tdCell(r[2], cw[2], i % 2 === 0 ? WHITE : ROW_EVEN),
    ],
  }));
  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: cw,
    rows: [headerRow, ...bodyRows],
  });
}

// ── Generic markdown table → docx Table ──────────────────────────────────────
function parseMarkdownTable(lines) {
  const rows = [];
  for (const line of lines) {
    if (/^\|[-: |]+\|$/.test(line.trim())) continue;
    const cells = line.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
    rows.push(cells);
  }
  return rows;
}

function buildDocxTable(mdRows) {
  if (!mdRows.length) return null;
  const nCols = Math.max(...mdRows.map(r => r.length));
  const cw = Math.floor(CONTENT_W / nCols);
  const colWidths = Array(nCols).fill(cw);
  // adjust last col to fill exactly
  colWidths[nCols - 1] = CONTENT_W - cw * (nCols - 1);

  const docxRows = mdRows.map((row, ri) => {
    while (row.length < nCols) row.push("");
    return new TableRow({
      children: row.map((cell, ci) => {
        const shade = ri === 0 ? NAVY : (ri % 2 === 0 ? WHITE : ROW_EVEN);
        const isHdr = ri === 0;
        return new TableCell({
          width: { size: colWidths[ci], type: WidthType.DXA },
          borders: cellBorders(isHdr ? "FFFFFF" : undefined),
          shading: { fill: shade, type: ShadingType.CLEAR },
          margins: cellPad,
          verticalAlign: VerticalAlign.CENTER,
          children: [new Paragraph({
            children: parseInline(cell, isHdr, isHdr ? WHITE : TEXT),
          })],
        });
      }),
      tableHeader: ri === 0,
    });
  });

  return new Table({
    width: { size: CONTENT_W, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: docxRows,
  });
}

// ── Main document builder ─────────────────────────────────────────────────────
function buildStory() {
  const children = [];

  // Cover-style subtitle block
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({
        text: "AI 바이브코딩 도구 시장 현황 및 2027년 전망",
        bold: true, font: "Arial", size: 48, color: NAVY,
      })],
      spacing: { before: 0, after: 200 },
    })
  );
  children.push(new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 1 } },
    spacing: { before: 0, after: 240 },
    children: [
      new TextRun({ text: "작성일: 2026년 5월 7일  |  분류: 시장 조사 / 기술 트렌드 리포트  |  대상 독자: 개발자, 1인 창업자, AI 도구 관심자", font: "Arial", size: 18, color: GRAY, italics: true }),
    ],
  }));

  // Parse and render the markdown body
  const md = fs.readFileSync("ai_vibecoding_report_2026.md", "utf8");
  const lines = md.split(/\r?\n/);
  let i = 0;
  let tableLines = [];
  let inTable = false;
  let inMermaid = false;
  let mermaidType = "";
  let quoteLines = [];
  let inQuote = false;
  let skipTitle = true; // skip H1 (already added)

  while (i < lines.length) {
    const raw = lines[i];

    // ── mermaid ──────────────────────────────────────────────────────────
    if (raw.trim().startsWith("```mermaid")) {
      if (inTable) { const t = buildDocxTable(parseMarkdownTable(tableLines)); if (t) { children.push(t); children.push(sp(8)); } tableLines = []; inTable = false; }
      if (inQuote) { children.push(new Paragraph({ children: quoteLines.map(l => new TextRun({ text: l + " ", font: "Arial", size: 20, italics: true, color: "444444" })), indent: { left: 400 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 8 } }, shading: { fill: "F0F4FA", type: ShadingType.CLEAR }, spacing: { before: 80, after: 80 } })); quoteLines = []; inQuote = false; }
      inMermaid = true;
      mermaidType = (lines[i + 1] || "").trim().split(/\s/)[0];
      i++; continue;
    }
    if (inMermaid) {
      if (raw.trim() === "```") {
        inMermaid = false;
        if (mermaidType === "pie") {
          children.push(sp(4));
          children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "AI 바이브코딩 도구 시장 점유율 (2026년 5월 추정)", bold: true, font: "Arial", size: 22, color: NAVY })], spacing: { after: 100 } }));
          children.push(makePieTable());
          children.push(sp(8));
        } else if (mermaidType === "timeline") {
          children.push(sp(4));
          children.push(new Paragraph({ alignment: AlignmentType.CENTER, children: [new TextRun({ text: "주요 AI 바이브코딩 도구 투자 타임라인 (2024~2025)", bold: true, font: "Arial", size: 22, color: NAVY })], spacing: { after: 100 } }));
          children.push(makeTimelineTable());
          children.push(sp(8));
        }
      }
      i++; continue;
    }

    // ── other code fences ────────────────────────────────────────────────
    if (raw.trim().startsWith("```")) { i++; continue; }

    // ── blockquote ───────────────────────────────────────────────────────
    if (raw.startsWith(">")) {
      if (inTable) { const t = buildDocxTable(parseMarkdownTable(tableLines)); if (t) { children.push(t); children.push(sp(8)); } tableLines = []; inTable = false; }
      const content = raw.replace(/^>\s*/, "").trim();
      // strip markdown links
      const clean = content.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1").replace(/\*\*/g, "");
      if (clean) quoteLines.push(clean);
      inQuote = true; i++; continue;
    } else if (inQuote) {
      if (quoteLines.length) {
        children.push(new Paragraph({
          children: quoteLines.map(l => new TextRun({ text: l + " ", font: "Arial", size: 18, italics: true, color: "444444" })),
          indent: { left: 400 },
          border: { left: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 8 } },
          shading: { fill: "F0F4FA", type: ShadingType.CLEAR },
          spacing: { before: 80, after: 80 },
        }));
      }
      quoteLines = []; inQuote = false;
    }

    // ── HR ───────────────────────────────────────────────────────────────
    if (/^---+$/.test(raw.trim())) {
      if (inTable) { const t = buildDocxTable(parseMarkdownTable(tableLines)); if (t) { children.push(t); children.push(sp(8)); } tableLines = []; inTable = false; }
      children.push(hr()); i++; continue;
    }

    // ── Table ─────────────────────────────────────────────────────────────
    if (raw.trim().startsWith("|")) {
      inTable = true; tableLines.push(raw); i++; continue;
    } else if (inTable) {
      const t = buildDocxTable(parseMarkdownTable(tableLines));
      if (t) { children.push(t); children.push(sp(8)); }
      tableLines = []; inTable = false;
    }

    // ── Images ───────────────────────────────────────────────────────────
    if (raw.trim().startsWith("![")) { i++; continue; }

    // ── Headings ──────────────────────────────────────────────────────────
    const hm = raw.match(/^(#{1,4})\s+(.*)/);
    if (hm) {
      const lvl = hm[1].length;
      const txt = hm[2].replace(/\*\*/g, "").replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
      if (lvl === 1) {
        if (skipTitle) { skipTitle = false; i++; continue; } // skip duplicate H1
        children.push(new Paragraph({
          heading: HeadingLevel.HEADING_1,
          children: [new TextRun({ text: txt, bold: true, font: "Arial", size: 36, color: NAVY })],
          spacing: { before: 300, after: 160 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 1 } },
        }));
      } else if (lvl === 2) {
        children.push(sp(6));
        children.push(new Paragraph({
          heading: HeadingLevel.HEADING_2,
          children: [new TextRun({ text: txt, bold: true, font: "Arial", size: 28, color: NAVY })],
          spacing: { before: 240, after: 120 },
          border: { left: { style: BorderStyle.SINGLE, size: 16, color: BLUE, space: 8 } },
          indent: { left: 200 },
        }));
      } else if (lvl === 3) {
        children.push(new Paragraph({
          heading: HeadingLevel.HEADING_3,
          children: [new TextRun({ text: txt, bold: true, font: "Arial", size: 24, color: BLUE })],
          spacing: { before: 180, after: 80 },
        }));
      } else {
        children.push(new Paragraph({
          children: [new TextRun({ text: txt, bold: true, font: "Arial", size: 22, color: TEXT })],
          spacing: { before: 120, after: 60 },
        }));
      }
      i++; continue;
    }

    // ── Bullet list ──────────────────────────────────────────────────────
    const bm = raw.match(/^\s*[-*+]\s+(.*)/);
    if (bm) {
      const txt = bm[1].replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
      children.push(new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: parseInline(txt, false, TEXT),
        spacing: { before: 40, after: 40 },
      }));
      i++; continue;
    }

    // ── Numbered list ────────────────────────────────────────────────────
    const nm = raw.match(/^\s*\d+\.\s+(.*)/);
    if (nm) {
      const txt = nm[1].replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
      children.push(new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: parseInline(txt, false, TEXT),
        spacing: { before: 40, after: 40 },
      }));
      i++; continue;
    }

    // ── Blank line ───────────────────────────────────────────────────────
    if (!raw.trim()) { children.push(sp(3)); i++; continue; }

    // ── Regular paragraph ────────────────────────────────────────────────
    const txt = raw.trim().replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
    if (txt) {
      children.push(new Paragraph({
        children: parseInline(txt, false, TEXT),
        spacing: { before: 60, after: 80 },
        alignment: AlignmentType.JUSTIFIED,
      }));
    }
    i++;
  }

  // flush trailing table/quote
  if (inTable) { const t = buildDocxTable(parseMarkdownTable(tableLines)); if (t) { children.push(t); children.push(sp(8)); } }
  if (inQuote && quoteLines.length) {
    children.push(new Paragraph({ children: quoteLines.map(l => new TextRun({ text: l + " ", font: "Arial", size: 18, italics: true, color: "444444" })), indent: { left: 400 }, border: { left: { style: BorderStyle.SINGLE, size: 12, color: BLUE, space: 8 } }, shading: { fill: "F0F4FA", type: ShadingType.CLEAR }, spacing: { before: 80, after: 80 } }));
  }

  return children;
}

// ── Assemble document ─────────────────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 360 } } },
        }],
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 560, hanging: 360 } } },
        }],
      },
    ],
  },
  styles: {
    default: {
      document: { run: { font: "Arial", size: 20, color: TEXT } },
    },
    paragraphStyles: [
      {
        id: "Heading1", name: "Heading 1",
        basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 48, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 300, after: 200 }, outlineLevel: 0 },
      },
      {
        id: "Heading2", name: "Heading 2",
        basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial", color: NAVY },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 },
      },
      {
        id: "Heading3", name: "Heading 3",
        basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: BLUE },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 },
      },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 }, // A4
        margin: { top: M, right: M, bottom: M, left: M },
      },
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: NAVY, space: 4 } },
            children: [
              new TextRun({ text: "AI 바이브코딩 시장 현황 및 2027년 전망", font: "Arial", size: 16, color: NAVY, bold: true }),
              new TextRun({ text: "\t2026.05.07", font: "Arial", size: 16, color: GRAY }),
            ],
            tabStops: [{ type: "right", position: CONTENT_W }],
          }),
        ],
      }),
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            border: { top: { style: BorderStyle.SINGLE, size: 4, color: "D0D8E8", space: 4 } },
            alignment: AlignmentType.CENTER,
            children: [
              new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: GRAY }),
            ],
          }),
        ],
      }),
    },
    children: buildStory(),
  }],
});

// ── Write file ────────────────────────────────────────────────────────────────
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync("ai_vibecoding_report_2026.docx", buf);
  const kb = Math.round(buf.length / 1024);
  console.log(`DOCX saved (${kb} KB): ai_vibecoding_report_2026.docx`);
}).catch(err => {
  console.error("Error:", err.message);
  process.exit(1);
});
