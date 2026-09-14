from __future__ import annotations

import html
import math
import os
import textwrap
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion"
IMG_DIR = OUT / "imagenes"
OUT.mkdir(exist_ok=True)
IMG_DIR.mkdir(exist_ok=True)

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
]
BOLD_CANDIDATES = [
    Path("C:/Windows/Fonts/arialbd.ttf"),
    Path("C:/Windows/Fonts/segoeuib.ttf"),
]


def load_font(size: int, bold: bool = False):
    candidates = BOLD_CANDIDATES if bold else FONT_CANDIDATES
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


FONT_TITLE = load_font(36, True)
FONT_SUBTITLE = load_font(21, True)
FONT_NODE = load_font(22, True)
FONT_LABEL = load_font(17, False)
FONT_SMALL = load_font(16, False)

COLORS = {
    "actor": (238, 225, 188),
    "usecase": (205, 232, 224),
    "component": (204, 221, 240),
    "class": (224, 215, 240),
    "state": (250, 220, 197),
    "activity": (221, 235, 203),
    "object": (230, 230, 230),
    "edge": (54, 63, 70),
    "ink": (23, 26, 74),
    "background": (248, 247, 243),
}


def wrap(text: str, width: int = 24):
    return "\n".join(textwrap.wrap(text, width=width, break_long_words=False))


