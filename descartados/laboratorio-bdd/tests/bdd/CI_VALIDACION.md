# Validación local de la configuración de CI

Estado: configuración preparada; ejecución real en GitHub Actions pendiente.

## Repositorio

- El directorio es un repositorio Git y la rama local es `main`.
- `origin` apunta a `https://github.com/jefroMMM/PG1-Muni.git`; la consulta Git de su HEAD respondió correctamente.
- La API pública de GitHub respondió 404 al consultar el repositorio sin autenticación. Esa respuesta no permite determinar su visibilidad ni consultar ejecuciones de Actions por esa vía.
- Los archivos de la suite BDD y el workflow no estaban registrados en el commit local al iniciar esta tarea. No se hizo commit, push, publicación ni ejecución remota.

## Comprobaciones realizadas

| Comprobación | Resultado |
|---|---|
| YAML, eventos, expresiones y estructura del workflow con actionlint 1.7.12 | Aprobada; sin errores |
| Sintaxis de los cuatro bloques PowerShell con el parser de PowerShell | Aprobada; sin errores |
| Referencias de las cuatro acciones fijadas a commits | Verificadas mediante sus tags remotos |
| Resumen de CI con ocho variantes de reportes temporales | Aprueba únicamente el caso completo; rechaza fallo, paso omitido, escenario omitido, reporte parcial, integridad fallida, JUnit ausente y JSON ausente |
| Comando completo documentado de pytest en Windows local | 10 aprobados, 0 fallidos, 0 omitidos; 72,15 segundos |
| Integridad de configuración real, semilla, cargas existentes, CSS y Gherkin | Intactos según los hashes de las fixtures |
| Ejecución real del nuevo workflow en GitHub Actions | Pendiente; no se afirma que CI funcione en el runner remoto |

Los veinte avisos de deprecación provienen de `gherkin-official` en Python 3.13; no son fallos de los escenarios. Los resultados de la suite están en `reports/resultados.md`, `reports/resultados.json`, `reports/junit.xml` y `reports/pytest.log`. Esos archivos se conservan localmente y se excluyen de Git.

## Archivos del paso de CI

- `.github/workflows/bdd.yml`: ejecuta la suite en push, pull request y ejecución manual; prepara Python y Chrome, conserva evidencia y comunica el resultado.
- `tests/bdd/ci_summary.py`: comprueba que aprobaron los diez escenarios, que la integridad sea correcta y que exista JUnit; escribe el resumen y un estado JSON.
- `tests/bdd/.gitignore`: evita registrar reportes generados y cachés locales.
- `tests/bdd/README.md`: actualizada con funcionamiento, artifacts, requisitos y activación de CI.
- Este documento: registra el alcance exacto de la validación.

## Activación pendiente

Revisar y registrar únicamente los archivos del laboratorio necesarios, junto con el workflow; evitar incorporar los cambios locales ajenos en configuración municipal, estilos, documentos o juegos. Subirlos cuando el propietario autorice el push, verificar que Actions y las acciones utilizadas estén permitidas, y revisar la ejecución `Laboratorio BDD`. La evidencia que acredita CI operativo será una ejecución real de esos archivos en GitHub y sus artifacts, no este documento de validación local.
