# Terminal de localizacion de oficinas

Aplicacion web para mostrar rutas sobre dos mapas:

- `/` muestra la terminal/oficinas.
- `/MapaR/` muestra el mapa de Retalhuleu.
- `/Conf` permite editar graficamente las rutas de la terminal.
- `/MapaR/Conf` permite editar graficamente las rutas del mapa de Retalhuleu.
- `/dashboard` agrupa las rutas de Mapa y MapaR. Cada ruta abre su propio editor en una nueva pestana del navegador; los titulos permiten editar el fondo, iconos y decoraciones del mapa.
- `/dashboard2` ofrece una interfaz administrativa con navegacion lateral, resumen de rutas, busqueda y filtros de estado. Conserva los mismos editores y datos.

En cada seccion, **Nueva ruta** abre un borrador que se publica al guardar. **Nueva seccion** permite indicar un nombre, escoger uno de ocho iconos y elegir un mapa inicial; cada seccion conserva sus rutas por separado. Desde el editor, **Previsualizar ruta** muestra el recorrido animado, las indicaciones y el audio del borrador sin guardar la configuracion. Las nuevas secciones tienen su visor en `/maps/<id>` y su editor en `/maps/<id>/Conf`.

El dashboard esta disponible en `http://localhost:3000/dashboard` y `http://localhost:8080/dashboard` al ejecutar Docker Compose. Las variantes visuales comparten las mismas rutas. Desde el dashboard, el guardado de una ruta solo actualiza esa ruta, y el guardado de un mapa solo actualiza su fondo, iconos y decoraciones.

## Caracteristicas

- Frontend con HTML, CSS y JavaScript modular.
- Backend pequeno con Flask para servir el frontend y guardar configuracion.
- Configuracion compartida en `data/routes-config.json`.
- API JSON:
  - `GET /api/config`
  - `PUT /api/config`
- Rutas generadas desde configuracion, no desde constantes dentro del codigo.
- Editor grafico para crear, editar, archivar y desarchivar rutas.
- Nodos arrastrables sobre base SVG `2000 x 1000`.
- Seleccion de asset por tramo desde catalogo interno.
- Iconos colocables y movibles sobre el mapa.
- Audios existentes conservados para las rutas iniciales.

## Estructura principal

```text
.
|-- backend/
|   |-- app.py
|   |-- Dockerfile
|   `-- requirements.txt
|-- data/
|   |-- routes-config.default.json
|   `-- routes-config.json
|-- frontend/
|   |-- index.html
|   |-- conf.html
|   |-- assets/
|   |   |-- css/
|   |   |-- js/
|   |   |   |-- shared/
|   |   |   |-- terminal.js
|   |   |   |-- mapar.js
|   |   |   `-- route-editor.js
|   |   |-- images/
|   |   `-- Audios/
|   `-- MapaR/
|       |-- index.html
|       |-- Imagenes-MapaR/
|       `-- Audios/
`-- docker-compose.yml
```

## Uso con Docker

Construir y ejecutar:

```bash
docker compose up --build
```

Abrir:

```text
http://localhost:8080/
http://localhost:8080/MapaR/
http://localhost:8080/Conf
http://localhost:8080/MapaR/Conf
```

Detener:

```bash
docker compose down
```

`docker-compose.yml` monta `./data:/app/data`, por lo que los cambios hechos desde los editores quedan en `data/routes-config.json` y sobreviven reinicios o reconstrucciones del contenedor.

## Editor grafico

En `/Conf` o `/MapaR/Conf` puedes:

- crear nuevas rutas;
- cambiar nombre, color e indicaciones;
- archivar o desarchivar rutas;
- agregar nodos haciendo clic sobre el mapa;
- mover nodos arrastrandolos;
- borrar el ultimo nodo de una ruta;
- escoger el asset de cada tramo;
- colocar iconos desde el catalogo interno;
- mover o borrar iconos;
- guardar los cambios para que aparezcan en las pantallas normales.

Las rutas archivadas siguen apareciendo en el editor, pero no se muestran como botones en `/` ni en `/MapaR/`.

## Configuracion

La configuracion vive en `data/routes-config.json`. El archivo `data/routes-config.default.json` sirve como semilla inicial si el archivo principal no existe.

Cada mapa contiene:

- `background`: imagen de fondo.
- `viewBox`: base SVG, actualmente `0 0 2000 1000`.
- `routes`: rutas visibles o archivadas.
- `markers`: iconos colocados sobre el mapa.

Cada ruta contiene:

- `id`, `name`, `archived`;
- `instructions`;
- `nodes`;
- `segmentAssets`;
- `highlightPolygon`, opcional para resaltar oficinas;
- `audio`, opcional para rutas existentes.
