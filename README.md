# Terminal municipal de rutas

Aplicacion Flask con frontend JavaScript modular para los mapas y recorridos de
la Municipalidad de Retalhuleu.

## Ejecutar

```sh
docker compose up -d --build
```

| Pantalla | URL |
| --- | --- |
| Administracion principal | http://localhost:8080/dashboard2 |
| Administracion clasica | http://localhost:8080/dashboard |
| Mapa de oficinas | http://localhost:8080/ |
| Mapa urbano | http://localhost:8080/MapaR/ |
| Editor de oficinas | http://localhost:8080/Conf |
| Editor urbano | http://localhost:8080/MapaR/Conf |

Las secciones creadas desde el dashboard tienen visor en `/maps/<id>` y editor
en `/maps/<id>/Conf`. Las secciones base conservan sus URLs de la tabla.
Las antiguas variantes numericas y sus assets ya no se publican.

## Estructura activa

```text
backend/
  app.py                 Arranque, fabrica Flask y compatibilidad con pruebas
  api.py                 Endpoints JSON de mapas, rutas y archivos
  pages.py               Pantallas y entrega de archivos publicos
  validation.py          Reglas compartidas y campos permitidos
  storage.py             Persistencia atomica y cache de lectura
  resources.py           Carpetas, propiedad de recursos y URLs compatibles
  Dockerfile
  requirements.txt
frontend/
  index.html             Visor de oficinas
  MapaR/index.html        Visor urbano
  conf.html              Editor compartido
  dashboard.html         Panel clasico
  dashboard2.html        Panel principal
  preview.html           Vista previa de borradores
  assets/
    css/
      styles.css         Estilos compartidos y del visor publico
      editor.css         Estilos exclusivos del editor
      route-preview.css  Dialogo de previsualizacion
      dashboard*.css     Estilos de los paneles
    js/
      route-editor.js    Coordinacion del editor y sus herramientas
      editor/
        area-editor.js        Seleccion y ajuste de cuatro esquinas
        instruction-editor.js Pasos de indicaciones
        placed-items-editor.js Iconos y decoraciones
        catalog-uploads.js    Cargas y actualizacion de catalogos
        preview-controller.js Comunicacion con la vista previa
      shared/
        config-api.js    Acceso HTTP y tratamiento de errores
        sections.js      URLs canonicas y metadatos de secciones
        map-utils.js     Geometria y renderizado SVG
        route-viewer.js  Visor y reproduccion del recorrido
        route-timing.js  Distribucion de la duracion total
        instructions.js Compatibilidad de indicaciones antiguas y nuevas
        highlight-area.js Validacion de areas
        resource-catalog.js Filtros y selectores de bibliotecas por seccion
data/
  routes-config.json          Configuracion guardada
  routes-config.default.json  Configuracion inicial
  recursos/                   Fondos y recursos por seccion
  resource-aliases.json        Equivalencias de las URLs migradas
  backups/                    Respaldo local previo a la migracion
tests/
  test_*.py              Pruebas de API, persistencia y recursos
  js/                    Pruebas de funciones JavaScript
  ui/                    Regresiones visuales y funcionales de ambos editores
tools/                   Herramientas de generacion de documentos
descartados/             Versiones, experimentos y recursos retirados
```

## Bibliotecas por seccion

```text
data/recursos/
  Fondos/                 Biblioteca compartida de mapas y croquis
  assets/
    Mapa/
    MapaR/
    <id-de-seccion>/
  audios/
    Mapa/
    MapaR/
    <id-de-seccion>/
  iconos/
    Compartidos/          Logo municipal
    Mapa/
    MapaR/
    <id-de-seccion>/
  decoraciones/
    Mapa/
    MapaR/
    <id-de-seccion>/
```

Tambien se reservan carpetas Compartidos para recursos sin propietario exclusivo.
Al crear una seccion desde dashboard2 se crean sus carpetas automaticamente.
El nombre visible puede cambiar sin modificar su identificador ni sus archivos.

Los selectores de assets, audios, iconos y decoraciones permiten elegir entre
**Esta seccion y compartidos** y **Todas las secciones**. Los recursos ya asignados
de otra seccion se conservan en las opciones, identificados como En uso.
Los fondos son compartidos y siempre estan disponibles para todos los mapas.

En dashboard2, cada fila tiene acciones para archivar/restaurar y borrar rutas.
El borrado pide confirmacion y conserva los archivos de la biblioteca, incluso
cuando se borra el ultimo recorrido de una seccion. Las operaciones cambian solo
la ruta seleccionada y conservan los cambios de otras ventanas.

