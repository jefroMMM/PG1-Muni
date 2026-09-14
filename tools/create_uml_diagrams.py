from __future__ import annotations

import html
import math
import textwrap
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor

from create_diagrams import specs


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion"
IMAGES = OUT / "imagenes"
W, H = 1800, 1000
INK = "#14213D"
EDGE = "#415A77"
BG = "#F7F6F2"
PALETTE = {
    "blue": "#D7E8F7",
    "green": "#DDEFD9",
    "yellow": "#F8E8B5",
    "purple": "#E7DCF3",
    "orange": "#FBE2CF",
    "gray": "#F0F2F4",
}


def font(size, bold=False):
    name = "arialbd.ttf" if bold else "arial.ttf"
    path = Path("C:/Windows/Fonts") / name
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


F_TITLE = font(34, True)
F_SUB = font(18, True)
F_NODE = font(19, True)
F_TEXT = font(16)
F_SMALL = font(14)


def wrap(value, width=20):
    return "\n".join(textwrap.wrap(str(value), width=width, break_long_words=False))


def text_center(draw, box, value, fnt=F_NODE, fill=INK, width=20):
    x1, y1, x2, y2 = box
    draw.multiline_text(((x1 + x2) / 2, (y1 + y2) / 2), wrap(value, width), anchor="mm", align="center", font=fnt, fill=fill, spacing=3)


def arrow(draw, start, end, label="", y_offset=-16):
    draw.line((*start, *end), fill=EDGE, width=3)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    size = 12
    left = (end[0] - size * math.cos(angle - math.pi / 6), end[1] - size * math.sin(angle - math.pi / 6))
    right = (end[0] - size * math.cos(angle + math.pi / 6), end[1] - size * math.sin(angle + math.pi / 6))
    draw.polygon([end, left, right], fill=EDGE)
    if label:
        mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + y_offset
        bounds = draw.textbbox((0, 0), label, font=F_SMALL)
        draw.rounded_rectangle((mx + bounds[0] - 5, my + bounds[1] - 3, mx + bounds[2] + 5, my + bounds[3] + 3), radius=4, fill=BG)
        draw.text((mx, my), label, anchor="mm", font=F_SMALL, fill=EDGE)


def header(draw, spec, section):
    draw.rectangle((0, 0, W, H), fill=BG)
    draw.text((60, 34), spec["title"], font=F_TITLE, fill=INK)
    draw.text((62, 84), section, font=F_SUB, fill="#0E7C66")
    draw.line((60, 118, W - 60, 118), fill="#C8D1DA", width=2)


def actor(draw, x, y, label):
    draw.ellipse((x - 18, y, x + 18, y + 36), outline=INK, width=3)
    draw.line((x, y + 36, x, y + 100), fill=INK, width=3)
    draw.line((x - 42, y + 62, x + 42, y + 62), fill=INK, width=3)
    draw.line((x, y + 100, x - 38, y + 148), fill=INK, width=3)
    draw.line((x, y + 100, x + 38, y + 148), fill=INK, width=3)
    draw.text((x, y + 178), label, anchor="mm", font=F_NODE, fill=INK)


def usecase(draw, box, label):
    draw.ellipse(box, fill=PALETTE["green"], outline=INK, width=3)
    text_center(draw, box, label, width=21)


def component(draw, box, label):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=12, fill=PALETTE["blue"], outline=INK, width=3)
    draw.rectangle((x1 + 14, y1 + 14, x1 + 52, y1 + 42), fill="#FFFFFF", outline=INK, width=2)
    draw.rectangle((x1 + 14, y1 + 46, x1 + 52, y1 + 74), fill="#FFFFFF", outline=INK, width=2)
    text_center(draw, (x1 + 58, y1, x2, y2), label, width=18)


CLASS_INFO = {
    "MapConfig": ("+ title\n+ background\n+ markers", "+ routes()\n+ decorations()"),
    "Route": ("+ id\n+ name\n+ archived", "+ nodes()\n+ segmentAssets()"),
    "Node": ("+ x\n+ y", ""),
    "Marker": ("+ assetId\n+ x, y\n+ width", "+ rotate()\n+ mirror()"),
    "Decoration": ("+ assetId\n+ x, y\n+ rotation", "+ resize()\n+ mirror()"),
    "Asset": ("+ id\n+ name\n+ src", ""),
    "SegmentOption": ("+ rotation\n+ mirrored", ""),
    "ConfigRepository": ("+ configPath", "+ load()\n+ save()"),
    "UploadService": ("+ uploadDir", "+ upload()"),
}


