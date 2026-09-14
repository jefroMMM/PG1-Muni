# Documentacion de QA — Terminal de localizacion de oficinas

Este documento sirve como base para probar la aplicacion. Se concentra en las funciones que pueden fallar por datos incorrectos o incompletos: rutas, nodos, recursos del mapa, archivos y configuracion. No es necesario probar ni documentar todos los estilos visuales disponibles.

## Alcance

La aplicacion permite consultar rutas en dos mapas y administrarlas desde un editor:

| Funcion | Vista de consulta | Vista de administracion |
|---|---|---|
| Terminal de oficinas | `/` | `/Conf` |
| Mapa de Retalhuleu | `/MapaR/` | `/MapaR/Conf` |

La configuracion se guarda mediante la API y queda persistida en `data/routes-config.json`.

## Componentes que se deben probar

1. Consulta de rutas: botones, dibujo del recorrido, indicaciones y audio.
2. Edicion de rutas: crear, duplicar, archivar, desarchivar y borrar.
3. Edicion de nodos: agregar, mover y borrar el ultimo nodo.
4. Recursos: asignar imagenes al recorrido, iconos, decoraciones, fondos y audios.
5. Persistencia: cargar y guardar configuracion por API.
6. Validacion de archivos: solo se aceptan tipos de archivo compatibles con cada carga.

## Particiones de equivalencia

Una particion agrupa entradas que deberian tener el mismo resultado. Basta elegir uno o dos valores representativos de cada grupo, en lugar de probar todos los valores posibles.

### Rutas

| Campo o accion | Clase valida | Clase invalida | Resultado esperado |
|---|---|---|---|
| Nombre de ruta | Texto con contenido, por ejemplo `Tesoreria` | Vacio, solo espacios o ausente | La ruta no debe guardarse sin nombre; mostrar un mensaje claro. |
| Identificador (`id`) | Unico y estable, por ejemplo `tesoreria` | Repetido, vacio o con valor no textual | No debe reemplazar ni confundir otra ruta. |
| Estado `archived` | `true` o `false` | Texto, numero o campo ausente | Solo las rutas con `false` aparecen en la vista de consulta. |
| Color de boton | Color CSS valido, por ejemplo `#158b8f` | Cadena vacia o color no valido | Debe conservarse un color seguro o impedir el guardado. |
| Indicaciones | Texto legible con contenido | Vacio o tipo distinto de texto | La ruta debe mostrar indicaciones o informar que faltan. |
| Audio | Ruta a un audio existente o valor vacio | Ruta inexistente o archivo no reproducible | La ruta sigue funcionando; el fallo de audio no debe romper el mapa. |

### Nodos de una ruta

| Entrada | Clase valida | Clase invalida | Resultado esperado |
|---|---|---|---|
| Cantidad de nodos | Dos o mas nodos | Cero o un nodo | No se debe mostrar un recorrido incompleto. |
| Coordenada `x` | Numero entre `0` y `2000` | Negativo, mayor que `2000`, texto o vacio | El nodo no debe quedar fuera del mapa ni generar errores. |
| Coordenada `y` | Numero entre `0` y `1000` | Negativo, mayor que `1000`, texto o vacio | El nodo no debe quedar fuera del mapa ni generar errores. |
| Movimiento de nodo | Arrastre dentro del mapa | Arrastre fuera del mapa o sin seleccion | La posicion debe limitarse al area visible o ignorar la accion invalida. |
| Borrar ultimo nodo | Ruta con tres o mas nodos | Ruta con dos o menos nodos | No debe dejar una ruta sin recorrido valido. |

### Recursos de recorrido, iconos y decoraciones

| Elemento | Clase valida | Clase invalida | Resultado esperado |
|---|---|---|---|
| Asset por tramo | Un asset existente por cada tramo | Asset inexistente o cantidad distinta de tramos | La ruta debe seguir renderizando sin errores; no mostrar recursos rotos. |
| Icono de mapa | `assetId` existente y coordenadas validas | `assetId` inexistente o coordenadas invalidas | No debe mostrar una imagen rota ni bloquear el editor. |
| Decoracion | Archivo de imagen compatible y posicion valida | Archivo no imagen o posicion invalida | Rechazar el archivo o no guardar una decoracion inconsistente. |
| Fondo | Imagen compatible accesible | Archivo no imagen o ruta inexistente | Mantener el fondo anterior y mostrar el error. |

