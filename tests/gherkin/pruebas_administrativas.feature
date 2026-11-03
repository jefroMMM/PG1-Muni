# language: es
Característica: Administración de secciones y rutas con datos de prueba
  Todas las operaciones utilizan una copia temporal de los datos del proyecto.

  Escenario: Crear una sección correctamente
    Dado que el administrador está en el panel de pruebas
    Cuando crea una sección llamada "Servicios de prueba Gherkin"
    Entonces la sección aparece en el panel y queda guardada sin cambiar los mapas anteriores

  Escenario: Rechazar una sección con nombre demasiado largo
    Dado que existe un sistema de pruebas con datos iniciales
    Cuando se solicita por API crear una sección con un nombre de 81 caracteres
    Entonces se rechaza la solicitud y los datos permanecen iguales

  Escenario: Cargar y guardar el fondo de un mapa
    Dado que el administrador abre la configuración del mapa de oficinas
    Cuando carga un croquis y guarda el fondo
    Entonces el fondo permanece al recargar y el archivo cargado coincide con el original

  Escenario: Crear una ruta correctamente
    Dado que el administrador está en el panel de pruebas
    Cuando abre Nueva ruta y guarda "Ruta de prueba Gherkin" con dos puntos iniciales
    Entonces la nueva ruta queda guardada y puede abrirse desde el panel

  Escenario: Editar una ruta existente
    Dado que el administrador abre una ruta existente en su editor
    Cuando cambia su nombre a "Ruta modificada Gherkin" y escribe nuevas indicaciones
    Entonces los cambios permanecen al recargar sin modificar las otras rutas y mapas

  Escenario: Rechazar una ruta sin nombre
    Dado que el administrador abre una ruta existente en su editor
    Cuando intenta guardar un nombre que solo contiene espacios
    Entonces aparece el rechazo y se conservan los datos previamente guardados

  Escenario: Guardar varias indicaciones para una ruta
    Dado que el administrador abre una ruta existente en su editor
    Cuando escribe y guarda tres pasos de indicaciones
    Entonces los tres pasos permanecen en el editor y se muestran al visitante

  Escenario: Cargar un audio y asociarlo a una ruta
    Dado que el administrador abre una ruta existente en su editor
    Cuando carga el audio de prueba y guarda la ruta
    Entonces el audio queda asociado después de recargar y se entrega sin cambios

  Escenario: Archivar una ruta y ocultarla al visitante
    Dado que el administrador ve una ruta visible en el panel de pruebas
    Cuando pulsa Archivar para esa ruta
    Entonces queda archivada en el panel y no aparece como botón en el visor público

  Escenario: Restaurar una ruta archivada
    Dado que el administrador ve una ruta archivada en el panel de pruebas
    Cuando pulsa Restaurar para esa ruta
    Entonces queda visible en el panel y vuelve a aparecer como botón en el visor público
