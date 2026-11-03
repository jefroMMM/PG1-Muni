# language: es
Característica: Creación de rutas del mapa de oficinas
  Escenario: Crear una ruta y comprobar su persistencia
    Dado que el administrador está en el panel de rutas del mapa de oficinas
    Cuando selecciona Nueva ruta
    Y se abre el editor en una nueva pestaña
    Y escribe un nombre y unas indicaciones
    Y conserva los dos nodos iniciales
    Y presiona Guardar
    Entonces el sistema confirma el guardado
    Y la ruta aparece en el panel administrativo
    Y al abrirla nuevamente los datos se mantienen
