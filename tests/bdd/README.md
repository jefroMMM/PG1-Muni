# Laboratorio BDD: edición de rutas desde el panel administrativo

## Alcance y estructura

`features/edicion_rutas_administrativas.feature` conserva los diez escenarios Gherkin originales en español (`# language: es`), con etiquetas de identificación, perspectiva y nivel de prueba. Ahora son ejecutables con pytest-bdd: `test_edicion_rutas.py` enlaza los escenarios e implementa sus pasos; `conftest.py` prepara datos aislados, Selenium, un servidor temporal y reportes. La configuración de CI está en `.github/workflows/bdd.yml`; no se cambia la lógica de producción.

Se analiza el editor individual abierto desde `/dashboard` o `/dashboard2` con `scope=route` y el identificador de una ruta existente. Crear rutas usa otro flujo (`new=1` y POST) y queda fuera del piloto. Los identificadores técnicos en los escenarios sirven para localizar datos y contratos reales; no son nombres propuestos de capacitaciones.

## Los tres amigos

| Perspectiva | Aporte al laboratorio | Escenarios de aporte principal |
|---|---|---|
| Negocio | Define el resultado para el personal de TI y los visitantes: editar la ruta correcta, actualizar la orientación, controlar la visibilidad y revisar antes de guardar. | BDD01–BDD04 |
| Desarrollo | Explica el contrato de guardado por ruta, su aislamiento frente a otros mapas y el comportamiento cuando los datos cargados ya no existen. | BDD09–BDD10 |
| QA | Convierte las reglas reales en comprobaciones reproducibles: nombre inválido, mínimo de puntos, límites de coordenadas y rechazo de solicitudes malformadas. | BDD05–BDD08 |

Las etiquetas organizan el aporte principal; las tres perspectivas deben revisar todos los escenarios. Son propuestas basadas en el código, no acuerdos obtenidos de una sesión con representantes de esas áreas.

## Funcionamiento comprobado en el código

- `frontend/assets/js/dashboard.js` y `dashboard2.js`: el nombre de la ruta o el enlace de edición abre otra pestaña con `scope=route` y `route=<id>`. El segundo panel también permite búsqueda y filtros, pero estos no son el objetivo del piloto.
- `frontend/assets/js/route-editor.js`: el editor individual permite nodos, recursos de recorrido y texto/audio, además de archivar/desarchivar. Oculta crear, duplicar, borrar, fondo, iconos y decoraciones. Esas restricciones son de interfaz, no un mecanismo de autorización.
- Campos editables: nombre, color del botón, indicaciones, audio, tamaño de imágenes del recorrido, nodos, recurso por tramo, rotación y espejo por tramo, y estado archivado. El identificador se conserva; no existe un campo para editarlo.
- Nombre e indicaciones se recortan con `trim()` en la interfaz. Las indicaciones pueden quedar vacías; el inspector avisa `sin indicaciones`, pero el servidor permite guardar. `Sin audio` guarda una cadena vacía. No hay validación de nombres únicos ni un límite de longitud para el nombre de una ruta.
- `shared/map-utils.js`: las coordenadas de la interfaz se redondean y limitan a X entre 0 y 2000 e Y entre 0 y 1000. La interfaz no elimina el último nodo si quedan dos. Al cambiar nodos se normalizan los recursos y opciones para que exista una entrada por tramo.
- El tamaño de imágenes se limita en la interfaz a 12–180; un valor numérico igual a cero usa el tamaño predeterminado antes de limitarlo. La rotación avanza 45 grados y el espejo alterna un booleano.
- `backend/app.py`, `valid_route` y `update_route`: el PATCH exige `route` como objeto, identificador no vacío coincidente con la URL, nombre textual con contenido y al menos dos nodos con coordenadas numéricas dentro de los límites inclusivos. Los booleanos no se aceptan como coordenadas. El catálogo debe ser un objeto y sus grupos `routeAssets` y `audios`, si aparecen, deben ser listas.
- El servidor no valida exhaustivamente color, instrucciones, audio, tamaño, recursos por tramo, transformaciones ni el tipo de `archived`; no se presentan como reglas de rechazo en los escenarios. Tampoco comprueba que el recurso o audio referenciado exista.
- `shared/config-api.js`: la edición individual usa PATCH `/api/maps/<map_key>/routes/<route_id>`, con `route` y los catálogos de recursos y audios. Actualiza solamente los campos permitidos de esa ruta; no modifica fondo, iconos, decoraciones ni otras rutas. Anexa recursos nuevos por identificador conservando los previamente guardados.
- El servidor carga la configuración actual bajo un bloqueo y reemplaza el archivo mediante un temporal. Devuelve HTTP 200 con `{"ok": true}` al actualizar. Dos guardados de rutas distintas conservan ambos cambios. Para dos ediciones de la misma ruta no hay control de versiones: los campos enviados por el último guardado prevalecen.
- La interfaz indica `Cambios sin guardar`, `Guardando...` y `Guardado`. Durante la solicitud deshabilita Guardar; después lo habilita, también si falla. Un rechazo con JSON muestra el mensaje del servidor y conserva el borrador. Hay aviso del navegador al salir con cambios pendientes.
- Errores de API: `Ruta invalida` (400), `Catalogo invalido` (400), `La ruta necesita nombre y al menos dos nodos dentro del mapa` (400), `Mapa no encontrado` (404) y `Ruta no encontrada` (404). Al abrir un editor cuyo identificador no está en la configuración, aparece `La ruta seleccionada ya no existe. Vuelve al dashboard.`
- La previsualización clona el borrador y lo envía a un iframe del mismo origen. Muestra solo esa ruta, incluso si estaba archivada, sin enviar una solicitud de guardado. Subir archivos sí escribe en el servidor antes de guardar la ruta; BDD04 no sube archivos y no afirma que cualquier operación del editor sea libre de escrituras.

