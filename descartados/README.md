# Archivos fuera de la aplicacion activa

Este directorio conserva archivos historicos. Flask no los publica y Docker no
los incluye en la imagen ni en su contexto de construccion.

| Carpeta | Contenido y motivo |
| --- | --- |
| `versiones/` | Clasmorfismo, Glaymorfismo, Minimalismo, LiquidGlass, fork-core y el checkout anterior. Sus URLs fueron retiradas. |
| `lanzadores/` | v1.py, v2.py e index.html de apertura directa. Dependian de versiones antiguas o de abrir HTML sin servidor. |
| `experimentos/` | Juego medieval independiente de los mapas municipales. |
| `recursos-no-utilizados/` | Imagenes que ya estaban identificadas como no utilizadas. |
| `evidencias-generadas/` | Renderizados anteriores de documentos. |
| `entregas-historicas/` | Copia empaquetada de las pruebas BDD. Las pruebas vigentes siguen en tests/bdd. |
| `estilos/` | CSS de depuracion retirado del visor y mapar.css, que no era cargado por ninguna pantalla actual. |
| `recursos-previos/` | Ubicaciones originales de imagenes y audios antes de migrarlos a data/recursos. Se conservan como respaldo. |
| `documentacion/` | Entregables, diagramas y evidencias documentales; no son necesarios para ejecutar la aplicacion. |
| `laboratorio-bdd/` | Suite BDD, reportes, workflow de GitHub Actions y entorno virtual retirados del proyecto activo. |

Los archivos se trasladaron, no se eliminaron. Las referencias relativas dentro
de las versiones historicas se conservan como evidencia, no como aplicaciones
publicadas. Las herramientas de generacion permanecen en tools y conservan sus
rutas anteriores de salida para documentacion.

El workflow BDD archivado ya no esta en .github/workflows. El entorno virtual
se conserva como respaldo; sus lanzadores pueden mantener rutas absolutas de su
ubicacion anterior y no debe asumirse que sea portable. La entrega de dos pruebas
permanece en entregas-historicas/entrega_bdd. Los archivos del laboratorio conservan
sus referencias historicas, no instrucciones vigentes del proyecto.
