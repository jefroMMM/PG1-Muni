# Terminal de localizacion de oficinas

Pagina web interactiva para mostrar rutas desde la Entrada hacia oficinas sobre un croquis.

## Caracteristicas

- Frontend con HTML, CSS y JavaScript puro.
- Backend de despliegue con Nginx dentro de Docker.
- Mapa ajustado a una base SVG de `2000 x 1000`.
- La imagen ocupa toda la base del mapa para evitar margenes laterales.
- Rutas manuales definidas con coordenadas SVG.
- Animacion con `stroke-dasharray` y `stroke-dashoffset`.
- Resaltado visual de la oficina destino.
- Modo de depuracion para obtener coordenadas al hacer clic sobre el mapa.

## Estructura

```text
.
|-- frontend/
|   |-- index.html
|   `-- assets/
|       |-- css/
|       |   `-- styles.css
|       |-- js/
|       |   `-- script.js
|       `-- images/
|           `-- croquis-terminal-2000x1000.png
|-- backend/
|   |-- Dockerfile
|   |-- nginx.conf
|   `-- requirements.txt
|-- docker-compose.yml
|-- .dockerignore
|-- .gitignore
`-- README.md
```

## Uso local sin Docker

Abre este archivo directamente en el navegador:

```text
frontend/index.html
```

## Modo depuracion

Activa la casilla `Depuracion` y haz clic sobre el croquis. La pagina mostrara coordenadas `x, y` de la base SVG `2000 x 1000`.

Usa esas coordenadas para ajustar rutas en `frontend/assets/js/script.js`:

```js
const routes = {
  contaduria: "M 1000 877 L 1000 808 L 556 808 L 556 473 L 514 473 L 514 356 L 419 319",
  administracion: "M 1000 877 L 1000 808 L 556 808 L 556 484 L 514 484 L 514 563 L 389 648",
  sala: "M 1000 877 L 1000 808 L 556 808 L 556 473 L 556 313 L 670 287 L 909 260",
  rrhh: "M 1000 877 L 1000 808 L 1423 808 L 1423 473 L 1477 473 L 1477 335 L 1621 282",
  gerencia: "M 1000 877 L 1000 808 L 1423 808 L 1423 473 L 1477 473 L 1477 552 L 1663 648"
};
```

## Docker

Construir y ejecutar:

```bash
docker compose up --build
```

Abrir:

```text
http://localhost:8080
```

Detener:

```bash
docker compose down
```

## Backend

Por ahora el backend es la capa de servidor web. Nginx sirve los archivos estaticos del frontend desde `/usr/share/nginx/html`.

No hay API ni base de datos todavia. `backend/requirements.txt` queda como marcador para futuras dependencias si despues se agrega un backend real con Python.
