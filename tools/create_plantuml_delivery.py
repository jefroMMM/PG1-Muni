from __future__ import annotations

import re
import shutil
import urllib.request
import zlib
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion"
SOURCE_DIR = OUT / "plantuml"
IMAGE_DIR = OUT / "plantuml-imagenes"
DOCX_PATH = OUT / "diagramas-uml-con-codigo.docx"
LEGACY_IMAGE_SLUGS = [
    "01-casos-uso-mapa", "02-casos-uso-mapar", "03-casos-uso-mapaconf", "04-casos-uso-maparconf",
    "05-componentes", "06-clases", "07-secuencia-mapa-ruta", "08-secuencia-mapar-destino",
    "09-secuencia-mapaconf-ruta", "10-secuencia-maparconf-assets", "11-estados-ruta", "12-estados-editor",
    "13-estados-recorrido", "14-actividad-mapa", "15-actividad-mapar", "16-actividad-editor-ruta",
    "17-actividad-assets", "18-colaboracion-mapa", "19-colaboracion-editor", "20-colaboracion-assets",
]

STYLE = """!theme plain
skinparam backgroundColor #F8F7F3
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontColor #14213D
skinparam ArrowColor #415A77
skinparam BorderColor #14213D
skinparam packageBorderColor #14213D
skinparam packageBackgroundColor #FFFFFF
skinparam usecaseBackgroundColor #DDEFD9
skinparam usecaseBorderColor #14213D
skinparam componentBackgroundColor #D7E8F7
skinparam classBackgroundColor #E7DCF3
skinparam stateBackgroundColor #FBE2CF
skinparam activityBackgroundColor #DDEFD9
skinparam objectBackgroundColor #F0F2F4
skinparam sequenceParticipantBackgroundColor #D7E8F7
skinparam sequenceLifeLineBorderColor #415A77
skinparam sequenceArrowColor #415A77
skinparam roundcorner 12
"""


def uml(title: str, body: str) -> str:
    return f"@startuml\ntitle {title}\n{STYLE}\n{body.strip()}\n@enduml\n"


