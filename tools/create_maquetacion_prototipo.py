from pathlib import Path
from PIL import Image, ImageDraw, ImageOps
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion" / "maquetacion-prototipo.docx"
PLACEHOLDER = Path(r"C:\Users\masje\AppData\Local\Temp\codex-clipboard-0416d70c-ba13-47f7-b14c-b51d593f2547.png")
CAPTURE_DIR = ROOT / "documentacion" / "capturas-prototipo"
CAPTURE_SOURCES = {
    "Mapa": (Path(r"C:\Users\masje\AppData\Local\Temp\codex-clipboard-b8c6961f-7553-4b86-8694-e2e176edf856.png"), (4, 166, 1191, 761)),
    "MapaConf": (Path(r"C:\Users\masje\AppData\Local\Temp\codex-clipboard-94aff093-b283-44ba-aad4-ea6ac2b195c8.png"), (38, 336, 1006, 821)),
    "MapaR": (Path(r"C:\Users\masje\AppData\Local\Temp\codex-clipboard-3cd6f24e-054a-421a-b3b1-10a5da2dc8cf.png"), (13, 173, 1199, 765)),
    "MapaRConf": (Path(r"C:\Users\masje\AppData\Local\Temp\codex-clipboard-d972e605-8bc0-4b97-abe1-bcb3636b2259.png"), (36, 316, 1065, 830)),
}

SCREENS = [
    ("Mapa", "Consulta de recorridos dentro del terminal", "El mapa ocupa el area principal. El panel lateral presenta la identidad institucional y las indicaciones de la dependencia seleccionada. La barra inferior contiene los botones de acceso a las rutas."),
    ("MapaR", "Consulta de recorridos urbanos", "El mapa urbano funciona como elemento principal. Los marcadores ubican los destinos y el panel lateral comunica el destino elegido. Los botones inferiores permiten cambiar entre recorridos."),
    ("MapaConf", "Edicion de rutas internas", "La vista de configuracion mantiene el mapa como espacio de trabajo y agrega un panel de herramientas. El usuario puede seleccionar rutas, editar nodos, escribir indicaciones y guardar la configuracion."),
    ("MapaRConf", "Edicion visual del mapa urbano", "El editor urbano incorpora controles para cambiar el fondo, colocar iconos y administrar decoraciones. Los elementos visuales se pueden mover, girar, espejar y redimensionar."),
]


def shade(paragraph, fill):
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def set_cell_border(cell, color="D9D9D9"):
    tc_pr = cell._tc.get_or_add_tcPr()
    borders = OxmlElement("w:tcBorders")
    for edge in ("top", "left", "bottom", "right"):
        tag = OxmlElement(f"w:{edge}")
        tag.set(qn("w:val"), "single")
        tag.set(qn("w:sz"), "6")
        tag.set(qn("w:color"), color)
        borders.append(tag)
    tc_pr.append(borders)


def add_capture(doc, image_path, screen_name):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image_path), width=Inches(6.85))
    cap = doc.add_paragraph()
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = cap.add_run(f"Interfaz {screen_name} con el mapa sustituido por Your Image Here")
    run.italic = True
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(89, 89, 89)


def add_screen_table(doc, name, subtitle, description):
    heading = doc.add_heading(name, level=2)
    heading.paragraph_format.space_before = Pt(10)
    doc.add_paragraph(subtitle).runs[0].bold = True
    doc.add_paragraph(description)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = False
    table.columns[0].width = Inches(3.15)
    table.columns[1].width = Inches(6.15)
    left, right = table.rows[0].cells
    left.width = Inches(3.15)
    right.width = Inches(6.15)
    set_cell_border(left)
    set_cell_border(right)
    add_image_to_cell(left, CAPTURE_DIR / f"{name}.png", name)
    right.text = ""
    lines = [
        ("Distribucion", "Mapa o lienzo a la izquierda; panel de informacion y controles a la derecha; botones de rutas en la parte inferior."),
        ("Identidad", "El logotipo aparece en el panel institucional para reforzar el origen municipal sin quitar protagonismo al mapa."),
        ("Color", "Azul marino para titulos y textos principales, verde para acciones confirmadas y fondos claros para mantener contraste."),
        ("Tipografia", "Una tipografia sans serif legible para lectura rapida en pantallas y botones de uso frecuente."),
    ]
    for label, text in lines:
        p = right.add_paragraph()
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(label + ": ")
        r.bold = True
        p.add_run(text)


