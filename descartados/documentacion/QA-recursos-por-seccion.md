# QA: recursos por seccion

Fecha: 2026-10-29.

## Resultado

55 pruebas automatizadas aprobadas:

| Suite | Casos | Resultado |
| --- | ---: | --- |
| API, persistencia, archivos y migracion | 33 | Aprobados |
| Funciones compartidas JavaScript | 7 | Aprobados |
| Escenarios BDD | 10 | Aprobados |
| Navegador Selenium | 5 | Aprobados |

## Migracion real

- 25 archivos migrados a data/recursos: 26.250.285 bytes en total.
- Los hashes SHA256 de todos los archivos coinciden con sus originales.
- Los 25 archivos se descargaron por HTTP y se compararon con el contenido local.
- Las 9 rutas existentes conservan sus datos; solo cambian las URLs de los medios.
- La configuracion inicial y la configuracion actual fueron actualizadas.
- Los originales permanecen en descartados/recursos-previos.
- Respaldo previo: data/backups/recursos-20261029T170752305003Z.
- Segunda ejecucion de la migracion: 0 archivos y 0 configuraciones pendientes.

## Funcionalidad comprobada

- Fondos compartidos; assets, audios, iconos y decoraciones por seccion.
- Logo municipal en iconos/Compartidos.
- Filtro de recursos propios y compartidos frente a todas las secciones.
- Conservacion de recursos de otras secciones que ya esten asignados.
- Creacion de una seccion desde dashboard2 y creacion de sus cuatro carpetas.
- Subida real desde el navegador de assets, audio, fondo, icono y decoracion.
- Catalogo registrado en el servidor y guardado de una ruta nueva.
- Visor publico de la nueva seccion con sus recursos disponibles.
- Seleccion automatica del icono o decoracion que acaba de subirse.
- Guardados de configuraciones antiguas conservan las nuevas cargas del catalogo.
- URLs antiguas redirigen; payloads antiguos se normalizan a las nuevas URLs.
- Extensiones y secciones invalidas rechazadas sin guardar archivos.
- Acceso a rutas fuera de la biblioteca y archivos .gitkeep rechazado.
- Rutas numericas retiradas y contenido descartado siguen fuera de la app publica.

## Docker y persistencia

Se reconstruyo y reinicio el servicio terminal-muni. Despues del reinicio:

- GET /api/config devuelve resourceSchemaVersion 1.
- El hash del JSON persistente coincide con el anterior al reinicio.
- El audio admite peticiones Range y responde HTTP 206.
- Visores, editores y dashboard2 responden HTTP 200.
- Los recursos y el JSON siguen dentro del volumen ./data:/app/data.
- Los respaldos y descartados quedan fuera de la imagen de Docker.

SHA256 del JSON al cerrar la validacion:

```text
37b103b42b398d7a5adcee5790fb0a025ea2841607f0ebb9f6cbb407c2eb4030
```

## Evidencia y repeticion

Capturas de escritorio y movil en tests/ui/reports, incluyendo
resource-library-all.png y resource-library-mobile.png. Los reportes son locales
y se excluyen de Git. Las pruebas de navegador usan configuracion y archivos
temporales; no crean secciones ni cargas de prueba en los datos reales.

```sh
python -m unittest discover -s tests -p "test_*.py"
node --test tests/js/shared.test.mjs
python -m pytest -c tests/bdd/pytest.ini tests/bdd -q
python -m pytest tests/ui/test_editor_ui.py -q
python tools/migrate_resources.py
```

El ultimo comando solo inspecciona. Para aplicar una migracion pendiente se usa
--apply, que crea el respaldo antes de modificar los JSON.