def diagrams():
    return [
        ("01-caso-uso-mapa", "Casos de uso", "Caso de uso Mapa", "Muestra cómo un visitante consulta una dependencia del terminal: selecciona la oficina, observa el recorrido, lee las indicaciones y puede escuchar el audio asociado.", uml("Caso de uso Mapa", """left to right direction
actor Usuario
rectangle \"Mapa del terminal\" {
  usecase \"Seleccionar\ndependencia\" as UC1
  usecase \"Mostrar ruta\" as UC2
  usecase \"Mostrar\nindicaciones\" as UC3
  usecase \"Reproducir audio\" as UC4
}
Usuario --> UC1
UC1 .> UC2 : <<include>>
UC2 .> UC3 : <<include>>
UC2 .> UC4 : <<extend>>""")),
        ("02-caso-uso-mapar", "Casos de uso", "Caso de uso MapaR", "Describe la consulta de un destino urbano. El usuario escoge un destino y el sistema anima el recorrido, presenta puntos de interés, instrucciones y audio.", uml("Caso de uso MapaR", """left to right direction
actor Usuario
rectangle \"Mapa urbano de Retalhuleu\" {
  usecase \"Seleccionar destino\" as UC1
  usecase \"Animar recorrido\" as UC2
  usecase \"Mostrar puntos\nde interés\" as UC3
  usecase \"Mostrar\nindicaciones\" as UC4
  usecase \"Reproducir audio\" as UC5
}
Usuario --> UC1
UC1 .> UC2 : <<include>>
UC2 .> UC3 : <<include>>
UC2 .> UC4 : <<include>>
UC4 .> UC5 : <<extend>>""")),
        ("03-caso-uso-mapaconf", "Casos de uso", "Caso de uso MapaConf", "Representa las tareas del administrador en el editor del terminal: administrar rutas, definir nodos, elegir assets, editar indicaciones y publicar cambios.", uml("Caso de uso MapaConf", """left to right direction
actor Administrador
rectangle \"Editor MapaConf\" {
  usecase \"Crear, duplicar o\narchivar ruta\" as UC1
  usecase \"Agregar, mover o\nborrar nodos\" as UC2
  usecase \"Elegir asset\npor tramo\" as UC3
  usecase \"Editar texto\ny audio\" as UC4
  usecase \"Guardar\nconfiguración\" as UC5
}
Administrador --> UC1
Administrador --> UC2
Administrador --> UC4
UC1 .> UC3 : <<include>>
UC1 .> UC5 : <<include>>""")),
        ("04-caso-uso-maparconf", "Casos de uso", "Caso de uso MapaRConf", "Representa la administración del mapa urbano: rutas, fondo, iconos, decoraciones, transformaciones visuales y persistencia de cambios.", uml("Caso de uso MapaRConf", """left to right direction
actor Administrador
rectangle \"Editor MapaRConf\" {
  usecase \"Crear o editar\nruta urbana\" as UC1
  usecase \"Cambiar mapa\nde fondo\" as UC2
  usecase \"Colocar iconos\" as UC3
  usecase \"Colocar\ndecoraciones\" as UC4
  usecase \"Rotar, espejar y\ncambiar tamaño\" as UC5
  usecase \"Guardar\nconfiguración\" as UC6
}
Administrador --> UC1
Administrador --> UC2
Administrador --> UC3
Administrador --> UC4
UC3 .> UC5 : <<include>>
UC4 .> UC5 : <<include>>
UC1 .> UC6 : <<include>>""")),
        ("05-componentes", "Componentes", "Diagrama de componentes", "Muestra la arquitectura: cuatro pantallas frontend consumen módulos compartidos y una API Flask, que persiste configuración y sirve los archivos subidos.", uml("Diagrama de componentes", """package \"Frontend\" {
  [Mapa] as mapa
  [MapaR] as mapar
  [MapaConf] as conf
  [MapaRConf] as maparconf
  [Módulos compartidos\nconfig api map utils route viewer] as shared
}
component \"API Flask\" as api
database \"routes config json\" as config
folder \"Uploads\nmapas iconos audios\nassets decoraciones\" as uploads
node Docker as docker
mapa --> shared
mapar --> shared
conf --> shared
maparconf --> shared
shared --> api : HTTP JSON
api --> config : lee y guarda
api --> uploads : sirve y sube
docker --> api : ejecuta""")),
        ("06-clases", "Clases", "Diagrama de clases", "Modela la estructura de datos compartida. Un mapa contiene rutas, marcadores y decoraciones; una ruta tiene nodos, assets por tramo y opciones de rotación o espejo.", uml("Diagrama de clases", """class MapConfig {
  +title: string
  +background: string
  +viewBox: string
}
class Route {
  +id: string
  +name: string
  +archived: boolean
  +instructions: string
  +audio: string
}
class Node { +x: number\n+x: number }
class Marker { +assetId: string\n+x: number\n+y: number\n+rotation: number\n+mirrored: boolean }
class Decoration { +assetId: string\n+x: number\n+y: number\n+width: number\n+rotation: number }
class Asset { +id: string\n+name: string\n+src: string }
class SegmentOption { +rotation: number\n+mirrored: boolean }
class ConfigRepository { +load()\n+save() }
class UploadService { +upload(file, kind) }
MapConfig \"1\" *-- \"0..*\" Route
MapConfig \"1\" *-- \"0..*\" Marker
MapConfig \"1\" *-- \"0..*\" Decoration
Route \"1\" *-- \"2..*\" Node
Route \"1\" *-- \"0..*\" SegmentOption
Route ..> Asset : usa
Marker ..> Asset : usa
Decoration ..> Asset : usa
ConfigRepository --> MapConfig : persiste
UploadService --> Asset : crea""")),
        ("07-secuencia-mapa", "Secuencias", "Secuencia Mapa seleccionar ruta", "Explica el intercambio de mensajes cuando el visitante selecciona una dependencia del terminal y se dibuja el recorrido.", uml("Secuencia Mapa seleccionar ruta", """actor Usuario
participant Mapa
participant RouteViewer
database \"Config JSON\" as Config
participant Audio
Usuario -> Mapa : 1. pulsa dependencia
Mapa -> RouteViewer : 2. selectRoute(id)
RouteViewer -> Config : 3. obtiene ruta activa
Config --> RouteViewer : nodos assets instrucciones
RouteViewer -> Mapa : 4. renderiza recorrido SVG
RouteViewer -> Audio : 5. reproduce audio opcional
RouteViewer --> Usuario : 6. muestra pasos""")),
        ("08-secuencia-mapar", "Secuencias", "Secuencia MapaR seleccionar destino", "Describe cómo MapaR procesa la selección de un destino, anima los assets y muestra indicaciones para el recorrido urbano.", uml("Secuencia MapaR seleccionar destino", """actor Usuario
participant MapaR
participant RouteViewer
participant \"Capa SVG\" as SVG
participant Audio
Usuario -> MapaR : 1. pulsa destino
MapaR -> RouteViewer : 2. selectRoute(id)
RouteViewer -> SVG : 3. renderFootprints()
RouteViewer -> SVG : 4. renderMarkers()
RouteViewer -> Audio : 5. play()
RouteViewer --> Usuario : 6. muestra indicaciones""")),
        ("09-secuencia-mapaconf", "Secuencias", "Secuencia MapaConf editar ruta", "Muestra el ciclo de edición de una ruta del terminal desde la modificación visual hasta el guardado atómico de la configuración.", uml("Secuencia MapaConf editar ruta", """actor Administrador
participant RouteEditor
participant \"Mapa SVG\" as SVG
participant \"API Flask\" as API
database \"routes config json\" as Config
Administrador -> RouteEditor : 1. crea o selecciona ruta
Administrador -> RouteEditor : 2. modifica nodos assets texto
RouteEditor -> SVG : 3. actualiza vista previa
Administrador -> RouteEditor : 4. pulsa Guardar
RouteEditor -> API : 5. PUT api config
API -> Config : 6. guarda archivo temporal
API -> Config : 7. reemplaza config atómicamente
API --> RouteEditor : 8. confirmación""")),
        ("10-secuencia-maparconf", "Secuencias", "Secuencia MapaRConf administrar assets", "Explica la subida de un asset o mapa, su registro en el catálogo y la persistencia de su posición dentro del mapa urbano.", uml("Secuencia MapaRConf administrar assets", """actor Administrador
participant RouteEditor
participant \"Upload API\" as API
folder Uploads
database \"Config JSON\" as Config
Administrador -> RouteEditor : 1. selecciona archivo
RouteEditor -> API : 2. POST api upload
API -> Uploads : 3. guarda archivo clasificado
API --> RouteEditor : 4. devuelve src y nombre
Administrador -> RouteEditor : 5. coloca y transforma asset
RouteEditor -> Config : 6. agrega asset y posición
RouteEditor -> API : 7. guarda configuración""")),
        ("11-estados-ruta", "Estados", "Estados de una ruta", "Explica el ciclo de vida de una ruta desde que se crea hasta que se archiva o vuelve a quedar visible.", uml("Estados de una ruta", """[*] --> Creada
Creada --> Visible : guardar
Visible --> Seleccionada : usuario pulsa botón
Seleccionada --> MostrandoRecorrido : renderizar
MostrandoRecorrido --> Visible : temporizador termina
Visible --> Archivada : archivar
Archivada --> Visible : desarchivar
Visible --> [*] : eliminar""")),
        ("12-estados-editor", "Estados", "Estados del editor", "Muestra los estados de trabajo del editor: selección, edición, cambios pendientes, guardado correcto o error de persistencia.", uml("Estados del editor", """[*] --> Consulta
Consulta --> Edicion : seleccionar ruta
Edicion --> HerramientaActiva : nodos iconos assets
HerramientaActiva --> CambiosPendientes : modificar
CambiosPendientes --> Guardando : Guardar
Guardando --> Guardado : respuesta 200
Guardando --> Error : error API
Error --> CambiosPendientes : corregir
Guardado --> Edicion : continuar""")),
        ("13-estados-recorrido", "Estados", "Estados del recorrido", "Muestra el comportamiento visual del recorrido desde el panel inicial hasta la animación de salida y el reinicio.", uml("Estados del recorrido", """[*] --> PanelInicial
PanelInicial --> Entrada : seleccionar ruta
Entrada --> RutaVisible : animación completa
RutaVisible --> Salida : routeVisibleTime
Salida --> PanelInicial : animación completa
RutaVisible --> Entrada : seleccionar otra ruta""")),
        ("14-actividad-mapa", "Actividades", "Actividad consultar ruta en Mapa", "Describe el flujo operativo del visor del terminal cuando un visitante consulta una oficina.", uml("Actividad consultar ruta en Mapa", """start
:Seleccionar oficina;
:Cargar nodos y assets;
:Dibujar recorrido;
:Mostrar pasos;
if (La ruta tiene audio) then (sí)
  :Reproducir audio;
endif
:Esperar temporizador;
:Ocultar recorrido;
stop""")),
        ("15-actividad-mapar", "Actividades", "Actividad consultar destino en MapaR", "Describe la consulta de un destino urbano y la composición del recorrido con marcadores, assets e instrucciones.", uml("Actividad consultar destino en MapaR", """start
:Seleccionar destino;
:Leer nodos y segment assets;
:Renderizar huellas o vehículo;
:Mostrar iconos y decoraciones;
:Mostrar indicaciones;
if (Hay audio) then (sí)
  :Reproducir audio;
endif
:Restablecer mapa;
stop""")),
        ("16-actividad-crear-ruta", "Actividades", "Actividad crear y guardar ruta", "Muestra el proceso que sigue el administrador para publicar una ruta nueva desde cualquiera de los dos editores.", uml("Actividad crear y guardar ruta", """start
:Crear ruta;
:Definir nombre y color;
:Agregar nodos;
:Elegir assets por tramo;
:Escribir indicaciones;
if (Desea audio) then (sí)
  :Subir o seleccionar audio;
endif
:Guardar configuración;
:Ruta visible en el visor;
stop""")),
        ("17-actividad-assets", "Actividades", "Actividad administrar mapas e iconos", "Muestra cómo el administrador sube o selecciona un mapa, icono o decoración, aplica transformaciones y guarda el resultado.", uml("Actividad administrar mapas e iconos", """start
:Elegir modo mapa iconos o decoraciones;
:Seleccionar o subir archivo;
:Clasificar asset;
:Colocar sobre el mapa;
:Mover y cambiar tamaño;
:Rotar o espejar;
:Guardar configuración;
stop""")),
        ("18-colaboracion-mapa", "Colaboración", "Colaboración Mapa seleccionar ruta", "Muestra los objetos que cooperan durante la selección de una ruta normal, incluyendo interfaz, visor, SVG, panel y audio.", uml("Colaboración Mapa seleccionar ruta", """object Usuario
object \"Botón de ruta\" as Boton
object RouteViewer
object \"Capa SVG\" as SVG
object \"Panel lateral\" as Panel
object Audio
Usuario --> Boton : 1 pulsa
Boton --> RouteViewer : 2 selectRoute
RouteViewer --> SVG : 3 renderFootprints
RouteViewer --> Panel : 4 showRoutePanel
RouteViewer --> Audio : 5 playRouteAudio""")),
        ("19-colaboracion-editor", "Colaboración", "Colaboración Editor modificar ruta", "Muestra la cooperación entre administrador, formularios, editor, modelo de configuración, mapa SVG y la API de guardado.", uml("Colaboración Editor modificar ruta", """object Administrador
object Formularios
object RouteEditor
object \"Mapa SVG\" as SVG
object MapConfig
object \"Save API\" as API
Administrador --> Formularios : 1 edita
Formularios --> RouteEditor : 2 input change
RouteEditor --> SVG : 3 renderNodes
RouteEditor --> MapConfig : 4 actualiza modelo
RouteEditor --> API : 5 PUT config""")),
        ("20-colaboracion-assets", "Colaboración", "Colaboración MapaRConf assets", "Muestra el intercambio entre editor, API de uploads, catálogo y capa del mapa cuando se sube o coloca un asset.", uml("Colaboración MapaRConf assets", """object Administrador
object Editor
object \"Upload API\" as API
object Uploads
object Catalogo
object \"Map Layer\" as MapLayer
Administrador --> Editor : 1 selecciona archivo
Editor --> API : 2 uploadFile
API --> Uploads : 3 guarda archivo
API --> Editor : 4 devuelve src
Editor --> Catalogo : 5 registra asset
Editor --> MapLayer : 6 renderiza posición""")),
    ]