def specs():
    return [
        {
            "kind": "Casos de uso",
            "slug": "01-casos-uso-mapa",
            "title": "Caso de uso Mapa",
            "description": "El visitante selecciona una dependencia del terminal y consulta un recorrido visual con indicaciones y audio.",
            "nodes": [
                ("u", "Usuario", "actor"), ("m", "Mapa del terminal", "usecase"),
                ("s", "Seleccionar dependencia", "usecase"), ("r", "Mostrar ruta", "usecase"),
                ("i", "Mostrar indicaciones", "usecase"), ("a", "Reproducir audio", "usecase"),
            ],
            "edges": [("u", "s", "inicia"), ("s", "m", "usa"), ("m", "r", "incluye"), ("m", "i", "incluye"), ("m", "a", "opcional")],
        },
        {
            "kind": "Casos de uso",
            "slug": "02-casos-uso-mapar",
            "title": "Caso de uso MapaR",
            "description": "El visitante escoge un destino urbano y recibe un recorrido con huellas, vehículos, marcadores e instrucciones.",
            "nodes": [
                ("u", "Usuario", "actor"), ("m", "MapaR", "usecase"),
                ("d", "Seleccionar destino", "usecase"), ("r", "Animar recorrido", "usecase"),
                ("p", "Mostrar puntos de interés", "usecase"), ("a", "Reproducir audio", "usecase"),
            ],
            "edges": [("u", "d", "inicia"), ("d", "m", "usa"), ("m", "r", "incluye"), ("m", "p", "incluye"), ("m", "a", "opcional")],
        },
        {
            "kind": "Casos de uso",
            "slug": "03-casos-uso-mapaconf",
            "title": "Caso de uso MapaConf",
            "description": "El administrador configura las rutas del terminal mediante una interfaz gráfica y las publica para el visor.",
            "nodes": [
                ("a", "Administrador", "actor"), ("e", "Editor MapaConf", "usecase"),
                ("r", "Crear o editar ruta", "usecase"), ("n", "Editar nodos", "usecase"),
                ("t", "Editar texto y audio", "usecase"), ("g", "Guardar configuración", "usecase"),
            ],
            "edges": [("a", "e", "usa"), ("e", "r", "incluye"), ("e", "n", "incluye"), ("e", "t", "incluye"), ("e", "g", "incluye")],
        },
        {
            "kind": "Casos de uso",
            "slug": "04-casos-uso-maparconf",
            "title": "Caso de uso MapaRConf",
            "description": "El administrador configura el mapa urbano, cambia el fondo y coloca iconos o decoraciones reutilizables.",
            "nodes": [
                ("a", "Administrador", "actor"), ("e", "Editor MapaRConf", "usecase"),
                ("m", "Cambiar mapa de fondo", "usecase"), ("i", "Colocar iconos", "usecase"),
                ("d", "Colocar decoraciones", "usecase"), ("x", "Espejar o rotar assets", "usecase"),
                ("g", "Guardar configuración", "usecase"),
            ],
            "edges": [("a", "e", "usa"), ("e", "m", "incluye"), ("e", "i", "incluye"), ("e", "d", "incluye"), ("e", "x", "incluye"), ("e", "g", "incluye")],
        },
        {
            "kind": "Componentes",
            "slug": "05-componentes",
            "title": "Diagrama de componentes",
            "description": "Vista de los módulos principales del sistema y sus dependencias entre frontend, backend, persistencia y assets.",
            "nodes": [
                ("m", "Mapa", "component"), ("mr", "MapaR", "component"), ("mc", "MapaConf", "component"),
                ("mrc", "MapaRConf", "component"), ("js", "Módulos JavaScript compartidos", "component"),
                ("api", "API Flask", "component"), ("json", "routes-config.json", "object"),
                ("up", "Uploads y catálogo de assets", "object"), ("dock", "Docker", "component"),
            ],
            "edges": [("m", "js", "usa"), ("mr", "js", "usa"), ("mc", "js", "usa"), ("mrc", "js", "usa"), ("js", "api", "HTTP JSON"), ("api", "json", "lee/escribe"), ("api", "up", "sirve/guarda"), ("dock", "api", "ejecuta")],
        },
        {
            "kind": "Clases",
            "slug": "06-clases",
            "title": "Diagrama de clases",
            "description": "Modelo conceptual de la configuración compartida, las rutas, los nodos y los assets usados por los editores y visores.",
            "nodes": [
                ("mc", "MapConfig", "class"), ("r", "Route", "class"), ("n", "Node", "class"),
                ("m", "Marker", "class"), ("d", "Decoration", "class"), ("a", "Asset", "class"),
                ("s", "SegmentOption", "class"), ("repo", "ConfigRepository", "class"), ("up", "UploadService", "class"),
            ],
            "edges": [("mc", "r", "contiene"), ("mc", "m", "contiene"), ("mc", "d", "contiene"), ("r", "n", "contiene"), ("r", "s", "usa"), ("r", "a", "selecciona"), ("m", "a", "usa"), ("d", "a", "usa"), ("repo", "mc", "persiste"), ("up", "a", "crea")],
        },
        {
            "kind": "Secuencias",
            "slug": "07-secuencia-mapa-ruta",
            "title": "Secuencia Mapa seleccionar ruta",
            "description": "Flujo de selección de una dependencia en el visor del terminal.",
            "nodes": [("u", "Usuario", "actor"), ("v", "Mapa", "component"), ("rv", "RouteViewer", "component"), ("api", "API Flask", "component"), ("cfg", "Config JSON", "object")],
            "edges": [("u", "v", "pulsa dependencia"), ("v", "rv", "selectRoute(id)"), ("rv", "cfg", "usa ruta cargada"), ("rv", "v", "renderiza nodos y assets"), ("rv", "u", "muestra instrucciones y audio")],
        },
        {
            "kind": "Secuencias",
            "slug": "08-secuencia-mapar-destino",
            "title": "Secuencia MapaR seleccionar destino",
            "description": "Flujo de selección de un destino urbano y animación del recorrido.",
            "nodes": [("u", "Usuario", "actor"), ("v", "MapaR", "component"), ("rv", "RouteViewer", "component"), ("svg", "Capa SVG", "component"), ("aud", "Audio", "object")],
            "edges": [("u", "v", "pulsa destino"), ("v", "rv", "selectRoute(id)"), ("rv", "svg", "renderFootprints()"), ("rv", "aud", "play()"), ("rv", "u", "muestra ruta e instrucciones")],
        },
        {
            "kind": "Secuencias",
            "slug": "09-secuencia-mapaconf-ruta",
            "title": "Secuencia MapaConf editar ruta",
            "description": "Flujo de creación, edición y guardado de una ruta del terminal.",
            "nodes": [("a", "Administrador", "actor"), ("e", "Editor", "component"), ("svg", "Mapa SVG", "component"), ("api", "API Flask", "component"), ("cfg", "Config JSON", "object")],
            "edges": [("a", "e", "pulsa Nueva"), ("e", "svg", "agrega/mueve nodos"), ("a", "e", "edita texto y asset"), ("e", "api", "PUT /api/config"), ("api", "cfg", "guarda atómicamente"), ("api", "e", "ok")],
        },
        {
            "kind": "Secuencias",
            "slug": "10-secuencia-maparconf-assets",
            "title": "Secuencia MapaRConf administrar assets",
            "description": "Flujo para cambiar el mapa, subir una decoración y guardarla en la configuración.",
            "nodes": [("a", "Administrador", "actor"), ("e", "Editor MapaRConf", "component"), ("up", "Upload API", "component"), ("fs", "Uploads", "object"), ("cfg", "Config JSON", "object")],
            "edges": [("a", "e", "elige mapa/decoración"), ("e", "up", "POST multipart"), ("up", "fs", "guarda archivo"), ("up", "e", "devuelve src"), ("e", "cfg", "añade asset y posición"), ("e", "cfg", "PUT configuración")],
        },
        {
            "kind": "Estados",
            "slug": "11-estados-ruta",
            "title": "Estados de una ruta",
            "description": "Ciclo de vida de una ruta desde su creación hasta su archivo.",
            "nodes": [("c", "Creada", "state"), ("v", "Visible", "state"), ("s", "Seleccionada", "state"), ("p", "En reproducción", "state"), ("f", "Finalizada", "state"), ("a", "Archivada", "state")],
            "edges": [("c", "v", "guardar"), ("v", "s", "pulsar botón"), ("s", "p", "mostrar recorrido"), ("p", "f", "tiempo agotado"), ("f", "v", "reiniciar"), ("v", "a", "archivar"), ("a", "v", "desarchivar")],
        },
        {
            "kind": "Estados",
            "slug": "12-estados-editor",
            "title": "Estados del editor",
            "description": "Estados de interacción del editor gráfico y de persistencia de cambios.",
            "nodes": [("q", "Consulta", "state"), ("e", "Editando", "state"), ("t", "Herramienta activa", "state"), ("d", "Cambios pendientes", "state"), ("g", "Guardando", "state"), ("ok", "Guardado", "state")],
            "edges": [("q", "e", "seleccionar elemento"), ("e", "t", "elegir nodos/iconos"), ("t", "d", "modificar"), ("d", "g", "Guardar"), ("g", "ok", "respuesta 200"), ("ok", "e", "seguir editando")],
        },
        {
            "kind": "Estados",
            "slug": "13-estados-recorrido",
            "title": "Estados del recorrido",
            "description": "Estados visuales del recorrido en el mapa durante su aparición y desaparición.",
            "nodes": [("i", "Inicial", "state"), ("a", "Animando entrada", "state"), ("s", "Visible", "state"), ("o", "Animando salida", "state"), ("r", "Reiniciado", "state")],
            "edges": [("i", "a", "seleccionar ruta"), ("a", "s", "terminar entrada"), ("s", "o", "temporizador"), ("o", "r", "terminar salida"), ("r", "i", "mostrar panel inicial")],
        },
        {
            "kind": "Actividades",
            "slug": "14-actividad-mapa",
            "title": "Actividad consultar ruta en Mapa",
            "description": "Proceso completo para consultar una ruta de oficinas del terminal.",
            "nodes": [("i", "Inicio", "activity"), ("s", "Seleccionar oficina", "activity"), ("c", "Cargar datos de ruta", "activity"), ("r", "Dibujar recorrido", "activity"), ("t", "Mostrar pasos", "activity"), ("a", "Reproducir audio", "activity"), ("f", "Fin", "activity")],
            "edges": [("i", "s", ""), ("s", "c", ""), ("c", "r", ""), ("r", "t", ""), ("t", "a", ""), ("a", "f", "")],
        },
        {
            "kind": "Actividades",
            "slug": "15-actividad-mapar",
            "title": "Actividad consultar destino en MapaR",
            "description": "Proceso de consulta de un destino urbano en el mapa de Retalhuleu.",
            "nodes": [("i", "Inicio", "activity"), ("s", "Seleccionar destino", "activity"), ("m", "Leer nodos y assets", "activity"), ("r", "Animar recorrido", "activity"), ("p", "Mostrar marcadores", "activity"), ("f", "Fin", "activity")],
            "edges": [("i", "s", ""), ("s", "m", ""), ("m", "r", ""), ("r", "p", ""), ("p", "f", "")],
        },
        {
            "kind": "Actividades",
            "slug": "16-actividad-editor-ruta",
            "title": "Actividad crear y guardar ruta",
            "description": "Proceso de configuración de una nueva ruta desde el editor gráfico.",
            "nodes": [("i", "Inicio", "activity"), ("n", "Crear ruta", "activity"), ("p", "Agregar nodos", "activity"), ("x", "Elegir assets", "activity"), ("t", "Escribir indicaciones", "activity"), ("v", "Validar datos", "activity"), ("g", "Guardar", "activity"), ("f", "Fin", "activity")],
            "edges": [("i", "n", ""), ("n", "p", ""), ("p", "x", ""), ("x", "t", ""), ("t", "v", ""), ("v", "g", ""), ("g", "f", "")],
        },
        {
            "kind": "Actividades",
            "slug": "17-actividad-assets",
            "title": "Actividad administrar mapas y decoraciones",
            "description": "Proceso para subir, seleccionar, transformar y guardar assets reutilizables.",
            "nodes": [("i", "Inicio", "activity"), ("u", "Subir archivo", "activity"), ("c", "Clasificar asset", "activity"), ("p", "Colocar en mapa", "activity"), ("t", "Rotar o espejar", "activity"), ("g", "Guardar configuración", "activity"), ("f", "Fin", "activity")],
            "edges": [("i", "u", ""), ("u", "c", ""), ("c", "p", ""), ("p", "t", ""), ("t", "g", ""), ("g", "f", "")],
        },
        {
            "kind": "Colaboración",
            "slug": "18-colaboracion-mapa",
            "title": "Colaboración Mapa seleccionar ruta",
            "description": "Objetos que colaboran para responder a la selección de una ruta en el terminal.",
            "nodes": [("u", "Usuario", "actor"), ("b", "Botón de ruta", "object"), ("v", "RouteViewer", "component"), ("svg", "SVG del mapa", "component"), ("p", "Panel lateral", "object"), ("au", "Audio", "object")],
            "edges": [("u", "b", "1: pulsa"), ("b", "v", "2: selectRoute"), ("v", "svg", "3: renderFootprints"), ("v", "p", "4: showRoutePanel"), ("v", "au", "5: playRouteAudio")],
        },
        {
            "kind": "Colaboración",
            "slug": "19-colaboracion-editor",
            "title": "Colaboración Editor modificar ruta",
            "description": "Objetos que colaboran para editar una ruta, sus nodos y sus assets.",
            "nodes": [("a", "Administrador", "actor"), ("e", "RouteEditor", "component"), ("n", "NodeLayer", "component"), ("f", "Formularios", "object"), ("m", "MapConfig", "object"), ("s", "Save API", "component")],
            "edges": [("a", "f", "1: edita"), ("f", "e", "2: input/change"), ("e", "n", "3: renderNodes"), ("e", "m", "4: actualiza modelo"), ("e", "s", "5: PUT config")],
        },
        {
            "kind": "Colaboración",
            "slug": "20-colaboracion-assets",
            "title": "Colaboración MapaRConf assets",
            "description": "Objetos que colaboran para subir y colocar un mapa o decoración en MapaRConf.",
            "nodes": [("a", "Administrador", "actor"), ("e", "Editor", "component"), ("u", "Upload API", "component"), ("fs", "Uploads", "object"), ("c", "Catalog", "object"), ("svg", "MapLayer", "component")],
            "edges": [("a", "e", "1: selecciona archivo"), ("e", "u", "2: uploadFile"), ("u", "fs", "3: guarda"), ("u", "e", "4: devuelve src"), ("e", "c", "5: registra asset"), ("e", "svg", "6: renderiza posición")],
        },
    ]