def class_box(draw, box, label):
    x1, y1, x2, y2 = box
    fields, methods = CLASS_INFO.get(label, ("", ""))
    draw.rectangle(box, fill=PALETTE["purple"], outline=INK, width=3)
    y_name, y_attr = y1 + 36, y1 + 106
    draw.line((x1, y_name, x2, y_name), fill=INK, width=2)
    draw.line((x1, y_attr, x2, y_attr), fill=INK, width=2)
    draw.text(((x1 + x2) / 2, y1 + 18), label, anchor="mm", font=F_NODE, fill=INK)
    draw.multiline_text((x1 + 12, y_name + 10), fields, font=F_SMALL, fill=INK, spacing=2)
    draw.multiline_text((x1 + 12, y_attr + 10), methods, font=F_SMALL, fill=INK, spacing=2)


def state(draw, box, label):
    draw.rounded_rectangle(box, radius=18, fill=PALETTE["orange"], outline=INK, width=3)
    text_center(draw, box, label, width=16)


def activity(draw, box, label):
    draw.rounded_rectangle(box, radius=16, fill=PALETTE["green"], outline=INK, width=3)
    text_center(draw, box, label, width=18)


def object_box(draw, box, label, blue=True):
    draw.rounded_rectangle(box, radius=8, fill=PALETTE["blue"] if blue else PALETTE["gray"], outline=INK, width=3)
    text_center(draw, box, label, width=18)


def use_case_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de casos de uso")
    draw.rounded_rectangle((390, 170, 1710, 880), radius=16, outline=INK, width=3, fill="#FCFCFA")
    draw.text((420, 194), "Sistema de mapas municipales", font=F_SUB, fill=INK)
    actor(draw, 180, 390, spec["nodes"][0][1])
    cases = [node[1] for node in spec["nodes"][1:]]
    positions = []
    for index, label in enumerate(cases):
        col, row = index % 3, index // 3
        x = 610 + col * 370
        y = 300 + row * 260
        box = (x - 140, y - 55, x + 140, y + 55)
        usecase(draw, box, label)
        positions.append((box, label))
    for index, (box, label) in enumerate(positions):
        cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
        if index == 0:
            arrow(draw, (252, 466), (box[0], cy), "", 0)
        elif index > 0:
            source = positions[0][0]
            arrow(draw, (source[2], (source[1] + source[3]) / 2), (box[0], cy), "<<include>>", -18 if index % 2 else 18)


def component_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de componentes")
    nodes = spec["nodes"]
    grid = {}
    for index, (node_id, label, kind) in enumerate(nodes):
        col, row = index % 3, index // 3
        x, y = 180 + col * 560, 230 + row * 230
        grid[node_id] = (x, y, x + 290, y + 120)
        component(draw, grid[node_id], label)
    for source, target, label in spec["edges"]:
        a, b = grid[source], grid[target]
        arrow(draw, ((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1]), label)


def class_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de clases")
    grid = {}
    for index, (node_id, label, kind) in enumerate(spec["nodes"]):
        col, row = index % 3, index // 3
        x, y = 120 + col * 570, 180 + row * 250
        grid[node_id] = (x, y, x + 310, y + 190)
        class_box(draw, grid[node_id], label)
    for source, target, label in spec["edges"]:
        a, b = grid[source], grid[target]
        arrow(draw, ((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1]), label)


def sequence_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de secuencia")
    participants = spec["nodes"]
    x_by_id = {}
    for index, (node_id, label, kind) in enumerate(participants):
        x = 150 + index * ((W - 300) / max(1, len(participants) - 1))
        x_by_id[node_id] = x
        if kind == "actor":
            actor(draw, x, 160, label)
        else:
            object_box(draw, (x - 110, 185, x + 110, 255), label)
        draw.line((x, 285, x, 860), fill=EDGE, width=2)
        for y in range(300, 860, 12):
            draw.line((x, y, x, y + 6), fill=BG, width=2)
    for index, (source, target, label) in enumerate(spec["edges"], 1):
        y = 350 + (index - 1) * 95
        start, end = x_by_id[source], x_by_id[target]
        arrow(draw, (start, y), (end, y), f"{index}. {label}", -21)