def encode6bit(value: int) -> str:
    if value < 10:
        return chr(48 + value)
    value -= 10
    if value < 26:
        return chr(65 + value)
    value -= 26
    if value < 26:
        return chr(97 + value)
    value -= 26
    return "-" if value == 0 else "_" if value == 1 else "?"


def plantuml_encode(data: bytes) -> str:
    output = []
    for index in range(0, len(data), 3):
        b1 = data[index]
        b2 = data[index + 1] if index + 1 < len(data) else 0
        b3 = data[index + 2] if index + 2 < len(data) else 0
        c1, c2 = b1 >> 2, ((b1 & 0x3) << 4) | (b2 >> 4)
        c3, c4 = ((b2 & 0xF) << 2) | (b3 >> 6), b3 & 0x3F
        output.extend([encode6bit(c1), encode6bit(c2), encode6bit(c3), encode6bit(c4)])
    return "".join(output)


def download_png(source: str, destination: Path):
    compressed = zlib.compress(source.encode("utf-8"))[2:-4]
    encoded = plantuml_encode(compressed)
    url = f"https://www.plantuml.com/plantuml/png/{encoded}"
    request = urllib.request.Request(url, headers={"User-Agent": "Codex UML generator"})
    with urllib.request.urlopen(request, timeout=40) as response:
        data = response.read()
    if not data.startswith(b"\x89PNG"):
        raise RuntimeError(f"PlantUML no devolvió una imagen para {destination.name}")
    destination.write_bytes(data)


