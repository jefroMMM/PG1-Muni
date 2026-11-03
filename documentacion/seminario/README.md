# Entrega de Seminario

Abrir **Informe_Seminario_E2E_API.pdf**. Está preparado sin carátula, con análisis,
diseño, tres diagramas, justificación de los dos aportes, implementación, resultados,
limitaciones y correspondencia con la rúbrica.

- `informe.md`: fuente editable del informe.
- `diagramas.md`: fuentes Mermaid editables de arquitectura, datos y secuencia.
- `diagramas/*.svg`: diagramas vectoriales para incluir en otros documentos.
- `evidencias/resultados.md`: resultado por escenario.
- `evidencias/normal/`: ocho pruebas aprobadas, JUnit, log, integridad y capturas.
- `evidencias/defecto-controlado/`: cinco API aprobadas y una fallida por diseño,
  demostrando detección de una regresión temporal de validación.
- `guion-demostracion.md`: guía para exponer y responder preguntas.
- `VERSION.json`: identificación de los archivos locales mediante hashes.

El código nuevo está en `../../tests/seminario/`: `run.py`, `cypress.config.js`,
`e2e.cy.js` y `api.cy.js`, con comentarios en español. Allí están las dependencias,
la configuración de ejemplo y los comandos de ejecución. Se reutiliza el MP3
`Audio de prueba.mp3` de la raíz y se conserva el croquis adjunto como fixture.

## Qué falta para entregar según la rúbrica

1. Añadir la carátula que elaborará el responsable y las contribuciones reales
   de los integrantes, si corresponde. No se inventaron nombres o atribuciones.
2. Revisar y registrar una versión completa del proyecto en GitHub, con acceso
   para el docente. No se hizo commit ni push ni se mezclaron otros trabajos.
   El commit base indicado en VERSION.json no contiene por sí solo esta entrega
   ni todos los cambios locales que necesita el sistema actual.
3. Identificar el commit o etiqueta publicado en la entrega final y comprobar sus
   instrucciones en otra copia del proyecto. Los hashes locales no sustituyen
   esa identificación exigida por la rúbrica.
4. Realizar la demostración en clase. La rúbrica no pide video.

El ZIP complementario contiene estos aportes y documentación, no toda la
aplicación. Para ejecutarlo en otro equipo se necesita la versión correspondiente
del proyecto; se puede extraer conservando su estructura sobre una copia de ella.
No contiene node_modules, entornos virtuales, datos municipales ni el BDD antiguo.
