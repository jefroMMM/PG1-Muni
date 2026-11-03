# Guion de demostración en clase

Duración orientativa: 8 a 10 minutos. Presentar el PDF junto con los archivos
de código; no se requiere video ni CI.

1. **Contexto, un minuto.** El proyecto orienta visitantes mediante mapas y rutas.
   El personal administra secciones, fondos, recorridos, indicaciones y audio.
   El riesgo es publicar un recorrido incorrecto o perder datos durante cambios.
2. **Diseño, un minuto.** Mostrar los tres diagramas del informe. Explicar que
   Flask y la persistencia ya existían; lo añadido es su verificación con Cypress.
3. **E2E, dos minutos.** Mostrar e2e.cy.js: creación de sección, carga del croquis,
   nombre, pasos, color, nodos y MP3. Señalar que intercept solo observa respuestas.
   Ejecutar run.py --aporte e2e y mostrar capturas y resumen.
4. **API Testing, dos minutos.** Mostrar api.cy.js: solicitud, estado, cuerpo y
   archivo guardado. Ejecutar run.py --aporte api. Explicar límites inclusivos,
   duplicado 409, objetivo ausente 404 e inválido 400.
5. **Detección de fallos, un minuto.** Ejecutar --aporte api --defecto-controlado.
   Mostrar que API03 detecta aceptar un nombre vacío. Es una regresión simulada
   únicamente en memoria del proceso temporal, no una edición de producción.
6. **Cierre técnico, un minuto.** Mostrar integridad.json, limitaciones y el
   comando normal. El ensayo con defecto falla por diseño y no sustituye la
   ejecución correcta. Identificar los archivos nuevos y la versión entregada.

## Preguntas que hay que poder responder

- **¿Son pruebas unitarias?** No. El E2E cubre interfaz y backend; API Testing
  verifica directamente contratos HTTP del mismo sistema.
- **¿Por qué una herramienta para dos aportes?** La rúbrica diferencia enfoques
  y objetivos. El E2E verifica interacción y representación; API Testing cubre
  reglas, límites y errores sin depender de los controles web.
- **¿Se simula que el servidor responde bien?** No. Solo la ejecución explícita
  con defecto debilita una regla para demostrar que se detecta el problema.
- **¿Dónde se guardan los datos?** En un directorio temporal propio de la ejecución.
- **¿Se probó que el audio suena?** Se probó su carga, asociación y entrega exacta;
  la percepción acústica y el hardware requieren revisión manual.
- **¿Se validan pestañas?** Se comprueba target=_blank, pero Cypress sigue el
  enlace en una pestaña; no se afirma cobertura de múltiples pestañas.
- **¿Qué mejora se demuestra?** Verificación reproducible de estos riesgos. No
  se afirma un porcentaje de mejora ni un aumento de rendimiento sin medirlo.
- **¿Quién hizo qué?** Completar con las contribuciones reales de cada integrante;
  este documento no atribuye tareas a personas sin información del equipo.