def positions(nodes, kind="", width=1800, height=1000):
    count = len(nodes)
    out = {}
    if kind in {"Secuencias", "Actividades", "Estados"}:
        usable = width - 240
        step = usable / max(1, count - 1)
        y = 300 if kind == "Secuencias" else 360
        for i, (node_id, label, node_kind) in enumerate(nodes):
            out[node_id] = (120 + i * step, y)
        return out

    if kind == "Casos de uso":
        for i, (node_id, label, node_kind) in enumerate(nodes):
            if i == 0:
                out[node_id] = (150, 430)
            elif i == 1:
                out[node_id] = (520, 430)
            else:
                col = (i - 2) % 2
                row = (i - 2) // 2
                out[node_id] = (1020 + col * 430, 270 + row * 250)
        return out

    cols = 3
    cell_w = (width - 300) / cols
    cell_h = (height - 260) / max(1, math.ceil(count / cols))
    for i, (node_id, label, node_kind) in enumerate(nodes):
        col = i % cols
        row = i // cols
        out[node_id] = (180 + col * cell_w, 220 + row * cell_h)
    return out


def boundary_point(box, target):
    x1, y1, x2, y2 = box
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2
    dx = target[0] - cx
    dy = target[1] - cy
    if dx == 0 and dy == 0:
        return cx, cy
    scale = min((x2 - x1) / 2 / abs(dx) if dx else float("inf"), (y2 - y1) / 2 / abs(dy) if dy else float("inf"))
    return cx + dx * scale, cy + dy * scale