def set_cell_shading(cell, fill: str):
    tc_pr = cell._tc.get_or_add_tcPr()
    shading = OxmlElement("w:shd")
    shading.set(qn("w:fill"), fill)
    tc_pr.append(shading)


def concise_source(source: str) -> str:
    """Keeps the Word code sample valid while omitting repeated visual styling."""
    return source.replace(STYLE, "").strip()


def add_code(cell, source: str):
    cell.text = ""
    set_cell_shading(cell, "F0F2F4")
    title = cell.paragraphs[0]
    title.alignment = WD_ALIGN_PARAGRAPH.LEFT
    title.paragraph_format.space_after = Pt(2)
    title.add_run("Codigo PlantUML").bold = True
    title.runs[0].font.size = Pt(8)
    paragraph = cell.add_paragraph()
    paragraph.alignment = WD_ALIGN_PARAGRAPH.LEFT
    paragraph.paragraph_format.space_after = Pt(0)
    for line in source.strip().splitlines():
        run = paragraph.add_run(line + "\n")
        run.font.name = "Courier New"
        run.font.size = Pt(7)
        run.font.color.rgb = RGBColor(31, 41, 55)


def write_docx(items):
    doc = Document()
    for section in doc.sections:
        section.orientation = WD_ORIENT.LANDSCAPE
        section.page_width, section.page_height = Inches(11), Inches(8.5)
        section.left_margin = section.right_margin = Inches(0.45)
        section.top_margin = section.bottom_margin = Inches(0.4)
    styles = doc.styles
    for name in ("Normal", "Title", "Heading 1", "Heading 2"):
        styles[name].font.name = "Arial"
        styles[name].font.color.rgb = RGBColor(0, 0, 0)
    styles["Normal"].font.size = Pt(9.5)
    title = doc.add_paragraph(style="Title")
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title.add_run("Diagramas UML del Sistema de Mapas")
    cover = doc.add_paragraph()
    cover.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cover.add_run("Mapa  MapaR  MapaConf y MapaRConf").bold = True
    doc.add_paragraph("Cada sección incluye una imagen generada desde PlantUML, la explicación del flujo y el código fuente UML correspondiente. Los archivos individuales se entregan en la carpeta plantuml.")
    doc.add_page_break()
    current_category = None
    for number, (slug, category, title_text, explanation, source) in enumerate(items, 1):
        if category != current_category:
            current_category = category
            doc.add_heading(category, level=1)
        doc.add_heading(f"{number}. {title_text}", level=2)
        doc.add_paragraph(explanation)
        table = doc.add_table(rows=1, cols=2)
        table.autofit = False
        left, right = table.rows[0].cells
        left.width, right.width = Inches(6.05), Inches(3.85)
        left.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        right.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
        image_p = left.paragraphs[0]
        image_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        image_p.add_run().add_picture(str(IMAGE_DIR / f"{slug}.png"), width=Inches(5.85))
        add_code(right, concise_source(source))
        caption = doc.add_paragraph()
        caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
        caption.add_run(f"Figura {number}. {title_text}").italic = True
        if number < len(items):
            doc.add_page_break()
    doc.save(DOCX_PATH)


def main():
    OUT.mkdir(exist_ok=True)
    SOURCE_DIR.mkdir(exist_ok=True)
    IMAGE_DIR.mkdir(exist_ok=True)
    items = diagrams()
    for index, (slug, category, title_text, explanation, source) in enumerate(items):
        (SOURCE_DIR / f"{slug}.puml").write_text(source, encoding="utf-8")
        output_image = IMAGE_DIR / f"{slug}.png"
        local_image = OUT / "imagenes" / f"{LEGACY_IMAGE_SLUGS[index]}.png"
        if not local_image.exists():
            raise FileNotFoundError(f"No se encontró la imagen UML local {local_image.name}")
        shutil.copyfile(local_image, output_image)
    write_docx(items)
    print(f"Generados {len(items)} archivos PlantUML y {DOCX_PATH.name}")


if __name__ == "__main__":
    main()
