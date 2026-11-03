const { defineConfig } = require('cypress');
const fs = require('node:fs');
const path = require('node:path');

module.exports = defineConfig({
  viewportWidth: 1440,
  viewportHeight: 1000,
  video: false,
  retries: 0,
  allowCypressEnv: false,
  defaultCommandTimeout: 8000,
  screenshotsFolder: path.join(process.env.SEMINARIO_RESULTS || 'results/manual', 'screenshots'),
  reporter: 'junit',
  reporterOptions: { mochaFile: path.join(process.env.SEMINARIO_RESULTS || 'results/manual', 'junit-[hash].xml'), toConsole: true },
  e2e: {
    specPattern: ['e2e.cy.js', 'api.cy.js'],
    supportFile: false,
    setupNodeEvents(on, config) {
      const target = process.env.SEMINARIO_CONFIG;
      const baseline = process.env.SEMINARIO_BASELINE;
      if (!target || !baseline || !process.env.SEMINARIO_RESULTS) {
        throw new Error('Utiliza python tests/seminario/run.py; no ejecutes Cypress contra producción.');
      }
      if (!fs.realpathSync(target).startsWith(fs.realpathSync(require('node:os').tmpdir()) + path.sep)) {
        throw new Error('La configuración de pruebas debe estar en el directorio temporal.');
      }
      on('task', {
        reset() {
          fs.writeFileSync(target, fs.readFileSync(baseline));
          return JSON.parse(fs.readFileSync(baseline, 'utf8'));
        },
        saved() { return JSON.parse(fs.readFileSync(target, 'utf8')); },
        audioPath() { return process.env.SEMINARIO_AUDIO; }
      });
      on('before:browser:launch', (browser, options) => {
        if (browser.family === 'chromium') {
          options.args.push('--window-size=1600,1200', '--force-device-scale-factor=1');
        }
        return options;
      });
      on('after:run', (result) => {
        const summary = {
          cypress: result.cypressVersion, browser: result.browserName,
          browserVersion: result.browserVersion, total: result.totalTests,
          passed: result.totalPassed, failed: result.totalFailed,
          pending: result.totalPending, skipped: result.totalSkipped,
          runs: (result.runs || []).map(run => ({ spec: run.spec.name,
            tests: run.tests.map(test => ({ title: test.title.join(' / '), state: test.state,
              error: test.displayError || null })) }))
        };
        fs.writeFileSync(path.join(process.env.SEMINARIO_RESULTS, 'resumen.json'), JSON.stringify(summary, null, 2));
      });
      return config;
    }
  }
});