def draw_arrow(draw, start, end, color):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=3)
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 13
    left = (x2 - size * math.cos(angle - math.pi / 6), y2 - size * math.sin(angle - math.pi / 6))
    right = (x2 - size * math.cos(angle + math.pi / 6), y2 - size * math.sin(angle + math.pi / 6))
    draw.polygon([(x2, y2), left, right], fill=color)


def render(spec):
    image = Image.new("RGB", (1800, 1000), COLORS["background"])
    draw = ImageDraw.Draw(image)
    draw.text((50, 32), spec["title"], font=FONT_TITLE, fill=COLORS["ink"])
    draw.text((52, 88), spec["kind"], font=FONT_SUBTITLE, fill=(20, 122, 105))
    pos = positions(spec["nodes"], spec["kind"])
    node_map = {node_id: (label, kind) for node_id, label, kind in spec["nodes"]}
    boxes = {}
    for node_id, label, kind in spec["nodes"]:
        x, y = pos[node_id]
        w, h = (255, 92) if kind != "class" else (280, 118)
        boxes[node_id] = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
    for edge_index, (source, target, label) in enumerate(spec["edges"], 1):
        sx1, sy1, sx2, sy2 = boxes[source]
        tx1, ty1, tx2, ty2 = boxes[target]
        target_center = ((tx1 + tx2) / 2, (ty1 + ty2) / 2)
        source_center = ((sx1 + sx2) / 2, (sy1 + sy2) / 2)
        start = boundary_point((sx1, sy1, sx2, sy2), target_center)
        end = boundary_point((tx1, ty1, tx2, ty2), source_center)
        draw_arrow(draw, start, end, COLORS["edge"])
        if label:
            if spec["kind"] == "Secuencias":
                label = str(edge_index)
            lx = (start[0] + end[0]) / 2
            ly = (start[1] + end[1]) / 2 - 12
            bbox = draw.textbbox((0, 0), label, font=FONT_SMALL)
            pad = 5
            draw.rounded_rectangle((lx + bbox[0] - pad, ly + bbox[1] - pad, lx + bbox[2] + pad, ly + bbox[3] + pad), radius=5, fill=COLORS["background"])
            draw.text((lx, ly), label, font=FONT_SMALL, fill=COLORS["edge"], anchor="mm")
    for node_id, label, kind in spec["nodes"]:
        x1, y1, x2, y2 = boxes[node_id]
        fill = COLORS.get(kind, COLORS["object"])
        if kind in {"actor", "usecase"}:
            draw.ellipse((x1, y1, x2, y2), fill=fill, outline=COLORS["ink"], width=3)
        else:
            draw.rounded_rectangle((x1, y1, x2, y2), radius=14, fill=fill, outline=COLORS["ink"], width=3)
        draw.multiline_text(((x1 + x2) / 2, (y1 + y2) / 2), wrap(label, 21), font=FONT_NODE, fill=COLORS["ink"], anchor="mm", align="center", spacing=4)
    return image


