const routeUrl = '/api/maps/terminal/routes';
const newRoute = () => ({ id: 'ruta-api-seminario', name: 'Ruta API', archived: false,
  instructions: 'Avance a la oficina.', instructionSteps: ['Avance a la oficina.'],
  buttonColor: '#2563eb', audio: '', durationSeconds: 15,
  nodes: [{ x: 0, y: 0 }, { x: 2000, y: 1000 }], segmentAssets: [], segmentOptions: [] });
const request = (method, url, body) => cy.request({ method, url, body, failOnStatusCode: false });

describe('API Testing — contratos y persistencia de rutas', () => {
  let initial;
  beforeEach(() => cy.task('reset').then(config => { initial = config; }));

  it('API01 crea una ruta en los límites, consulta su contenido y rechaza ID duplicado', () => {
    const route = newRoute();
    request('POST', routeUrl, { route }).then(response => {
      expect(response.status).to.eq(201);
      expect(response.body).to.deep.eq({ ok: true });
    });
    cy.request('/api/config').then(({ body }) => {
      expect(body.maps.terminal.routes.find(item => item.id === route.id)).to.deep.eq(route);
      expect(body.maps.mapar).to.deep.eq(initial.maps.mapar);
    });
    cy.task('saved').then(config => expect(config.maps.terminal.routes).to.have.length(initial.maps.terminal.routes.length + 1));
    request('POST', routeUrl, { route }).then(response => {
      expect(response.status).to.eq(409);
      expect(response.body.error).to.eq('Esta ruta ya existe');
    });
    cy.task('saved').then(config => expect(config.maps.terminal.routes).to.have.length(initial.maps.terminal.routes.length + 1));
  });

  it('API02 edita una ruta y conserva las otras rutas y mapas', () => {
    const route = { ...initial.maps.terminal.routes[0], name: 'Ruta actualizada API',
      instructions: 'Primera indicación. Segunda indicación.',
      instructionSteps: ['Primera indicación.', 'Segunda indicación.'], buttonColor: '#112233' };
    request('PATCH', `${routeUrl}/${route.id}`, { route }).then(response => {
      expect(response.status).to.eq(200);
      expect(response.body).to.deep.eq({ ok: true });
    });
    cy.request('/api/config').then(({ body }) => {
      expect(body.maps.terminal.routes[0]).to.deep.eq(route);
      expect(body.maps.terminal.routes.slice(1)).to.deep.eq(initial.maps.terminal.routes.slice(1));
      expect(body.maps.mapar).to.deep.eq(initial.maps.mapar);
    });
    cy.task('saved').then(config => expect(config.maps.terminal.routes[0]).to.deep.eq(route));
  });

  it('API03 rechaza nombre vacío, pocos nodos, coordenadas y duración inválidas sin escrituras', () => {
    const variants = [{ name: '   ' }, { nodes: [{ x: 10, y: 10 }] },
      { nodes: [{ x: -1, y: 0 }, { x: 10, y: 10 }] },
      { nodes: [{ x: true, y: 0 }, { x: 10, y: 10 }] },
      { durationSeconds: 2 }, { durationSeconds: 3601 }];
    for (const invalid of variants) {
      request('POST', routeUrl, { route: { ...newRoute(), ...invalid } }).then(response => {
        expect(response.status, JSON.stringify(invalid)).to.eq(400);
        expect(response.body.error).to.eq('La ruta necesita nombre y al menos dos nodos dentro del mapa');
      });
      cy.task('saved').then(config => expect(config).to.deep.eq(initial));
    }
  });

  it('API04 devuelve 404 para mapa o ruta ausentes sin crearlos', () => {
    request('POST', '/api/maps/no-existe/routes', { route: newRoute() }).then(response => {
      expect(response.status).to.eq(404);
      expect(response.body.error).to.eq('Mapa no encontrado');
    });
    request('PATCH', `${routeUrl}/no-existe`, { route: { ...newRoute(), id: 'no-existe' } }).then(response => {
      expect(response.status).to.eq(404);
      expect(response.body.error).to.eq('Ruta no encontrada');
    });
    cy.task('saved').then(config => expect(config).to.deep.eq(initial));
  });

  it('API05 crea sección con nombre de 80 caracteres y rechaza 81', () => {
    request('POST', '/api/maps', { name: 'A'.repeat(80), icon: 'building', template: 'terminal' }).then(response => {
      expect(response.status).to.eq(201);
      expect(response.body.ok).to.eq(true);
      cy.task('saved').then(config => {
        expect(config.maps[response.body.mapKey].sectionName).to.eq('A'.repeat(80));
        expect(config.maps[response.body.mapKey].routes).to.deep.eq([]);
      });
    });
    cy.task('saved').then(before => {
      request('POST', '/api/maps', { name: 'A'.repeat(81) }).then(response => {
        expect(response.status).to.eq(400);
        expect(response.body.error).to.eq('Escribe un nombre de sección de hasta 80 caracteres');
      });
      cy.task('saved').then(after => expect(after).to.deep.eq(before));
    });
  });

  it('API06 rechaza cargas sin archivo y catálogos malformados', () => {
    request('POST', '/api/upload', {}).then(response => {
      expect(response.status).to.eq(400);
      expect(response.body.error).to.eq('Archivo requerido');
    });
    request('POST', routeUrl, { route: newRoute(), catalog: { audios: 'inválido' } }).then(response => {
      expect(response.status).to.eq(400);
      expect(response.body.error).to.eq('Catalogo invalido');
    });
    cy.task('saved').then(config => expect(config).to.deep.eq(initial));
  });
});