def state_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de estados")
    nodes = spec["nodes"]
    xs = [180 + i * ((W - 360) / max(1, len(nodes) - 1)) for i in range(len(nodes))]
    draw.ellipse((80, 450, 110, 480), fill=INK)
    previous = (110, 465)
    boxes = []
    for index, ((node_id, label, kind), x) in enumerate(zip(nodes, xs)):
        box = (x - 105, 420, x + 105, 510)
        boxes.append(box)
        state(draw, box, label)
        arrow(draw, previous, (box[0], 465), "" if index == 0 else "")
        previous = (box[2], 465)
    draw.ellipse((W - 100, 445, W - 60, 485), outline=INK, width=3)
    draw.ellipse((W - 91, 454, W - 69, 476), fill=INK)
    arrow(draw, previous, (W - 100, 465), "")
    for index, edge in enumerate(spec["edges"]):
        if index < len(boxes) - 1:
            label = edge[2]
            x = (boxes[index][2] + boxes[index + 1][0]) / 2
            draw.text((x, 410), label, anchor="mm", font=F_SMALL, fill=EDGE)


def activity_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de actividades")
    nodes = spec["nodes"]
    x = W / 2
    draw.ellipse((x - 16, 150, x + 16, 182), fill=INK)
    previous = (x, 182)
    boxes = []
    for index, (node_id, label, kind) in enumerate(nodes):
        y = 220 + index * 88
        box = (x - 190, y, x + 190, y + 58)
        boxes.append(box)
        activity(draw, box, label)
        arrow(draw, previous, (x, box[1]), "")
        previous = (x, box[3])
    draw.ellipse((x - 21, previous[1] + 35, x + 21, previous[1] + 77), outline=INK, width=3)
    draw.ellipse((x - 11, previous[1] + 45, x + 11, previous[1] + 67), fill=INK)
    arrow(draw, previous, (x, previous[1] + 35), "")


def collaboration_diagram(draw, spec):
    header(draw, spec, "Diagrama UML de colaboración")
    grid = {}
    for index, (node_id, label, kind) in enumerate(spec["nodes"]):
        col, row = index % 3, index // 3
        x, y = 220 + col * 610, 260 + row * 280
        grid[node_id] = (x, y, x + 250, y + 100)
        if kind == "actor":
            actor(draw, x + 125, y - 50, label)
        else:
            object_box(draw, grid[node_id], f"{label}", blue=kind == "component")
    for source, target, label in spec["edges"]:
        a, b = grid[source], grid[target]
        arrow(draw, ((a[0] + a[2]) / 2, a[3]), ((b[0] + b[2]) / 2, b[1]), label)


def render(spec):
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    kind = spec["kind"]
    if kind == "Casos de uso":
        use_case_diagram(draw, spec)
    elif kind == "Componentes":
        component_diagram(draw, spec)
    elif kind == "Clases":
        class_diagram(draw, spec)
    elif kind == "Secuencias":
        sequence_diagram(draw, spec)
    elif kind == "Estados":
        state_diagram(draw, spec)
    elif kind == "Actividades":
        activity_diagram(draw, spec)
    else:
        collaboration_diagram(draw, spec)
    return image


def cell(cell_id, value, style, x, y, w, h, parent="1"):
    return f'<mxCell id="{cell_id}" value="{html.escape(value)}" style="{style}" vertex="1" parent="{parent}"><mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>'


def edge(cell_id, source, target, label="", style="endArrow=block;html=1;rounded=0;"):
    return f'<mxCell id="{cell_id}" value="{html.escape(label)}" style="{style}labelBackgroundColor=#F7F6F2;" edge="1" parent="1" source="{source}" target="{target}"><mxGeometry relative="1" as="geometry"/></mxCell>'


def page_use_case(spec, index):
    cells = [cell(f"boundary-{index}", "Sistema de mapas municipales", "rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#14213D;fontStyle=1;align=left;verticalAlign=top;spacingTop=14;spacingLeft=16;", 390, 150, 1320, 690), cell(f"actor-{index}", spec["nodes"][0][1], "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;fontStyle=1;", 130, 380, 110, 180)]
    use_nodes = spec["nodes"][1:]
    for pos, (node_id, label, kind) in enumerate(use_nodes):
        col, row = pos % 3, pos // 3
        x, y = 500 + col * 390, 290 + row * 250
        cells.append(cell(f"n-{index}-{node_id}", label, "ellipse;whiteSpace=wrap;html=1;fillColor=#DDEFD9;strokeColor=#14213D;fontStyle=1;", x, y, 260, 100))
        if pos == 0:
            cells.append(edge(f"e-{index}-{pos}", f"actor-{index}", f"n-{index}-{node_id}"))
        else:
            cells.append(edge(f"e-{index}-{pos}", f"n-{index}-{use_nodes[0][0]}", f"n-{index}-{node_id}", "&lt;&lt;include&gt;&gt;", "endArrow=open;dashed=1;html=1;"))
    return "".join(cells)