def add_image_to_cell(cell, image_path, screen_name):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(str(image_path), width=Inches(3.05))
    c = cell.add_paragraph()
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = c.add_run(f"Captura completa\n{screen_name}")
    r.italic = True
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(89, 89, 89)


def main():
    CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    placeholder = Image.open(PLACEHOLDER).convert("RGB")
    for name, (source, rect) in CAPTURE_SOURCES.items():
        base = Image.open(source).convert("RGB")
        x1, y1, x2, y2 = rect
        replacement = ImageOps.fit(placeholder, (x2 - x1, y2 - y1), method=Image.Resampling.LANCZOS)
        mask = Image.new("L", replacement.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, replacement.width - 1, replacement.height - 1), radius=12, fill=255)
        base.paste(replacement, (x1, y1), mask)
        base.save(CAPTURE_DIR / f"{name}.png")

    doc = Document()
    section = doc.sections[0]
    section.orientation = WD_ORIENT.LANDSCAPE
    section.page_width = Inches(11)
    section.page_height = Inches(8.5)
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.55)
    section.right_margin = Inches(0.55)

    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    styles["Normal"].font.color.rgb = RGBColor(31, 41, 55)
    styles["Title"].font.name = "Arial"
    styles["Title"].font.color.rgb = RGBColor(0, 0, 0)
    for level in ("Heading 1", "Heading 2"):
        styles[level].font.name = "Arial"
        styles[level].font.color.rgb = RGBColor(0, 0, 0)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Maquetacion y prototipo del sistema de mapas")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Mapa, MapaR, MapaConf y MapaRConf").bold = True
    doc.add_paragraph("Este documento presenta las decisiones visuales de las pantallas y una muestra no funcional de su apariencia. Los marcadores visuales se dejan como espacios reservados para incorporar las capturas finales.")

    doc.add_heading("5.2 Maquetacion", level=1)
    doc.add_paragraph("La maquetacion organiza el contenido para que el usuario pueda localizar una ruta, leer sus indicaciones y regresar al mapa sin perder contexto. La pantalla utiliza una composicion de dos zonas: el mapa como area de trabajo y un panel lateral para identidad, informacion y acciones.")
    doc.add_heading("Criterios visuales", level=2)
    for label, text in [
        ("Mapa y panel", "El mapa tiene el mayor peso visual porque es el elemento que muestra la ubicacion y el recorrido. El panel lateral concentra el nombre del destino, las indicaciones y los controles."),
        ("Logotipo", "El logotipo se coloca dentro del panel institucional, en la parte superior, para identificar la aplicacion sin cubrir calles, nodos ni marcadores."),
        ("Menu y rutas", "Las rutas se presentan como botones claros y separados. En los editores, el menu se convierte en un panel de herramientas para evitar mezclar acciones de edicion con la vista publica."),
        ("Colores", "El azul marino comunica identidad y estabilidad; el verde distingue acciones confirmadas y recorridos activos; los fondos claros reducen la fatiga visual sobre mapas detallados."),
        ("Tipografia", "Se recomienda Arial o una sans serif equivalente para asegurar lectura en distintos equipos. Los titulos usan mayor peso y las indicaciones se dividen en pasos numerados."),
    ]:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(5)
        p.add_run(label + ". ").bold = True
        p.add_run(text)
    for name, subtitle, description in SCREENS:
        add_screen_table(doc, name, subtitle, description)

    doc.add_page_break()
    doc.add_heading("5.3 Prototipo", level=1)
    doc.add_paragraph("El prototipo es una representacion visual no funcional de la version final. Permite validar la posicion de los elementos, la jerarquia de la informacion y la consistencia entre las cuatro rutas del sistema antes de realizar pruebas de funcionamiento.")
    for name, subtitle, description in SCREENS:
        doc.add_heading(name, level=2)
        doc.add_paragraph(subtitle)
        doc.add_paragraph(description)
        add_capture(doc, CAPTURE_DIR / f"{name}.png", name)
        doc.add_paragraph("Interaccion prevista: el usuario selecciona una ruta o herramienta, observa el cambio en el mapa y consulta las indicaciones en el panel correspondiente.")
        if name != SCREENS[-1][0]:
            doc.add_page_break()

    doc.save(OUT)
    print(OUT)


if __name__ == "__main__":
    main()