### Archivos cargados

| Carga | Clase valida | Clase invalida | Resultado esperado |
|---|---|---|---|
| Asset, icono, decoracion o mapa | Archivo de imagen (`image/*`) | Audio, documento, ejecutable o archivo vacio | El servidor debe responder con error `400` si falta archivo; la interfaz debe rechazar formatos no permitidos. |
| Audio | Archivo de audio (`audio/*`) | Imagen, documento, ejecutable o archivo vacio | No debe agregarse al catalogo como audio. |
| Nombre del archivo | Nombre normal con extension | Sin nombre o extension no compatible | No debe producir rutas malformadas ni errores del servidor. |

### Configuracion y API

| Solicitud | Clase valida | Clase invalida | Resultado esperado |
|---|---|---|---|
| `GET /api/config` | Configuracion JSON existente | Archivo de configuracion inexistente | Se crea desde `routes-config.default.json` y se devuelve JSON. |
| `PUT /api/config` | Objeto JSON que contiene `maps` y `catalog` | JSON malformado, texto no JSON, lista o campos principales ausentes | Respuesta `400` con `Configuracion invalida`; no debe sobrescribirse la configuracion correcta. |
| Guardar cambios | Conexion disponible y datos validos | Error de red o respuesta no exitosa | Se informa el fallo y los cambios no confirmados no se consideran guardados. |

## Casos de prueba prioritarios

| ID | Caso | Pasos resumidos | Resultado esperado |
|---|---|---|---|
| QA-01 | Consultar ruta activa | Abrir `/` y seleccionar una oficina. | Se dibuja la ruta, se leen las indicaciones y, si existe, se reproduce el audio. |
| QA-02 | Ruta archivada | Archivar una ruta en `/Conf`, guardar y abrir `/`. | La ruta no aparece como opcion al usuario, pero sigue visible en el editor. |
| QA-03 | Crear ruta valida | Crear ruta, escribir nombre, agregar al menos dos nodos y guardar. | La ruta queda disponible tras recargar la pagina. |
| QA-04 | Nombre invalido | Intentar guardar una ruta nueva con nombre vacio. | Se bloquea el guardado o se muestra un error de validacion. |
| QA-05 | Nodos fuera de limites | Mover un nodo al borde y fuera del mapa. | El nodo queda dentro de `0–2000` en X y `0–1000` en Y, o se rechaza el movimiento. |
| QA-06 | Eliminar nodos minimos | Borrar nodos hasta dejar menos de dos. | La aplicacion evita una ruta invalida o avisa al usuario. |
| QA-07 | Archivo incorrecto | Intentar cargar un `.pdf` como icono y una imagen como audio. | La carga se rechaza y la configuracion no cambia. |
| QA-08 | Configuracion incompleta | Enviar `PUT /api/config` sin `maps` o sin `catalog`. | Respuesta HTTP `400`; se conserva el archivo anterior. |
| QA-09 | Recurso inexistente | Configurar temporalmente una imagen o audio con ruta inexistente. | La pantalla no se cae; el error queda contenido en ese recurso. |
| QA-10 | Persistencia | Editar una ruta, guardar, recargar y reiniciar el contenedor. | Los cambios permanecen en `data/routes-config.json`. |

## Criterios de aceptacion

- Una ruta visible tiene nombre, al menos dos nodos validos y recursos que no interrumpen la visualizacion.
- Las rutas archivadas no se muestran al usuario final.
- Un dato invalido no debe dañar ni reemplazar la configuracion existente.
- Los archivos cargados se almacenan y se pueden recuperar desde `/uploads/`.
- Si un recurso opcional falla, el mapa y las demas rutas continúan operando.
- Los cambios confirmados en el editor siguen presentes al recargar la aplicacion.

## Registro sugerido de incidencias

Para cada error encontrado, registrar: ID de caso, fecha, mapa afectado, pasos para reproducir, resultado obtenido, resultado esperado, evidencia (captura) y severidad.

Severidad recomendada:

- **Alta:** impide consultar rutas, guardar la configuracion o abrir una pantalla.
- **Media:** una ruta, audio o recurso concreto no funciona, pero el resto de la aplicacion sí.
- **Baja:** texto, alineacion o detalle visual que no impide completar la tarea.
