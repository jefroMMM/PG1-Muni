# Resultados verificados

Fecha: 30 de octubre de 2026, America/Guatemala.

| Caso | Resultado normal |
| --- | --- |
| E2E01 crea sección, carga croquis y audio, dibuja ruta y conserva su configuración | Aprobado |
| E2E02 rechaza nombre vacío, conserva lo guardado y permite corregir | Aprobado |
| API01 crea una ruta en los límites, consulta su contenido y rechaza ID duplicado | Aprobado |
| API02 edita una ruta y conserva las otras rutas y mapas | Aprobado |
| API03 rechaza nombre vacío, pocos nodos, coordenadas y duración inválidas sin escrituras | Aprobado |
| API04 devuelve 404 para mapa o ruta ausentes sin crearlos | Aprobado |
| API05 crea sección con nombre de 80 caracteres y rechaza 81 | Aprobado |
| API06 rechaza cargas sin archivo y catálogos malformados | Aprobado |

Total: 8 aprobadas, 0 fallidas, 0 pendientes y 0 omitidas.

## Detección de defecto controlado

5 aprobadas y 1 fallida de 6 API. API03 esperaba 400 y recibió 201 para un nombre vacío.
Fallo intencional del proceso temporal; no es un defecto observado en producción.

Integridad de los datos: sin cambios en ambas ejecuciones. Servidor detenido al finalizar.

Los archivos JUnit, resumen.json, ejecucion.json y cypress.log están en las carpetas normal y defecto-controlado.