def mx_cell(cell_id, value, style, x, y, w=220, h=80):
    return f'<mxCell id="{cell_id}" value="{html.escape(value)}" style="{style}" vertex="1" parent="1"><mxGeometry x="{int(x)}" y="{int(y)}" width="{w}" height="{h}" as="geometry"/></mxCell>'


def drawio_page(spec, index):
    pos = positions(spec["nodes"], spec["kind"])
    node_map = {node_id: (label, kind) for node_id, label, kind in spec["nodes"]}
    cells = [mx_cell(f"title-{index}", spec["title"], "text;html=1;strokeColor=none;fillColor=none;fontSize=24;fontStyle=1;fontColor=#171A4A;", 40, 20, 650, 45)]
    for node_id, label, kind in spec["nodes"]:
        x, y = pos[node_id]
        style = {"actor": "ellipse;whiteSpace=wrap;html=1;fillColor=#EEE1BC;strokeColor=#171A4A;fontStyle=1;", "usecase": "ellipse;whiteSpace=wrap;html=1;fillColor=#CDE8E0;strokeColor=#171A4A;fontStyle=1;", "component": "rounded=1;whiteSpace=wrap;html=1;fillColor=#CCDDF0;strokeColor=#171A4A;fontStyle=1;", "class": "swimlane;whiteSpace=wrap;html=1;fillColor=#E0D7F0;strokeColor=#171A4A;fontStyle=1;", "state": "rounded=1;whiteSpace=wrap;html=1;fillColor=#FADCC5;strokeColor=#171A4A;fontStyle=1;", "activity": "rounded=1;whiteSpace=wrap;html=1;fillColor=#DDEBCB;strokeColor=#171A4A;fontStyle=1;", "object": "rounded=1;whiteSpace=wrap;html=1;fillColor=#E6E6E6;strokeColor=#171A4A;fontStyle=1;"}.get(kind, "rounded=1;whiteSpace=wrap;html=1;fillColor=#E6E6E6;strokeColor=#171A4A;")
        cells.append(mx_cell(f"node-{index}-{node_id}", label, style, x - 125, y - 45, 250, 90))
    for edge_index, (source, target, label) in enumerate(spec["edges"]):
        edge_value = str(edge_index + 1) if spec["kind"] == "Secuencias" and label else label
        cells.append(f'<mxCell id="edge-{index}-{edge_index}" value="{html.escape(edge_value)}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;endArrow=block;labelBackgroundColor=#F8F7F3;" edge="1" parent="1" source="node-{index}-{source}" target="node-{index}-{target}"><mxGeometry relative="1" as="geometry"/></mxCell>')
    return "".join(cells)


