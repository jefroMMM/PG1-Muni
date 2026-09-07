from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "documentacion"
SOURCE_DIR = OUT / "plantuml"
MARKDOWN_PATH = OUT / "codigos-uml-diferenciados.md"


def uml(title: str, body: str) -> str:
    return f"@startuml\ntitle {title}\n{body.strip()}\n@enduml\n"


DIAGRAMS = [
    (
        "01-caso-uso-mapa",
        "Caso de uso - Mapa: consulta dentro del terminal",
        uml("Mapa - consulta dentro del terminal", """left to right direction
actor Visitante
rectangle "Pantalla Mapa" {
  usecase "Elegir dependencia" as select
  usecase "Destacar destino" as highlight
  usecase "Trazar recorrido interno" as draw
  usecase "Leer pasos ordenados" as steps
  usecase "Escuchar indicaciones" as audio
}
Visitante --> select
select .> highlight : <<include>>
highlight .> draw : <<include>>
draw .> steps : <<include>>
audio .> steps : <<extend>>
Visitante --> audio"""),
    ),
    (
        "02-caso-uso-mapar",
        "Caso de uso - MapaR: recorrido urbano",
        uml("MapaR - recorrido urbano", """left to right direction
actor Ciudadano
rectangle "Pantalla MapaR" {
  usecase "Escoger destino urbano" as destination
  usecase "Ubicar punto de interes" as marker
  usecase "Animar tramos de calle" as animate
  usecase "Mostrar iconos del mapa" as icons
  usecase "Cerrar guia y limpiar mapa" as reset
}
Ciudadano --> destination
destination .> marker : <<include>>
marker .> animate : <<include>>
animate .> icons : <<include>>
Ciudadano --> reset"""),
    ),
    (
        "03-caso-uso-mapaconf",
        "Caso de uso - MapaConf: autor de rutas internas",
        uml("MapaConf - autor de rutas internas", """left to right direction
actor Administrador
rectangle "Editor MapaConf" {
  usecase "Crear ruta interna" as create
  usecase "Editar nombre e indicaciones" as copy
  usecase "Definir nodos del recorrido" as nodes
  usecase "Asignar asset a cada tramo" as segment
  usecase "Vincular audio" as audio
  usecase "Publicar o archivar ruta" as publish
}
Administrador --> create
Administrador --> copy
Administrador --> nodes
nodes .> segment : <<include>>
Administrador --> audio
create .> publish : <<include>>"""),
    ),
    (
        "04-caso-uso-maparconf",
        "Caso de uso - MapaRConf: compositor de mapa urbano",
        uml("MapaRConf - compositor de mapa urbano", """left to right direction
actor Administrador
rectangle "Editor MapaRConf" {
  usecase "Reemplazar fondo del mapa" as background
  usecase "Subir mapa, icono o decoracion" as upload
  usecase "Colocar elemento visual" as place
  usecase "Cambiar tamano, giro o espejo" as transform
  usecase "Guardar catalogo visual" as save
}
Administrador --> background
Administrador --> upload
upload .> place : <<include>>
place .> transform : <<include>>
background .> save : <<include>>
transform .> save : <<include>>"""),
    ),
    (
        "05-componentes",
        "Diagrama de componentes - entrega de un recorrido",
        uml("Componentes - entrega de un recorrido", """package "Cliente web" {
  [Mapa] as mapa
  [MapaR] as mapar
  [RouteViewer] as viewer
  [RoutePanel] as panel
  [SvgRenderer] as svg
}
component "Flask API" as api
database "routes-config.json" as config
folder "assets clasificados" as files
mapa --> viewer
mapar --> viewer
viewer --> panel
viewer --> svg
viewer --> api : GET /api/config
api --> config : cargar configuracion
api --> files : servir recursos"""),
    ),
    (
        "06-clases",
        "Diagrama de clases - configuracion persistente",
        uml("Clases - configuracion persistente", """class MapConfig {
  background
  viewBox
}
class Route {
  id
  name
  archived
  instructions
  audio
}
class RouteNode {
  x
  y
}
class SegmentAsset {
  assetId
  rotation
  mirrored
}
class MapMarker {
  assetId
  x
  y
  width
}
class Decoration {
  assetId
  rotation
}
class AssetCatalog {
  find(assetId)
}
MapConfig "1" *-- "many" Route
MapConfig "1" *-- "many" MapMarker
MapConfig "1" *-- "many" Decoration
Route "1" *-- "many" RouteNode
Route "1" *-- "many" SegmentAsset
SegmentAsset --> AssetCatalog
MapMarker --> AssetCatalog
Decoration --> AssetCatalog"""),
    ),
    (
        "07-secuencia-mapa",
        "Secuencia - Mapa muestra una dependencia",
        uml("Mapa - mostrar una dependencia", """actor Visitante
participant "Boton de dependencia" as Button
participant RouteViewer
participant SvgRenderer
participant RoutePanel
participant Audio
Visitante -> Button : pulsa una oficina
Button -> RouteViewer : selectRoute(routeId)
RouteViewer -> SvgRenderer : dibuja nodos y tramos
SvgRenderer --> RouteViewer : recorrido listo
RouteViewer -> RoutePanel : muestra titulo y pasos
alt la ruta tiene audio
  RouteViewer -> Audio : play(audioUrl)
end
RouteViewer --> Visitante : guia visible"""),
    ),
    (
        "08-secuencia-mapar",
        "Secuencia - MapaR anima una ruta urbana",
        uml("MapaR - animar una ruta urbana", """actor Ciudadano
participant "Boton de destino" as Button
participant MapaR
participant "Capa de rutas" as Layer
participant "Capa de iconos" as Icons
participant Temporizador
Ciudadano -> Button : selecciona destino
Button -> MapaR : activateDestination(id)
MapaR -> Layer : crea assets por segmento
Layer -> Layer : anima recorrido
MapaR -> Icons : mantiene marcadores urbanos
MapaR -> Temporizador : programa salida
Temporizador -> MapaR : limpiar ruta al terminar
MapaR --> Ciudadano : vuelve al mapa base"""),
    ),
    (
        "09-secuencia-mapaconf",
        "Secuencia - MapaConf guarda una ruta editada",
        uml("MapaConf - guardar una ruta editada", """actor Administrador
participant "Formulario de ruta" as Form
participant RouteEditor
participant "Vista SVG" as Preview
participant "Config API" as API
database Config
Administrador -> Form : cambia pasos y nodos
Form -> RouteEditor : updateDraft(data)
RouteEditor -> Preview : renderDraft()
Administrador -> RouteEditor : guardar
RouteEditor -> RouteEditor : valida nodos y tramos
RouteEditor -> API : PUT /api/config
API -> Config : reemplazo atomico
Config --> API : guardado
API --> RouteEditor : 200 OK"""),
    ),
    (
        "10-secuencia-maparconf",
        "Secuencia - MapaRConf reemplaza un fondo",
        uml("MapaRConf - reemplazar fondo", """actor Administrador
participant "Selector de mapas" as Picker
participant "Upload API" as Upload
folder "uploads/maps" as Maps
participant RouteEditor
participant "Config API" as ConfigApi
Administrador -> Picker : elige archivo de mapa
Picker -> Upload : POST /api/upload/maps
Upload -> Maps : almacena archivo
Maps --> Upload : ruta publica
Upload --> Picker : assetId y src
Picker -> RouteEditor : setBackground(assetId)
RouteEditor -> ConfigApi : PUT /api/config
ConfigApi --> Administrador : fondo publicado"""),
    ),
    (
        "11-estados-ruta",
        "Estados - ciclo de publicacion de una ruta",
        uml("Estados - ciclo de una ruta", """[*] --> Borrador
Borrador --> Validada : tiene nombre y dos nodos
Validada --> Visible : guardar y publicar
Visible --> Archivada : archivar
Archivada --> Visible : restaurar
Visible --> Borrador : editar
Borrador --> Descartada : eliminar
Descartada --> [*]"""),
    ),
    (
        "12-estados-editor",
        "Estados - transformacion de un elemento visual",
        uml("Estados - elemento visual del editor", """[*] --> EnCatalogo
EnCatalogo --> Seleccionado : elegir asset
Seleccionado --> Colocando : pulsar colocar
Colocando --> Ajustando : soltar en el mapa
Ajustando --> Ajustando : mover, girar o espejar
Ajustando --> Guardado : confirmar
Guardado --> EnUso : guardar configuracion
EnUso --> Seleccionado : volver a editar
Seleccionado --> EnCatalogo : cancelar"""),
    ),
    (
        "13-estados-recorrido",
        "Estados - reproduccion de audio de una ruta",
        uml("Estados - audio de indicaciones", """[*] --> SinAudio
SinAudio --> Disponible : se vincula archivo
Disponible --> Reproduciendo : usuario inicia guia
Reproduciendo --> Pausado : pausar
Pausado --> Reproduciendo : continuar
Reproduciendo --> Finalizado : termina archivo
Finalizado --> Disponible : reiniciar
Disponible --> SinAudio : quitar audio"""),
    ),
    (
        "14-actividad-mapa",
        "Actividad - consulta guiada dentro del terminal",
        uml("Actividad - Mapa dentro del terminal", """start
:Pulsar una dependencia;
:Resolver la ruta activa;
:Resaltar destino final;
:Dibujar cada tramo en SVG;
:Convertir indicaciones en lista numerada;
if (Existe audio?) then (si)
  :Iniciar narracion;
endif
:Mantener la guia visible;
:Ocultar el recorrido al finalizar;
stop"""),
    ),
    (
        "15-actividad-mapar",
        "Actividad - recorrido urbano temporal",
        uml("Actividad - MapaR recorrido urbano", """start
:Elegir un destino de ciudad;
:Conservar iconos de puntos de interes;
:Crear sprites para cada tramo;
:Aplicar giro y espejo configurados;
:Animar el avance sobre calles;
:Abrir panel de instrucciones;
:Esperar el tiempo de visualizacion;
:Eliminar sprites temporales;
stop"""),
    ),
    (
        "16-actividad-crear-ruta",
        "Actividad - construir una ruta desde MapaConf",
        uml("Actividad - crear ruta en MapaConf", """start
:Crear borrador;
:Escribir nombre y pasos;
repeat
  :Pulsar sobre el mapa para agregar nodo;
  :Elegir asset del siguiente tramo;
repeat while (Faltan tramos?) is (si)
if (Se necesita audio?) then (si)
  :Seleccionar o subir audio;
endif
:Validar la ruta;
:Guardar y habilitar boton;
stop"""),
    ),
    (
        "17-actividad-assets",
        "Actividad - personalizar el lienzo desde MapaRConf",
        uml("Actividad - personalizar MapaRConf", """start
:Elegir modo fondo, icono o decoracion;
if (El asset ya existe?) then (si)
  :Seleccionar desde el catalogo;
else (no)
  :Subir archivo y clasificarlo;
endif
:Colocar el elemento sobre el mapa;
:Ajustar posicion y tamano;
:Girar en incrementos de 45 grados;
if (Debe verse al reves?) then (si)
  :Activar modo espejo;
endif
:Guardar composicion;
stop"""),
    ),
    (
        "18-colaboracion-mapa",
        "Colaboracion - objetos de una guia interna",
        uml("Colaboracion - guia interna en Mapa", """object Visitante
object RouteButton
object RouteViewer
object RouteData
object SvgRenderer
object InstructionList
Visitante --> RouteButton : 1 pulsa
RouteButton --> RouteViewer : 2 routeId
RouteViewer --> RouteData : 3 obtiene ruta
RouteViewer --> SvgRenderer : 4 dibuja ruta
RouteViewer --> InstructionList : 5 ordena pasos"""),
    ),
    (
        "19-colaboracion-editor",
        "Colaboracion - objetos del editor de rutas",
        uml("Colaboracion - edicion de nodos en MapaConf", """object Administrador
object NodeTool
object RouteEditor
object DraftRoute
object SvgPreview
object SaveButton
Administrador --> NodeTool : 1 selecciona herramienta
NodeTool --> RouteEditor : 2 agrega o mueve nodo
RouteEditor --> DraftRoute : 3 modifica modelo
RouteEditor --> SvgPreview : 4 actualiza vista
Administrador --> SaveButton : 5 confirma
SaveButton --> RouteEditor : 6 persiste borrador"""),
    ),
    (
        "20-colaboracion-assets",
        "Colaboracion - objetos del catalogo visual",
        uml("Colaboracion - catalogo visual en MapaRConf", """object Administrador
object AssetPicker
object UploadDialog
object UploadAPI
object AssetCatalog
object MapCanvas
Administrador --> AssetPicker : 1 busca recurso
AssetPicker --> UploadDialog : 2 solicita archivo nuevo
UploadDialog --> UploadAPI : 3 envia archivo
UploadAPI --> AssetCatalog : 4 registra asset
AssetCatalog --> AssetPicker : 5 devuelve assetId
AssetPicker --> MapCanvas : 6 coloca y transforma"""),
    ),
]


def main() -> None:
    OUT.mkdir(exist_ok=True)
    SOURCE_DIR.mkdir(exist_ok=True)
    markdown = ["# Codigos PlantUML diferenciados", ""]
    for index, (slug, title, source) in enumerate(DIAGRAMS, start=1):
        (SOURCE_DIR / f"{slug}.puml").write_text(source, encoding="utf-8")
        markdown.extend([f"## {index}. {title}", "", "```plantuml", source.strip(), "```", ""])
    MARKDOWN_PATH.write_text("\n".join(markdown), encoding="utf-8")
    print(f"Actualizados {len(DIAGRAMS)} codigos PlantUML.")


if __name__ == "__main__":
    main()
