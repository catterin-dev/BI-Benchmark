from pathlib import Path
import re
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

BASE = Path(__file__).resolve().parent
SOURCE = BASE / "INFORME_RESULTADOS.md"
OUTPUT = BASE / "INFORME_RESULTADOS_ACADEMICO.docx"

if not SOURCE.exists():
    raise FileNotFoundError(f"No se encontro el archivo: {SOURCE}")

text = SOURCE.read_text(encoding="utf-8-sig")
lines = text.splitlines()

doc = Document()
section = doc.sections[0]
section.top_margin = Inches(1)
section.bottom_margin = Inches(1)
section.left_margin = Inches(1)
section.right_margin = Inches(1)

# Estilo general compatible con una presentacion academica basada en APA 7
normal = doc.styles["Normal"]
normal.font.name = "Times New Roman"
normal.font.size = Pt(12)
normal.paragraph_format.line_spacing = 2
normal.paragraph_format.space_after = Pt(0)

for style_name in ["Title", "Heading 1", "Heading 2", "Heading 3"]:
    style = doc.styles[style_name]
    style.font.name = "Times New Roman"
    style.font.color.rgb = None

doc.styles["Heading 1"].font.size = Pt(14)
doc.styles["Heading 1"].font.bold = True
doc.styles["Heading 1"].paragraph_format.space_before = Pt(12)
doc.styles["Heading 1"].paragraph_format.space_after = Pt(6)
doc.styles["Heading 1"].paragraph_format.keep_with_next = True

doc.styles["Heading 2"].font.size = Pt(12)
doc.styles["Heading 2"].font.bold = True
doc.styles["Heading 2"].paragraph_format.keep_with_next = True

# Numero de pagina en el pie de pagina
footer = section.footer.paragraphs[0]
footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
run = footer.add_run()
field = OxmlElement("w:fldSimple")
field.set(qn("w:instr"), "PAGE")
run._r.addnext(field)

# Portada: no se inventan autor, docente ni fecha
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(55)
r = p.add_run("UNIVERSIDAD NACIONAL DEL ALTIPLANO DE PUNO")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(14)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(18)
r = p.add_run("INFORME DE RESULTADOS")
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(16)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(18)
r = p.add_run(
    "Benchmark de ingesta de datos de las arquitecturas "
    "Lambda y Kappa"
)
r.bold = True
r.font.name = "Times New Roman"
r.font.size = Pt(14)

for label in [
    "",
    "Programa de estudios / posgrado: ______________________________",
    "Asignatura: _________________________________________________",
    "Autor(a): ___________________________________________________",
    "Docente: ____________________________________________________",
    "Puno - Peru",
    "Fecha: ______________________________________________________",
]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.5
    p.add_run(label)

doc.add_page_break()

# Indice sencillo basado en los encabezados existentes
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = p.add_run("CONTENIDO")
r.bold = True
r.font.size = Pt(14)

headings = []
for line in lines:
    m = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
    if m:
        heading = m.group(2).strip()
        if heading.lower() not in ["contenido", "indice", "índice"]:
            headings.append((len(m.group(1)), heading))

for level, heading in headings:
    p = doc.add_paragraph()
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.left_indent = Inches(0.25 * (level - 1))
    p.paragraph_format.space_after = Pt(3)
    p.add_run(heading)

doc.add_page_break()

def shade_cell(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    tc_pr.append(shd)

def set_cell_text(cell, value, bold=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.space_after = Pt(0)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(value.strip())
    r.font.name = "Times New Roman"
    r.font.size = Pt(10)
    r.bold = bold
    cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

def add_markdown_table(rows):
    parsed = []
    for row in rows:
        cells = [c.strip() for c in row.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", c.replace(" ", "")) for c in cells):
            continue
        parsed.append(cells)

    if not parsed:
        return

    col_count = max(len(row) for row in parsed)
    table = doc.add_table(rows=0, cols=col_count)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    for row_index, values in enumerate(parsed):
        cells = table.add_row().cells
        for j in range(col_count):
            value = values[j] if j < len(values) else ""
            set_cell_text(cells[j], value, bold=(row_index == 0))
            if row_index == 0:
                shade_cell(cells[j], "D9EAF7")

    doc.add_paragraph().paragraph_format.space_after = Pt(0)

def add_text_paragraph(value):
    value = value.strip()
    if not value:
        return

    if value in ["---", "***"]:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1
        p.add_run("—" * 35)
        return

    if value.startswith(">"):
        value = value.lstrip("> ").strip()

    if value.startswith(("- ", "* ")):
        p = doc.add_paragraph(style="List Bullet")
        p.paragraph_format.line_spacing = 2
        value = value[2:].strip()
    elif re.match(r"^\d+\.\s+", value):
        p = doc.add_paragraph(style="List Number")
        p.paragraph_format.line_spacing = 2
        value = re.sub(r"^\d+\.\s+", "", value)
    else:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Inches(0.5)
        p.paragraph_format.line_spacing = 2

    # Respeta negritas sencillas escritas como **texto**
    pieces = re.split(r"(\*\*.*?\*\*)", value)
    for piece in pieces:
        if piece.startswith("**") and piece.endswith("**"):
            r = p.add_run(piece[2:-2])
            r.bold = True
        else:
            p.add_run(piece)

i = 0
while i < len(lines):
    line = lines[i].strip()

    if not line:
        i += 1
        continue

    if line.startswith("|"):
        table_lines = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            table_lines.append(lines[i].strip())
            i += 1
        add_markdown_table(table_lines)
        continue

    match = re.match(r"^(#{1,3})\s+(.+)$", line)
    if match:
        level = len(match.group(1))
        heading = match.group(2).strip()
        # El titulo principal ya aparece en la portada
        if level == 1:
            doc.add_heading(heading, level=1)
        else:
            doc.add_heading(heading, level=level)
        i += 1
        continue

    # Une lineas consecutivas de un mismo parrafo
    paragraph_lines = [line]
    i += 1
    while i < len(lines):
        nxt = lines[i].strip()
        if not nxt or nxt.startswith("|") or re.match(r"^#{1,3}\s+", nxt):
            break
        paragraph_lines.append(nxt)
        i += 1

    add_text_paragraph(" ".join(paragraph_lines))

doc.core_properties.title = (
    "Informe de resultados: benchmark de ingesta Lambda y Kappa"
)
doc.core_properties.subject = "Comparacion experimental de rendimiento"
doc.core_properties.author = "Autor por completar"

doc.save(OUTPUT)
print(f"Documento creado: {OUTPUT}")
print(f"Tamano: {OUTPUT.stat().st_size:,} bytes")