def page_components(spec, index):
    cells = []
    nodes = {}
    for pos, (node_id, label, kind) in enumerate(spec["nodes"]):
        col, row = pos % 3, pos // 3
        x, y = 160 + col * 560, 200 + row * 220
        nodes[node_id] = f"n-{index}-{node_id}"
        cells.append(cell(nodes[node_id], label, "shape=component;whiteSpace=wrap;html=1;fillColor=#D7E8F7;strokeColor=#14213D;fontStyle=1;", x, y, 300, 110))
    for pos, (source, target, label) in enumerate(spec["edges"]):
        cells.append(edge(f"e-{index}-{pos}", nodes[source], nodes[target], label, "endArrow=block;edgeStyle=orthogonalEdgeStyle;html=1;"))
    return "".join(cells)


def page_classes(spec, index):
    cells, nodes = [], {}
    for pos, (node_id, label, kind) in enumerate(spec["nodes"]):
        col, row = pos % 3, pos // 3
        x, y = 120 + col * 570, 170 + row * 245
        fields, methods = CLASS_INFO.get(label, ("", ""))
        value = f"&lt;b&gt;{html.escape(label)}&lt;/b&gt;&lt;hr&gt;{html.escape(fields).replace(chr(10), '&lt;br&gt;')}&lt;hr&gt;{html.escape(methods).replace(chr(10), '&lt;br&gt;')}"
        nodes[node_id] = f"n-{index}-{node_id}"
        cells.append(cell(nodes[node_id], value, "swimlane;html=1;rounded=0;whiteSpace=wrap;fillColor=#E7DCF3;strokeColor=#14213D;align=left;", x, y, 310, 180))
    for pos, (source, target, label) in enumerate(spec["edges"]):
        cells.append(edge(f"e-{index}-{pos}", nodes[source], nodes[target], label, "endArrow=open;edgeStyle=orthogonalEdgeStyle;html=1;"))
    return "".join(cells)


def page_sequence(spec, index):
    cells, nodes = [], {}
    participants = spec["nodes"]
    for pos, (node_id, label, kind) in enumerate(participants):
        x = 70 + pos * int(1650 / max(1, len(participants) - 1))
        nodes[node_id] = f"n-{index}-{node_id}"
        style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;" if kind == "actor" else "rounded=1;whiteSpace=wrap;html=1;fillColor=#D7E8F7;strokeColor=#14213D;fontStyle=1;"
        cells.append(cell(nodes[node_id], label, style, x, 120, 160, 70))
        cells.append(cell(f"life-{index}-{node_id}", "", "line;strokeWidth=1;dashed=1;", x + 80, 210, 1, 580))
    for pos, (source, target, label) in enumerate(spec["edges"]):
        cells.append(edge(f"e-{index}-{pos}", nodes[source], nodes[target], f"{pos + 1}. {label}", "endArrow=block;html=1;exitY=0.5;entryY=0.5;"))
    return "".join(cells)


def page_states(spec, index):
    cells = [cell(f"start-{index}", "", "ellipse;fillColor=#14213D;strokeColor=#14213D;", 80, 440, 30, 30)]
    nodes = []
    for pos, (node_id, label, kind) in enumerate(spec["nodes"]):
        x = 180 + pos * int(1340 / max(1, len(spec["nodes"]) - 1))
        node = f"n-{index}-{node_id}"
        nodes.append(node)
        cells.append(cell(node, label, "rounded=1;whiteSpace=wrap;html=1;fillColor=#FBE2CF;strokeColor=#14213D;fontStyle=1;", x, 410, 180, 90))
    cells.append(edge(f"e-start-{index}", f"start-{index}", nodes[0]))
    for pos, (source, target, label) in enumerate(spec["edges"]):
        if pos < len(nodes) - 1:
            cells.append(edge(f"e-{index}-{pos}", nodes[pos], nodes[pos + 1], label))
    cells.append(cell(f"end-{index}", "", "ellipse;fillColor=#14213D;strokeColor=#14213D;", 1710, 435, 45, 45))
    cells.append(edge(f"e-end-{index}", nodes[-1], f"end-{index}"))
    return "".join(cells)


def page_activities(spec, index):
    cells = [cell(f"start-{index}", "", "ellipse;fillColor=#14213D;strokeColor=#14213D;", 875, 130, 30, 30)]
    nodes = []
    for pos, (node_id, label, kind) in enumerate(spec["nodes"]):
        y = 210 + pos * 88
        node = f"n-{index}-{node_id}"
        nodes.append(node)
        cells.append(cell(node, label, "rounded=1;whiteSpace=wrap;html=1;fillColor=#DDEFD9;strokeColor=#14213D;fontStyle=1;", 720, y, 340, 56))
    cells.append(edge(f"e-start-{index}", f"start-{index}", nodes[0]))
    for pos in range(len(nodes) - 1):
        cells.append(edge(f"e-{index}-{pos}", nodes[pos], nodes[pos + 1]))
    cells.append(cell(f"end-{index}", "", "ellipse;fillColor=#14213D;strokeColor=#14213D;", 868, 910, 45, 45))
    cells.append(edge(f"e-end-{index}", nodes[-1], f"end-{index}"))
    return "".join(cells)


