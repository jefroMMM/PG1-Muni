# Seminario de Tecnologías de Información

Dos aportes al proyecto municipal: **Cypress E2E** y **API Testing**. Comparten
Cypress como herramienta, pero sus objetivos y evidencias son distintos. No son
pruebas unitarias ni se presenta Cypress como un tercer aporte.

## Instalar y ejecutar en Windows

Desde la raíz de PG1-Muni, con Python 3.10+, Node.js 22.12+ y Chrome instalado:

```powershell
python -m venv tests/seminario/.venv
tests/seminario/.venv/Scripts/python.exe -m pip install -r tests/seminario/requirements.txt
cd tests/seminario
npm ci
cd ../..
tests/seminario/.venv/Scripts/python.exe tests/seminario/run.py
```

En Linux/macOS usa `tests/seminario/.venv/bin/python` en lugar de
`tests/seminario/.venv/Scripts/python.exe`. npm ci instala también el ejecutable
de Cypress si no está en caché; necesita Internet. No hace falta Docker, levantar
la aplicación manualmente ni el laboratorio BDD archivado.

El audio requerido es `Audio de prueba.mp3` en la raíz. También puedes indicar
otro MP3 mediante `$env:SEMINARIO_AUDIO='C:\ruta\audio.mp3'`. El croquis adjunto
se conserva en `fixtures/croquis.png`. `.env.example` documenta las variables;
no se carga automáticamente ni contiene secretos.

## Ejecutar cada aporte por separado

```powershell
tests/seminario/.venv/Scripts/python.exe tests/seminario/run.py --aporte e2e
tests/seminario/.venv/Scripts/python.exe tests/seminario/run.py --aporte api
```

No ejecutar `cypress run` directamente. El servidor aislado y las rutas de
almacenamiento son obligatorios y los prepara `run.py`.

## Qué comprueban

| Archivo | Aporte y objetivo |
| --- | --- |
| `e2e.cy.js` | E2E01 crea sección, carga fondo y audio reales, configura ruta con tres nodos, dos indicaciones, color y duración, guarda, recarga y verifica el visor. E2E02 comprueba rechazo de nombre vacío, conservación del JSON y corrección posterior. |
| `api.cy.js` | API01 creación y duplicados; API02 edición aislada; API03 seis variantes inválidas; API04 recursos ausentes; API05 límite de nombre de sección; API06 carga incompleta y catálogo inválido. |
| `run.py` | Crea Flask temporal, inicia Cypress, conserva evidencias y compara hashes de los datos reales. |
| `cypress.config.js` | Configura Chrome, tareas de lectura/restablecimiento temporal, JUnit, capturas y resumen. |

El E2E observa solicitudes reales mediante `cy.intercept` y no simula respuestas.
Las pruebas de API utilizan `cy.request` contra el servidor real de pruebas y
comprueban contenido, mensajes e integridad, además de códigos HTTP.

## Aislamiento y límites

- Cada ejecución crea un directorio temporal fuera del proyecto. `ConfigStore`
  usa allí una copia de la semilla; las cargas se escriben en su biblioteca temporal.
- Antes de cada prueba se restablece ese JSON. Los recursos temporales se eliminan
  junto al directorio al terminar toda la ejecución. No hay acumulación en data.
- Solo se leen recursos originales para mostrar las imágenes de la semilla.
- Se comparan archivos y directorios de data, croquis y MP3 antes/después.
- Cypress sigue enlaces del editor en la misma pestaña después de comprobar que
  originalmente tienen `target="_blank"`. No comprueba navegación entre pestañas.
- La prueba comprueba carga, asociación y entrega exacta del MP3. No certifica
  calidad acústica ni que una persona escuche audio en el equipo.
- No se mide rendimiento ni se cubren móviles, autenticación o concurrencia.
- Ejecutar las pruebas secuencialmente; no se preparó ejecución paralela.

## Mostrar que las pruebas detectan un problema

```powershell
tests/seminario/.venv/Scripts/python.exe tests/seminario/run.py --aporte api --defecto-controlado
```

Esta ejecución **debe fallar**: el ejecutor debilita en memoria la validación del
nombre solamente dentro del proceso temporal. API03 espera HTTP 400 y detecta
HTTP 201. No edita archivos de producción; al salir desaparece esa instancia.
Vuelve a ejecutar el comando normal para demostrar el comportamiento correcto.

## Evidencias y documentación

Cada ejecución escribe una carpeta con fecha en `results/`: JUnit, resumen JSON,
log, comprobación de integridad y capturas. La ejecución con defecto tiene su
propia carpeta y no sobrescribe el éxito. Los resultados generados y dependencias
están excluidos de Git. La evidencia seleccionada y el informe están en
`documentacion/seminario/`, con diagramas editables e instrucciones de exposición.

No se crea CI, no se despliega y no se hace commit o push automáticamente.
Antes de entregar un enlace de GitHub, registrar solo los archivos de este aporte
y sus evidencias; revisar aparte los cambios locales previos del proyecto.
