# language: es
Característica: Edición de rutas del mapa de oficinas
  Escenario: Editar una ruta y comprobar su persistencia
    Dado que existe una ruta en el sistema de pruebas
    Cuando el administrador selecciona Editar
    Y se abre el editor en una nueva pestaña
    Y modifica el nombre y las indicaciones
    Y presiona Guardar
    Entonces el sistema confirma el guardado
    Y al recargar el editor los cambios permanecen guardados