def page_collaboration(spec, index):
    cells, nodes = [], {}
    for pos, (node_id, label, kind) in enumerate(spec["nodes"]):
        col, row = pos % 3, pos // 3
        x, y = 200 + col * 600, 240 + row * 280
        nodes[node_id] = f"n-{index}-{node_id}"
        style = "shape=umlActor;verticalLabelPosition=bottom;verticalAlign=top;html=1;" if kind == "actor" else "rounded=1;whiteSpace=wrap;html=1;fillColor=#D7E8F7;strokeColor=#14213D;fontStyle=1;"
        cells.append(cell(nodes[node_id], label, style, x, y, 250, 90))
    for pos, (source, target, label) in enumerate(spec["edges"]):
        cells.append(edge(f"e-{index}-{pos}", nodes[source], nodes[target], label, "endArrow=block;edgeStyle=orthogonalEdgeStyle;html=1;"))
    return "".join(cells)


def page(spec, index):
    title = cell(f"title-{index}", spec["title"], "text;html=1;strokeColor=none;fillColor=none;fontSize=28;fontStyle=1;fontColor=#14213D;", 50, 25, 900, 50)
    kind = spec["kind"]
    if kind == "Casos de uso": body = page_use_case(spec, index)
    elif kind == "Componentes": body = page_components(spec, index)
    elif kind == "Clases": body = page_classes(spec, index)
    elif kind == "Secuencias": body = page_sequence(spec, index)
    elif kind == "Estados": body = page_states(spec, index)
    elif kind == "Actividades": body = page_activities(spec, index)
    else: body = page_collaboration(spec, index)
    return title + body


def write_drawio(all_specs):
    pages = []
    for index, spec in enumerate(all_specs, 1):
        pages.append(f'<diagram id="uml-{index}-{uuid.uuid4().hex[:8]}" name="{html.escape(spec["title"])}"><mxGraphModel dx="1800" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="1000"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{page(spec, index)}</root></mxGraphModel></diagram>')
    (OUT / "diagramas-sistema.drawio").write_text('<mxfile host="app.diagrams.net" modified="2026-09-07T00:00:00.000Z" agent="Codex" version="24.7.17">' + "".join(pages) + "</mxfile>", encoding="utf-8")


def write_docx(all_specs):
    doc = Document()
    for section in doc.sections:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = Inches(11), Inches(8.5)
        section.left_margin = section.right_margin = Inches(0.55)
        section.top_margin = section.bottom_margin = Inches(0.5)
    styles = doc.styles
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        styles[name].font.name = "Arial"
        styles[name].font.color.rgb = RGBColor(0, 0, 0)
    styles["Normal"].font.size = Pt(10)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Diagramas UML del Sistema de Mapas")
    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    subtitle.add_run("Mapa  MapaR  MapaConf y MapaRConf").bold = True
    doc.add_paragraph("Documento de modelado UML basado en la aplicación actual. Incluye visores de rutas, editores gráficos, API Flask, configuración compartida, assets, iconos, decoraciones y audio.")
    doc.add_paragraph("El archivo diagramas-sistema.drawio contiene las mismas veinte páginas en formato editable.")
    doc.add_page_break()
    current = None
    for number, spec in enumerate(all_specs, 1):
        if spec["kind"] != current:
            current = spec["kind"]
            doc.add_heading(spec["kind"], level=1)
        doc.add_heading(f"{number}. {spec['title']}", level=2)
        doc.add_paragraph(spec["description"])
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(IMAGES / f"{spec['slug']}.png"), width=Inches(9.65))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.add_run(f"Figura {number}. {spec['title']}").italic = True
        if number < len(all_specs):
            doc.add_page_break()
    doc.save(OUT / "diagramas-sistema.docx")


def main():
    OUT.mkdir(exist_ok=True)
    IMAGES.mkdir(exist_ok=True)
    all_specs = specs()
    for spec in all_specs:
        render(spec).save(IMAGES / f"{spec['slug']}.png")
    write_drawio(all_specs)
    write_docx(all_specs)
    print(f"Generados {len(all_specs)} diagramas UML.")


if __name__ == "__main__":
    main()
