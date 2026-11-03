# Fuentes editables de los diagramas

Estos diagramas describen la versión local analizada para Seminario. Se pueden
editar como Mermaid y visualizar en GitHub o un editor compatible. El informe
PDF incluye representaciones equivalentes de arquitectura, datos y secuencia.

## Arquitectura y participación de los dos aportes

```mermaid
flowchart TB
  E["Aporte 1 Cypress E2E"] --> UI["Frontend HTML CSS JavaScript"]
  UI -->|fetch HTTP| API["Flask API y páginas"]
  T["Aporte 2 API Testing cy.request"] -->|HTTP real| API
  API --> V["Validación de rutas y catálogos"]
  API --> S["ConfigStore JSON atómico y caché local"]
  API --> R["ResourceLibrary recursos por sección"]
  S --> D["JSON temporal durante las pruebas"]
  R --> F["Croquis y audio temporales"]
  R -. "Solo lectura de medios de la semilla" .-> B["data/recursos original"]
  RUN["run.py servidor local puerto libre"] --> API
  RUN --> H["Hashes antes y después de data"]
  E --> EV["Capturas JUnit resumen logs"]
  T --> EV
```

En uso habitual, ConfigStore apunta a data/routes-config.json. En estas pruebas
se inyecta otra instancia, con rutas temporales, mediante create_app. No hay
servicios cloud, base SQL, Redis ni proveedor externo en estos recorridos.

## Modelo de datos lógico

```mermaid
erDiagram
  CONFIGURACION ||--|{ SECCION : contiene
  SECCION ||--o{ RUTA : agrupa
  RUTA ||--|{ NODO : ordena
  RUTA ||--o{ PASO_INDICACION : muestra
  CONFIGURACION ||--o{ RECURSO : cataloga
  RUTA }o--o| RECURSO : audio
  SECCION }o--|| RECURSO : fondo
  RUTA }o--o{ RECURSO : assets_por_tramo
  CONFIGURACION {
    object maps
    object catalog
  }
  SECCION {
    string key
    string sectionName
    string background
    array routes
  }
  RUTA {
    string id
    string name
    boolean archived
    string buttonColor
    array instructionSteps
    number durationSeconds
    string audio
  }
  NODO {
    integer posicion
    number x
    number y
  }
  PASO_INDICACION {
    integer posicion
    string texto
  }
  RECURSO {
    string id
    string src
    string name
    string sectionId
  }
```

Es un modelo lógico de objetos y arreglos JSON, no tablas ni claves foráneas SQL.
Una ruta requiere al menos dos nodos; Mermaid no expresa ese mínimo exacto.
X admite 0..2000 e Y 0..1000. durationSeconds, si se envía, admite 3..3600.
Nombre de ruta no vacío; identificador único dentro del mapa al crear.
Las relaciones a recursos no implican una validación exhaustiva de referencias:
el servidor no comprueba toda asociación como lo haría una base relacional.

## Secuencia del proceso crítico

```mermaid
sequenceDiagram
  participant E as Cypress E2E
  participant U as Panel y editor
  participant A as Flask API
  participant S as JSON y recursos temporales
  participant T as API Testing
  E->>U: Nueva sección nombre e icono
  U->>A: POST /api/maps
  A->>S: Crear sección y carpetas
  A-->>U: 201 mapKey
  E->>U: Cargar croquis y guardar fondo
  U->>A: POST /api/upload y PATCH /api/maps/id
  A->>S: Registrar archivo y fondo
  E->>U: Nueva ruta nodos texto color audio
  U->>A: POST /api/upload y POST /api/maps/id/routes
  A->>S: Validar y persistir
  A-->>U: 201 ok
  E->>U: Recargar editor y abrir visor
  U->>A: GET /api/config y recursos
  A-->>U: Datos persistidos y medios
  E->>S: Comprobar JSON temporal mediante task
  Note over T,S: API Testing usa otro estado inicial restablecido
  T->>A: Solicitud inválida de creación
  A-->>T: 400 error
  T->>S: Comprobar que no hubo cambios
```
