const mode = name => cy.get(`[data-mode="${name}"]`).click();
const fill = (selector, value) => cy.get(selector).clear().type(value);
const save = () => {
  cy.get('#saveButton').click();
  cy.get('#saveStatus').should('have.text', 'Guardado');
};

function followEditor(selector) {
  cy.get(selector).should('have.attr', 'target', '_blank');
  cy.get(selector).invoke('removeAttr', 'target').click();
  cy.get('#routeNameInput, #backgroundSelect').filter(':visible').should('exist');
}

function node(index, x, y) {
  for (const [axis, value] of Object.entries({ x, y })) {
    cy.get(`[data-node-index="${index}"][data-axis="${axis}"]`)
      .clear().type(String(value)).blur();
  }
}

describe('E2E — configuración municipal desde el navegador', () => {
  beforeEach(() => cy.task('reset'));

  it('E2E01 crea sección, carga croquis y audio, dibuja ruta y conserva su configuración', () => {
    let key, routeId, background, audio;
    const steps = ['Ingrese por el acceso inferior.', 'Avance por el pasillo y gire a la derecha.'];
    cy.visit('/dashboard2');
    cy.get('#newSectionButton').click();
    fill('#sectionName', 'Servicios de prueba Seminario');
    cy.intercept('POST', '/api/maps').as('section');
    cy.get('#createSectionButton').click();
    cy.wait('@section').then(({ response }) => {
      expect(response.statusCode).to.eq(201);
      key = response.body.mapKey;
      cy.location('hash').should('eq', `#${key}`);
      followEditor(`#${key} .configure-map`);
    });
    cy.intercept('POST', '/api/upload').as('upload');
    cy.get('#backgroundUploadInput').selectFile('fixtures/croquis.png');
    cy.wait('@upload').then(({ response }) => {
      expect(response.statusCode).to.eq(201);
      background = response.body.src;
    });
    cy.get('#editorMapImage').should($img => expect($img[0].naturalWidth).to.be.greaterThan(0));
    save();
    cy.screenshot('E2E01-fondo-guardado');
    cy.get('#backLink').click();
    cy.then(() => followEditor(`#${key} .new-route-link`));
    fill('#routeNameInput', 'Atención al vecino');
    cy.get('#instructionStepList textarea').first().clear().type(steps[0]);
    cy.get('#addInstructionStepButton').click();
    cy.get('#instructionStepList textarea').last().type(steps[1]);
    cy.get('#routeColorInput').invoke('val', '#2563eb').trigger('input');
    fill('#routeDurationInput', '15');
    cy.task('audioPath').then(file => cy.get('#audioUploadInput').selectFile(file));
    cy.wait('@upload').then(({ response }) => {
      expect(response.statusCode).to.eq(201);
      audio = response.body.src;
      cy.get('#routeAudioSelect').should('have.value', audio);
    });
    mode('nodes');
    node(0, 1000, 900);
    node(1, 1000, 300);
    cy.get('#addNodeButton').click();
    cy.get('#editorLayer').click('center');
    cy.get('#nodeList .node-row').should('have.length', 3);
    node(2, 1700, 300);
    cy.get('#editorRoutePath').should('have.attr', 'd').and('include', '1700');
    save();
    cy.location('search').then(search => { routeId = new URLSearchParams(search).get('route'); });
    cy.task('saved').then(config => {
      const map = config.maps[key], route = map.routes[0];
      expect(map.background).to.eq(background);
      expect(route).to.include({ name: 'Atención al vecino', buttonColor: '#2563eb', audio, durationSeconds: 15 });
      expect(route.instructionSteps).to.deep.eq(steps);
      expect(route.nodes).to.deep.eq([{ x: 1000, y: 900 }, { x: 1000, y: 300 }, { x: 1700, y: 300 }]);
    });
    cy.screenshot('E2E01-recorrido-guardado');
    cy.reload();
    cy.get('#routeNameInput').should('have.value', 'Atención al vecino');
    cy.get('#routeColorInput').should('have.value', '#2563eb');
    cy.get('#instructionStepList textarea').should('have.length', 2);
    cy.get('#instructionStepList textarea').first().should('have.value', steps[0]);
    cy.get('#instructionStepList textarea').last().should('have.value', steps[1]);
    cy.then(() => cy.get('#routeAudioSelect').should('have.value', audio));
    cy.then(() => cy.visit(`/maps/${key}`));
    cy.get('#mapImage').should($img => expect($img[0].naturalWidth).to.be.greaterThan(0));
    cy.then(() => cy.get(`#routeControls button[data-route-id="${routeId}"]`)
      .should('have.css', 'background-color', 'rgb(37, 99, 235)').click());
    cy.get('#panelContent').should('contain', steps[0]).and('contain', steps[1]);
    cy.get('#routeFootprints').children().should('have.length.greaterThan', 0);
    cy.then(() => cy.request({ url: audio, encoding: 'binary' })).then(response => {
      expect(response.status).to.eq(200);
      cy.task('audioPath').then(file => cy.readFile(file, 'binary').should('eq', response.body));
    });
    cy.screenshot('E2E01-vista-publica');
  });

  it('E2E02 rechaza nombre vacío, conserva lo guardado y permite corregir', () => {
    let initial;
    cy.task('saved').then(config => { initial = config; });
    cy.visit('/dashboard2#terminal');
    followEditor('#terminal .edit-link:first');
    cy.get('#routeNameInput').clear().type('   ');
    cy.intercept('PATCH', '/api/maps/terminal/routes/*').as('save');
    cy.get('#saveButton').click();
    cy.wait('@save').its('response.statusCode').should('eq', 400);
    cy.get('#saveStatus').should('contain', 'La ruta necesita nombre');
    cy.get('#saveButton').should('be.enabled');
    cy.task('saved').then(config => expect(config).to.deep.eq(initial));
    cy.screenshot('E2E02-rechazo-visible');
    fill('#routeNameInput', 'Nombre corregido Seminario');
    save();
    cy.reload();
    cy.get('#routeNameInput').should('have.value', 'Nombre corregido Seminario');
    cy.task('saved').then(config => expect(config.maps.terminal.routes[0].name).to.eq('Nombre corregido Seminario'));
  });
});
