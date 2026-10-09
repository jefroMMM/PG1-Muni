# language: es
@edicion_rutas @piloto
Característica: Edición de rutas desde el panel administrativo
  Como personal de TI de la Municipalidad de Retalhuleu
  Quiero actualizar una ruta existente desde su editor individual
  Para mantener la orientación al visitante sin alterar otros recorridos ni el mapa

  # Cada escenario usa datos aislados preparados desde la configuración predeterminada.
  # Los escenarios API comprueban el contrato utilizado por el editor individual.
  # Las etiquetas identifican el aporte principal de los tres amigos, no su autor exclusivo.

  @BDD01 @negocio @interfaz @exitoso
  Escenario: Abrir el editor individual de una ruta desde el panel
    Dado que el panel administrativo "/dashboard2" muestra una ruta existente del mapa de oficinas
    Cuando el personal pulsa "Editar" en esa ruta
    Entonces se abre una nueva pestaña con el identificador de esa ruta y el parámetro "scope=route"
    Y se muestran sus datos guardados y los modos "Nodos", "Assets" y "Texto y audio"
    Y se ofrece la acción "Archivar" o "Desarchivar" según el estado de la ruta
    Y están ocultos los modos "Mapa", "Iconos" y "Decoraciones"
    Y están ocultas las acciones para crear, duplicar y borrar rutas

  @BDD02 @negocio @interfaz @exitoso
  Escenario: Guardar los campos y el recorrido de una ruta existente
    Dado que una ruta visible está abierta desde el panel en su editor individual
    Y que su catálogo contiene el recurso de recorrido "footprints-auto"
    Cuando el personal modifica sus campos con estos valores
      | campo                    | valor                                  |
      | Nombre                   | Atención al vecino                     |
      | Color de boton           | #158b8f                                |
      | Indicaciones             | Avance por el pasillo. Gire a la derecha. |
      | Audio de esta ruta       | Sin audio                              |
      | Tamano de assets         | 48                                     |
    Y agrega un nodo en las coordenadas 1200 y 700
    Y mueve el primer nodo a las coordenadas 900 y 650
    Y asigna el recurso "footprints-auto" al primer tramo
    Y pulsa una vez "Espejo" y una vez la rotación del primer tramo inicialmente sin transformaciones
    Y pulsa "Guardar"
    Entonces el estado del editor muestra "Guardado"
    Y al recargar el editor se conservan los campos y nodos modificados
    Y el primer tramo conserva el recurso elegido, el efecto espejo y una rotación de 45 grados
    Y al seleccionar la ruta en el visor se muestran el nuevo nombre y las nuevas indicaciones
    Y el fondo, los iconos, las decoraciones y las demás rutas permanecen como estaban

  @BDD03 @negocio @interfaz @exitoso
  Escenario: Archivar y volver a habilitar una ruta para los visitantes
    Dado que una ruta visible está abierta en su editor individual
    Cuando el personal pulsa "Archivar" y guarda la ruta
    Entonces al recargar el visor no aparece el botón de esa ruta
    Y el panel administrativo sigue mostrando la ruta con estado "Archivada"
    Cuando el personal vuelve a abrir esa ruta desde el panel, pulsa "Desarchivar" y guarda
    Entonces al recargar el visor vuelve a aparecer el botón de esa ruta
    Y el panel administrativo muestra la ruta con estado "Visible" al actualizarse

  @BDD04 @negocio @interfaz @exitoso
  Escenario: Previsualizar un borrador sin guardar la ruta
    Dado que una ruta existente está abierta en su editor individual
    Y que el personal cambia el nombre a "Recorrido en revisión" y las indicaciones a "Siga el recorrido de prueba."
    Cuando pulsa "Previsualizar ruta"
    Entonces la vista previa muestra el recorrido animado y los textos del borrador
    Y la configuración persistida conserva el nombre y las indicaciones anteriores
    Cuando pulsa "Volver a editar"
    Entonces el editor conserva el borrador y muestra "Cambios sin guardar"

  @BDD05 @qa @interfaz @negativo
  Escenario: Rechazar el guardado de un nombre formado únicamente por espacios
    Dado que una ruta existente está abierta en su editor individual
    Cuando el personal reemplaza el nombre por tres espacios y pulsa "Guardar"
    Entonces la solicitud de actualización recibe el código HTTP 400
    Y el editor muestra "La ruta necesita nombre y al menos dos nodos dentro del mapa"
    Y el botón "Guardar" vuelve a estar habilitado
    Y la configuración persistida conserva la ruta anterior
    Y el editor conserva el nombre vacío resultante de quitar los espacios

  @BDD06 @qa @interfaz @limite
  Escenario: Conservar los dos nodos mínimos al borrar el último nodo
    Dado que una ruta abierta en su editor individual tiene exactamente tres nodos
    Cuando el personal pulsa "Borrar ultimo" en el modo "Nodos"
    Entonces la ruta queda con dos nodos y un tramo
    Cuando vuelve a pulsar "Borrar ultimo"
    Entonces se conservan los mismos dos nodos y el mismo tramo
    Cuando pulsa "Guardar"
    Entonces el editor muestra "Guardado"
    Y al recargar la ruta conserva esos dos nodos

  @BDD07 @qa @interfaz @limite
  Escenario: Ajustar las coordenadas introducidas a los límites del mapa
    Dado que una ruta existente está abierta en su editor individual
    Cuando el personal introduce -1 en X y 1001 en Y del primer nodo y confirma cada cambio
    Y introduce 2001 en X y -1 en Y del segundo nodo y confirma cada cambio
    Entonces el primer nodo queda en las coordenadas 0 y 1000
    Y el segundo nodo queda en las coordenadas 2000 y 0
    Cuando pulsa "Guardar"
    Entonces el editor muestra "Guardado"
    Y al recargar se conservan las coordenadas ajustadas en los bordes del mapa

  @BDD08 @qa @api @negativo
  Escenario: Rechazar datos inválidos enviados al servicio de edición
    Dado que existe una ruta válida en una configuración aislada
    Cuando se envía por separado cada una de estas modificaciones al servicio PATCH de esa ruta
      | modificación del cuerpo de la solicitud                       | código | mensaje                                                        |
      | falta el objeto route                                        | 400    | Ruta invalida                                                  |
      | el id de route difiere del identificador de la URL            | 400    | La ruta necesita nombre y al menos dos nodos dentro del mapa    |
      | nodes contiene un solo nodo                                  | 400    | La ruta necesita nombre y al menos dos nodos dentro del mapa    |
      | el primer nodo tiene x igual a -1                             | 400    | La ruta necesita nombre y al menos dos nodos dentro del mapa    |
      | el primer nodo tiene y igual a 1001                           | 400    | La ruta necesita nombre y al menos dos nodos dentro del mapa    |
      | el primer nodo tiene x como texto JSON en vez de número       | 400    | La ruta necesita nombre y al menos dos nodos dentro del mapa    |
      | catalog.audios es un objeto en vez de una lista               | 400    | Catalogo invalido                                              |
    Entonces cada respuesta contiene el código y el mensaje indicados
    Y después de cada solicitud la configuración persistida permanece intacta

  @BDD09 @desarrollo @api @exitoso
  Escenario: Conservar las modificaciones de dos rutas editadas desde copias antiguas
    Dado que dos editores individuales cargaron la misma configuración con dos rutas distintas
    Y que el primer editor cambia el nombre de la primera ruta
    Y que el segundo editor cambia las indicaciones de la segunda ruta sin recargar la configuración
    Cuando se guarda primero la primera ruta y después la segunda mediante sus solicitudes PATCH
    Entonces ambas respuestas tienen código HTTP 200 y el campo ok igual a verdadero
    Y la configuración persistida contiene el nuevo nombre de la primera ruta y las nuevas indicaciones de la segunda
    Y se conservan los fondos, los iconos, las decoraciones y las rutas de los demás mapas

  @BDD10 @desarrollo @api @negativo
  Escenario: Informar que la ruta desapareció después de abrir su editor
    Dado que el editor individual cargó una ruta válida de un mapa existente
    Y que un cambio externo en la configuración aislada eliminó únicamente esa ruta
    Y que se registró la configuración persistida después de esa eliminación
    Cuando se envía la solicitud PATCH de guardado con los datos válidos del editor y el identificador original
    Entonces el servicio responde con código HTTP 404 y el mensaje "Ruta no encontrada"
    Y la configuración persistida permanece igual a la registrada después de la eliminación
    Y no se vuelve a crear la ruta eliminada
