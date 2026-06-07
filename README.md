# Terminal de localizacion de oficinas

Pagina web interactiva para mostrar rutas desde la Entrada hacia oficinas sobre un croquis.

## Caracteristicas

- Frontend con HTML, CSS y JavaScript puro.
- Backend de despliegue con Nginx dentro de Docker.
- Mapa ajustado a una base SVG de `2000 x 1000`.
- La imagen ocupa toda la base del mapa para evitar margenes laterales.
- Rutas manuales definidas con coordenadas SVG.
- Animacion con `stroke-dasharray` y `stroke-dashoffset`.
- Ruta visual con huellas direccionales desde assets: arriba, abajo, derecha e izquierda, colocadas sobre los pasillos.
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

Activa la casilla `Depuracion` y haz clic sobre el croquis. La pagina dejara una marca con las coordenadas `x, y` de la base SVG `2000 x 1000`.

Las marcas se pueden arrastrar para moverlas. Tambien puedes editar directamente los campos `x` y `y` de cada marca. Para borrar una marca, usa el boton `x` de la etiqueta.

Si el modo depuracion esta activo y presionas un boton de oficina, la ruta seleccionada dejara marcas automaticamente en cada punto de recorrido. Esto sirve para ver donde inicia, donde gira y donde termina la linea.

## Modo trazado

Activa la casilla `Trazado` para crear una linea recta temporal entre dos puntos.

1. Haz clic en el primer punto.
2. Haz clic en el segundo punto.
3. La pagina dibuja una linea recta entre ambos y muestra automaticamente el angulo entre el primer punto y el segundo.
4. Toca cualquier parte de la linea para mostrar la coordenada `x, y` exacta de ese punto.

El angulo se calcula desde la horizontal: una linea horizontal marca `0 grados`, una vertical marca `90 grados` y una diagonal perfecta marca `45 grados`.

Los puntos del trazado se pueden arrastrar para ajustar la linea. Tambien puedes editar directamente sus campos `x` y `y`. El angulo se actualiza automaticamente al moverlos o editar sus valores. Tambien se pueden borrar con la `x` de cada etiqueta. Si borras uno de los dos puntos, la linea se oculta hasta que vuelvas a tener dos puntos.

`Depuracion` y `Trazado` pueden estar activos al mismo tiempo. En ese caso, los clics en el mapa pueden crear marcas de depuracion y tambien completar los dos puntos del trazado.

Usa esas coordenadas para ajustar rutas en `frontend/assets/js/script.js`:

```js
const routes = {
  contaduria: "M 987 737 L 617 737 L 617 345 L 515 345",
  administracion: "M 987 737 L 617 737 L 617 462 L 515 462",
  sala: "M 987 737 L 617 737 L 633 291",
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