Junto al titulo de cada seccion, **Subir archivos** permite agregar audios,
assets, fondos, iconos y decoraciones directamente, incluso varios archivos a la
vez. Se agregan a la biblioteca; los fondos subidos no reemplazan automaticamente
el mapa actual. Los iconos de estas acciones son Lucide 1.64.0, distribuidos
localmente con su licencia en frontend/assets/icons/ui/LICENSE.

Cada entrada del catalogo incluye `sectionId`: terminal, mapar, el identificador
de una seccion nueva o shared. Los visores utilizan el catalogo completo, de modo
que una ruta puede combinar recursos de varias secciones sin duplicar archivos.
La subida envia file, kind y mapKey a POST /api/upload; el servidor devuelve y
registra id, src, name y sectionId, sin esperar al guardado de la ruta.

Los originales se conservan en descartados/recursos-previos. Las antiguas URLs
redirigen a /recursos/... mediante resource-aliases.json; tambien se normalizan
las referencias antiguas que lleguen desde un editor abierto antes de migrar.

## Datos y guardado

Docker monta `./data:/app/data`: los cambios y archivos subidos sobreviven a la
reconstruccion del contenedor. No es necesario reconstruir para guardar rutas.

`ConfigStore` devuelve copias independientes, conserva un cache invalidado por
cambios en el archivo y reemplaza el JSON de forma atomica. Un bloqueo protege
las operaciones de lectura-modificacion-escritura dentro del proceso servidor.
La fabrica `create_app` permite usar almacenamiento y cargas temporales en pruebas.

El editor individual guarda solo su ruta; el editor de mapa guarda solo fondo,
iconos y decoraciones. El editor general conserva el guardado completo.
Las validaciones de rutas y catalogos se comparten entre endpoints.

## Funciones del editor

- Crear, duplicar, archivar y editar rutas desde las pantallas correspondientes.
- Agregar y arrastrar nodos; seleccionar assets, giro y espejo por tramo.
- Redactar indicaciones mediante pasos independientes.
- Definir la duracion total en segundos, incluido el regreso al estado inicial.
- Marcar cuatro esquinas para resaltar el destino; moverlas o editar coordenadas.
- Cambiar mapas, colocar iconos y decoraciones y asociar audios.
- Previsualizar cambios sin publicarlos ni guardar la configuracion.

Los movimientos del puntero se agrupan por fotograma. Los controles de los
catalogos usan delegacion de eventos y asignan los textos mediante propiedades
del DOM, conservando correctamente comillas y caracteres especiales.

## API

| Metodo | Endpoint | Funcion |
| --- | --- | --- |
| GET | /api/config | Consultar configuracion |
| PUT | /api/config | Guardar configuracion completa validada |
| POST | /api/maps | Crear seccion |
| PATCH | /api/maps/<map_key> | Modificar imagen, iconos y decoraciones |
| POST | /api/maps/<map_key>/routes | Crear ruta |
| PATCH | /api/maps/<map_key>/routes/<route_id> | Modificar ruta |
| PATCH | /api/maps/<map_key>/routes/<route_id>/status | Archivar o restaurar ruta |
| DELETE | /api/maps/<map_key>/routes/<route_id> | Borrar ruta conservando sus recursos |
| POST | /api/upload | Subir archivo |

## Desarrollo y pruebas

Con Flask instalado, iniciar desde la raiz con `python -m backend.app`.
La variable `PORT` selecciona el puerto y `ROUTES_CONFIG_PATH` el JSON persistente.

```sh
python -m unittest discover -s tests -p "test_*.py"
node --test tests/js/shared.test.mjs
```

Para las pruebas de interfaz vigentes, instalar Flask, pytest y Selenium en un
entorno virtual y disponer de Chrome; Selenium gestiona ChromeDriver si no se
proporciona uno explicitamente.

```sh
python -m pytest tests/ui/test_editor_ui.py -q
```

Las pruebas usan datos temporales y verifican que los archivos reales permanezcan
intactos. Las capturas de escritorio y movil se generan en `tests/ui/reports`.
Los reportes, entornos virtuales y caches estan excluidos de Git.

## Aportes de Seminario

La verificación con Cypress E2E y API Testing está en `tests/seminario`.
Su [README](tests/seminario/README.md) explica instalación, ejecución con datos
temporales y demostración de detección de errores. El informe y sus evidencias
se conservan en `documentacion/seminario`. No depende del BDD archivado.

## Archivos retirados

`descartados/README.md` describe los traslados. Los archivos historicos se
conservan y quedan fuera de Flask y del contexto de Docker.

El laboratorio BDD, sus reportes, el workflow y su entorno virtual se conservan
en `descartados/laboratorio-bdd`. La entrega universitaria de dos pruebas esta
en `descartados/entregas-historicas/entrega_bdd` y los documentos en
`descartados/documentacion`. El workflow archivado queda fuera de
`.github/workflows` y no se ejecuta desde esa ubicacion.
