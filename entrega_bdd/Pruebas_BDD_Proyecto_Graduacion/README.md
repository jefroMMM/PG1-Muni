# Dos pruebas BDD del proyecto de graduación

Pruebas con Python, pytest-bdd y Selenium sobre el proyecto municipal PG1-Muni:

1. **Crear ruta:** abre Nueva ruta en otra pestaña, escribe nombre e indicaciones,
   conserva los dos nodos iniciales, guarda y comprueba la ruta en el panel y al
   abrirla nuevamente.
2. **Editar ruta:** abre una ruta de la semilla temporal en otra pestaña, modifica
   nombre e indicaciones, guarda y recarga para comprobar la persistencia.

Ambas leen también el JSON temporal guardado y comprueban que las otras rutas
se conservan. No utilizan la instancia habitual ni los datos reales.

## Requisitos y ejecución

Necesitas Python 3.10 o posterior, Google Chrome y una copia del proyecto PG1-Muni
que incluya backend, frontend y data/routes-config.default.json. Esta entrega
contiene las pruebas independientes del laboratorio anterior; no incluye la
aplicación ni datos municipales. No hace falta Docker ni iniciar Flask manualmente.

Descomprime el ZIP. Desde la carpeta que contiene este README, en PowerShell:

```powershell
$env:BDD_PROJECT_ROOT = 'C:\ruta\PG1-Muni'
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest --confcutdir=. -p no:cacheprovider -v test_rutas.py
```

Sustituye la ruta del proyecto. Si esta carpeta está dentro de PG1-Muni,
BDD_PROJECT_ROOT puede omitirse: se busca el proyecto en las carpetas superiores.
`--confcutdir=.` evita cargar las fixtures del laboratorio anterior si se ubica
la entrega dentro de tests/bdd. Se ejecutan exactamente dos escenarios.

Selenium Manager obtiene ChromeDriver si es necesario; su primera descarga
requiere Internet. Para usar ejecutables ya disponibles, antes de pytest:

```powershell
$env:BDD_CHROME_BINARY = 'C:\ruta\chrome.exe'
$env:BDD_CHROMEDRIVER = 'C:\ruta\chromedriver.exe'
```

Chrome y ChromeDriver deben tener versiones compatibles. El navegador se ejecuta
en modo headless. Las esperas son explícitas, sin pausas fijas.

## Aislamiento

conftest.py reutiliza y simplifica las fixtures de tests/bdd/conftest.py y los
patrones Selenium de test_edicion_rutas.py. Cada escenario copia la semilla a una
carpeta temporal, sustituye CONFIG_PATH y UPLOAD_DIR con monkeypatch e inicia
Flask en 127.0.0.1 con puerto libre. Chrome usa un perfil temporal nuevo.
Al finalizar se cierran navegador y servidor y se restauran las referencias.
Una fixture verifica los hashes de los datos originales y las cargas existentes.
No ejecutar en paralelo: las referencias del módulo Flask son globales.

Los dos archivos .feature contienen un escenario cada uno. test_rutas.py comparte
los pasos comunes; no depende de importar las pruebas del laboratorio anterior.

## Resultado comprobado

Ejecución local el 19 de octubre de 2026 con Python 3.13.14 y Chrome headless:
`2 passed in 11.86s` (cero fallidas u omitidas). La comprobación de integridad de
los datos originales también aprobó. No fue necesario instalar dependencias.