def write_drawio(all_specs):
    pages = []
    for index, spec in enumerate(all_specs, 1):
        pages.append(f'<diagram id="page-{index}-{uuid.uuid4().hex[:8]}" name="{html.escape(spec["title"])}"><mxGraphModel dx="1800" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1800" pageHeight="1000"><root><mxCell id="0"/><mxCell id="1" parent="0"/>{drawio_page(spec, index)}</root></mxGraphModel></diagram>')
    content = '<mxfile host="app.diagrams.net" modified="2026-09-07T00:00:00.000Z" agent="Codex" version="24.7.17">' + "".join(pages) + "</mxfile>"
    (OUT / "diagramas-sistema.drawio").write_text(content, encoding="utf-8")


def write_docx(all_specs):
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.65)
    section.bottom_margin = Inches(0.65)
    section.left_margin = Inches(0.7)
    section.right_margin = Inches(0.7)
    styles = doc.styles
    styles["Normal"].font.name = "Arial"
    styles["Normal"].font.size = Pt(10)
    styles["Title"].font.name = "Arial"
    styles["Title"].font.color.rgb = RGBColor(0, 0, 0)
    styles["Heading 1"].font.name = "Arial"
    styles["Heading 1"].font.color.rgb = RGBColor(0, 0, 0)
    styles["Heading 2"].font.name = "Arial"
    styles["Heading 2"].font.color.rgb = RGBColor(0, 0, 0)

    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Diagramas UML del Sistema de Mapas")
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub.add_run("Mapa, MapaR, MapaConf y MapaRConf").bold = True
    doc.add_paragraph("Este documento presenta los diagramas UML derivados de las funcionalidades actuales de la aplicación: visualización de rutas, edición gráfica, gestión de mapas, assets, iconos, decoraciones, audio y persistencia mediante API Flask.")
    doc.add_paragraph("El archivo diagramas-sistema.drawio contiene las mismas páginas en formato editable.")
    doc.add_page_break()

    current_kind = None
    for index, spec in enumerate(all_specs, 1):
        if spec["kind"] != current_kind:
            current_kind = spec["kind"]
            doc.add_heading(spec["kind"], level=1)
        doc.add_heading(f"{index}. {spec['title']}", level=2)
        doc.add_paragraph(spec["description"])
        image_path = IMG_DIR / f"{spec['slug']}.png"
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(image_path), width=Inches(6.75))
        cap = doc.add_paragraph()
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = cap.add_run(f"Figura {index}. {spec['title']}")
        run.italic = True
        if index != len(all_specs):
            doc.add_page_break()
    doc.save(OUT / "diagramas-sistema.docx")


def main():
    all_specs = specs()
    for spec in all_specs:
        render(spec).save(IMG_DIR / f"{spec['slug']}.png")
    write_drawio(all_specs)
    write_docx(all_specs)
    print(f"Generados {len(all_specs)} diagramas en {OUT}")


if __name__ == "__main__":
    main()