## Resumen de escenarios

| ID | Comportamiento que verifica |
|---|---|
| BDD01 | Apertura de la ruta correcta en otra pestaña y alcance de las herramientas del editor individual. |
| BDD02 | Persistencia de campos, nodos y transformaciones de un tramo; actualización del visor sin alterar otros datos. |
| BDD03 | Archivar oculta el botón del visitante; desarchivar lo restaura y conserva la ruta administrativa. |
| BDD04 | La previsualización refleja el borrador sin persistirlo y permite volver a editarlo. |
| BDD05 | Un nombre de espacios provoca HTTP 400, conserva los datos guardados y permite corregir el borrador. |
| BDD06 | La interfaz permite pasar de tres a dos nodos, impide bajar de dos y guarda ese mínimo. |
| BDD07 | La interfaz ajusta coordenadas fuera de rango y admite guardar puntos en los bordes inclusivos. |
| BDD08 | El servicio rechaza siete variantes de datos inválidos sin modificar la configuración. Es un escenario con tabla, no siete escenarios adicionales. |
| BDD09 | Guardar dos rutas distintas desde copias antiguas no revierte los cambios de la otra ruta. |
| BDD10 | Si la ruta desaparece tras cargarla, el PATCH devuelve 404 y no la recrea. |

## Cómo ejecutar nuevamente

Desde la raíz del proyecto, en PowerShell, con Python 3.10 o posterior y Google Chrome disponible:

```powershell
python -m venv .venv-bdd
.\.venv-bdd\Scripts\python.exe -m pip install -r tests/bdd/requirements.txt
.\.venv-bdd\Scripts\python.exe -m pytest -c tests/bdd/pytest.ini tests/bdd -v --junitxml=tests/bdd/reports/junit.xml
```

El entorno ya fue creado en esta máquina; basta el tercer comando para repetir las pruebas. No hace falta activar el entorno, iniciar Docker, abrir un navegador manualmente o levantar la aplicación por separado. `requirements.lock.txt` registra también las versiones transitivas utilizadas; para reproducirlas exactamente se puede instalar ese archivo en lugar de `requirements.txt`.

Selenium Manager resuelve el controlador de Chrome cuando no se proporciona uno. En la primera ejecución necesita acceso a Internet para descargar un controlador compatible. Si Chrome o el controlador están en una ruta especial, se admiten estas variables opcionales:

```powershell
$env:BDD_CHROME_BINARY = 'C:\ruta\chrome.exe'
$env:BDD_CHROMEDRIVER = 'C:\ruta\chromedriver.exe'
```

Las pruebas abren Chrome headless con perfil temporal y ventana de 1920 × 1080. Si falta navegador/controlador o no puede arrancar, el escenario falla con la causa de preparación; no se marca como aprobado ni se omite silenciosamente.

### Arranque de Chrome y diagnóstico de fallos en CI

ChromeDriver crea un perfil temporal nuevo para cada escenario y arranca en `data:,`.
La fixture comprueba que esa página esté cargada antes de ejecutar los pasos; no
reintenta navegaciones ni aumenta las esperas originales (15 segundos por condición
y 30 segundos para cargar una página). El servidor Flask usa un puerto disponible
asignado por el sistema, comprueba `/api/config` por HTTP antes de abrir Chrome y
verifica que la ruta de la semilla temporal exista.

La ejecución de diagnóstico [37981091037](https://github.com/jefroMMM/PG1-Muni/actions/runs/37981091037)
mostró que la navegación a `/dashboard2` era cancelada con `net::ERR_ABORTED` mientras
Chrome permanecía en `chrome://new-tab-page/`. Flask seguía respondiendo HTTP 200,
la semilla era correcta y solo había una pestaña. Al proporcionar `--user-data-dir`,
ChromeDriver omite su argumento inicial `data:,`; la página inicial de Chrome for
Testing podía interferir con la primera navegación. Se retiró únicamente ese
argumento de la fixture, conservando el aislamiento mediante el perfil temporal
gestionado por el controlador. Véase el [código de arranque de ChromeDriver](https://chromium.googlesource.com/chromium/src/+/main/chrome/test/chromedriver/chrome_launcher.cc).

Si falla un escenario se genera `reports/BDDxx-diagnostics.json` con URL, título,
pestañas, estado del documento, errores de consola, eventos de navegación, estado
HTTP del servidor y las últimas solicitudes recibidas. Se conserva junto con la
captura y los reportes en el artifact de Actions. No incluye cuerpos de solicitudes,
configuraciones completas ni credenciales. `resultados.json` registra además la URL
inicial, versión de ChromeDriver y directorio temporal del perfil por escenario.

Se comprobaron los diez escenarios en orden normal e inverso con Chrome for
Testing 155.0.8059.39 en Windows; las fixtures restablecen el estado por escenario.
El orden de ejecución no se utiliza como solución al fallo.

Para ejecutar solo una perspectiva o un nivel:

```powershell
.\.venv-bdd\Scripts\python.exe -m pytest -c tests/bdd/pytest.ini tests/bdd -m api -v
.\.venv-bdd\Scripts\python.exe -m pytest -c tests/bdd/pytest.ini tests/bdd -m interfaz -v
.\.venv-bdd\Scripts\python.exe -m pytest -c tests/bdd/pytest.ini tests/bdd -m BDD02 -v
```

Una selección parcial actualiza los reportes solamente con los escenarios seleccionados. Para obtener el reporte de los diez escenarios se debe usar el comando completo. Ejecutar en una sola sesión sin paralelización: las fixtures sustituyen temporalmente las rutas globales del módulo Flask, por lo que no está soportado ejecutar varios escenarios simultáneamente en el mismo proceso.

## Aislamiento y evidencia

- Cada escenario copia la semilla predeterminada a un directorio temporal de pytest y sustituye `CONFIG_PATH` y `UPLOAD_DIR` mediante `monkeypatch`; al terminar, los valores originales se restauran. BDD06 prepara tres nodos exclusivamente en esa copia. BDD10 elimina exclusivamente la ruta temporal.
- BDD01–BDD07 ejecutan la interfaz real con Selenium contra Flask en `127.0.0.1` y un puerto libre. BDD08–BDD10 usan `app.test_client()`. No se envían solicitudes a los puertos de la instancia real.
- El servidor temporal se detiene y Chrome se cierra al finalizar cada escenario. No se borran directorios del proyecto ni archivos reales. pytest puede retener sus últimas carpetas temporales para diagnóstico.
- Se comparan hashes SHA-256 antes y después de los datos reales, la semilla, los archivos cargados existentes, el CSS local y el Gherkin original. También se comprueba que no aparezcan cargas nuevas en `data/uploads`. Los hashes se incluyen en el reporte JSON.
- Se observan las respuestas PATCH con un envoltorio WSGI de pruebas que deja pasar las solicitudes reales sin cambiar su respuesta. Así BDD05 confirma el HTTP 400 recibido por el navegador, además del mensaje visible.
- Se usan esperas explícitas para carga, pestañas y guardado, sin pausas fijas. Las coordenadas se editan con los controles públicos. Al agregar un punto se hace clic real sobre el SVG y se ajusta la precisión mediante sus campos, porque las posiciones del puntero tienen resolución de píxeles.
- El campo nativo de color se establece con JavaScript sobre el elemento DOM y se dispara su evento `input`, porque escribir un hexadecimal en ese selector nativo no es portátil. No se modifica directamente el modelo de la aplicación ni se sustituye el guardado por una llamada de pruebas.

## Reportes

Después de cada ejecución se actualizan:

- `reports/resultados.md`: resumen legible con resultado por escenario y causas de fallos u omisiones.
- `reports/resultados.json`: fases, tiempos, versiones, errores completos y hashes de integridad.
- `reports/junit.xml`: resultado JUnit cuando se utiliza el argumento del comando completo.
- `reports/BDDxx-failure.png`: captura si falla un paso de interfaz y el navegador permite obtenerla. El reporte de texto conserva el error aunque una captura falle.

Los archivos `primera-ejecucion.*` conservan el primer intento, con nueve aprobados y un fallo de automatización en BDD02. Un selector demasiado amplio coincidía con el polígono de resaltado antes que con el botón del visor. Se corrigió solamente el selector de prueba; no se cambió la aplicación. El informe `resultados.*` corresponde a la ejecución más reciente.

Los avisos de deprecación de `gherkin-official` sobre `maxsplit` en Python 3.13 son de la dependencia y no se ocultan; no equivalen a un escenario fallido. La comprobación de dependencias se realizó con `pip check`.

## Limitaciones de cobertura

1. Los diez escenarios se automatizan en sus niveles originales. Las tablas de datos de BDD02 y BDD08 se procesan con pytest-bdd 8.1.0. No se sustituyen los pasos de interfaz por comprobaciones exclusivas de API.
2. Los escenarios de interfaz parten del mapa de oficinas y del panel `/dashboard2`. El aislamiento verifica que el mapa urbano permanece intacto, pero no implica cobertura de todos los mapas, paneles o variantes visuales.
3. La previsualización se comprueba dentro de su iframe: textos del borrador, imágenes de recorrido con animación CSS y ausencia de cambios persistidos. El sonido audible depende de las políticas del navegador; no se exige reproducción audible en este piloto.
4. BDD08 requiere solicitudes directas al servicio: el editor normal limita las coordenadas, conserva dos nodos y no permite editar el identificador ni el objeto del catálogo. No sería correcto esperar esos rechazos mediante el uso ordinario de sus controles.
5. BDD09 prepara dos copias antiguas y realiza guardados secuenciales sobre rutas distintas; no promete resolver conflictos sobre la misma ruta. BDD10 prepara mediante el cliente Flask una copia válida y retira después la ruta temporal: el editor individual no ofrece eliminarla. Verifica el contrato API ante datos obsoletos, no un botón de eliminación ni la presentación del error en el navegador.
6. Fallos de red, respuestas no JSON y errores de escritura pueden producir errores capturados por la interfaz, pero no tienen un mensaje español estable ni un punto de inyección preparado. Para escenarios deterministas adicionales habría que simular la red o el almacenamiento; no se han inventado mensajes ni agregado mecanismos.
7. Los controles de carga aceptan `image/*` y `audio/*` como indicaciones del selector de archivos. `/api/upload` comprueba archivo presente y nombre no vacío, pero no valida MIME, contenido ni extensión permitida. Un escenario de rechazo garantizado de un PDF como audio no está respaldado por el código.
8. No existe autenticación ni control de roles implementado en este flujo. No se incluyen inicio de sesión, permisos de administrador ni rechazo por rol.
9. En BDD05 el nombre del modelo se recorta a vacío, aunque el campo DOM conserva visualmente los espacios tecleados. La prueba comprueba el rechazo y el nombre vacío del borrador mediante su previsualización, sin exigir que la app reescriba el campo. Esto conserva el comportamiento real y el objetivo del escenario original.

## Revisión realizada

Se contrastaron los diez escenarios con paneles, editor, visor, previsualización, utilidades y endpoints reales, se implementaron sus pasos y se ejecutó la suite. El resultado definitivo por escenario está en `reports/resultados.md`. No se modificaron los diez escenarios originales ni la lógica de producción.

Referencias de las herramientas: [tablas y Gherkin de pytest-bdd](https://pytest-bdd.readthedocs.io/en/8.1.0/) y [Selenium Manager](https://www.selenium.dev/documentation/selenium_manager/).

## Integración continua con GitHub Actions

El remoto Git configurado es `https://github.com/jefroMMM/PG1-Muni.git`. El workflow `.github/workflows/bdd.yml` se activa en cada `push` y `pull_request`, sin filtros de rama o archivos. También admite ejecución manual desde Actions cuando esté disponible en la rama predeterminada.

Usa `windows-latest`, Python 3.13 y Chrome estable con un ChromeDriver compatible, cuya ruta se entrega a las fixtures existentes mediante `BDD_CHROME_BINARY` y `BDD_CHROMEDRIVER`. Se instala `tests/bdd/requirements.txt` y se ejecuta exactamente el comando completo documentado arriba. La suite ya configura el navegador headless y los datos temporales. No se necesita Docker, un servidor externo ni secretos del repositorio.

El código de salida de pytest determina si el paso aprueba o falla; no se usa `continue-on-error`. `ci_summary.py` comprueba además que estén presentes BDD01–BDD10, que todos aprueben, que la integridad sea satisfactoria y que exista JUnit. Una omisión o ejecución incompleta hace fallar esa comprobación. El resumen se muestra en la página de la ejecución.

La publicación de evidencia usa `if: always()`: conserva los archivos JUnit, Markdown y JSON, el log de pytest, el estado de la verificación y las capturas de fallos disponibles durante 14 días. Solo incluye esas rutas explícitas, sin entornos virtuales, datos municipales, archivos de configuración privada ni reportes históricos locales. Se limpian los resultados anteriores exclusivamente en el checkout efímero del runner, evitando presentar evidencia antigua como una ejecución nueva. Si falla la preparación antes de pytest, no habrá reportes de pruebas que todavía no se generaron; el resumen explica que la ejecución quedó incompleta.

`tests/bdd/.gitignore` excluye los reportes generados y la caché local de pytest del control de versiones; no elimina esos archivos. La evidencia de CI se descarga desde Actions como artifact.

Las acciones están fijadas a commits verificados y el workflow solo solicita `contents: read`. El código se obtiene del archivo del SHA exacto mediante la API de GitHub, sin inicializar el gitlink histórico ni guardar credenciales en Git. No se publica el sitio ni se modifica el repositorio remoto desde el workflow.

Para activarlo, una persona con acceso al repositorio debe revisar y registrar el workflow y los archivos necesarios de la suite: `conftest.py`, `test_edicion_rutas.py`, `pytest.ini`, `requirements.txt`, `ci_summary.py`, el `.feature` original y esta documentación. También deben estar versionados el backend, frontend y semilla que usan las pruebas. Revisar los archivos individualmente: hay cambios locales ajenos a este laboratorio y no corresponde agregarlos todos indiscriminadamente. No hace falta subir `.venv-bdd`, reportes históricos, datos locales modificados ni archivos privados.

Después de subir los cambios a una rama, habilitar GitHub Actions en la configuración del repositorio si está desactivado y permitir las acciones utilizadas. Revisar la ejecución `Laboratorio BDD` en Actions y descargar su artifact. La verificación final requiere una ejecución real de esa revisión en GitHub; una validación local del YAML y una suite local aprobada no demuestran por sí solas que el workflow funcione en el runner remoto.

Referencias: [setup-chrome y sus salidas](https://github.com/browser-actions/setup-chrome), [conservación de artifacts](https://github.com/actions/upload-artifact) y [setup-python](https://github.com/actions/setup-python).
