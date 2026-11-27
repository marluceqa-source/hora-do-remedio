/**
 * Configuração do Playwright — testes de API e de WEB do "Hora do Remédio".
 *
 * Três projetos:
 *   api          → testes REST (pilares VADER), sem navegador
 *   setup-portal → cria por API um profissional autenticado e salva a sessão em disco
 *   web          → testes de interface no portal, reaproveitando aquela sessão
 *   evidencias   → grava vídeo e screenshot de cada item do relatório de sessão
 *
 * `npm test` roda api + web. As evidências são geradas por `npm run evidencias`, porque
 * levam mais tempo (rodam com slowMo, para o vídeo ficar assistível).
 */

const fs = require('node:fs');
const path = require('node:path');

const { defineConfig, devices } = require('@playwright/test');

const config = require('./support/config');

const portaApi = new URL(config.apiBaseURL).port || '8000';
const portaWeb = new URL(config.webBaseURL).port || '5173';

// A automação só consegue subir a aplicação se ela estiver em algum lugar. Neste branch
// estão apenas os testes, então o padrão `../..` não encontra nada — a checagem acontece
// aqui, antes do webServer, para a falha dizer o que fazer em vez de um "No such file".
if (config.subirServidores && !fs.existsSync(path.join(config.diretorioApp, 'api/main.py'))) {
  throw new Error(
    `Aplicação não encontrada em "${config.diretorioApp}".\n\n` +
      'Este branch tem apenas os testes: o código da aplicação está no main.\n' +
      'Aponte APP_DIR para um diretório onde a aplicação esteja, por exemplo:\n' +
      '    APP_DIR=../../../aplicacao npm test\n\n' +
      'Para não repetir a cada comando, copie .env.example para .env e preencha uma vez.\n' +
      'Se os servidores já estiverem no ar, use START_SERVERS=0.',
  );
}

/** Sobe API e portal web; `START_SERVERS=0` desliga, para quando você já subiu na mão. */
const servidores = [
  {
    // O venv da aplicação foi criado antes da pasta ser renomeada, então os executáveis
    // de console (uvicorn, alembic) têm shebang quebrado. `python -m <modulo>` funciona.
    command: `"${config.pythonBin}" -m uvicorn api.main:app --host 0.0.0.0 --port ${portaApi}`,
    cwd: config.diretorioApp,
    url: `${config.apiBaseURL}/health`,
    env: {
      DATABASE_URL: config.testDatabaseUrl,
      RATE_LIMIT_PER_MINUTE: String(config.rateLimitPorMinuto),
    },
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 120_000,
  },
  {
    command: `npm run dev -- --port ${portaWeb} --strictPort`,
    cwd: config.diretorioFrontend,
    url: config.webBaseURL,
    env: { VITE_API_BASE_URL: config.apiBaseURL },
    reuseExistingServer: !process.env.CI,
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 180_000,
  },
];

module.exports = defineConfig({
  testDir: './tests',
  outputDir: './test-results',

  // Prepara o banco exclusivo da automação antes de qualquer teste.
  globalSetup: require.resolve('./global-setup.js'),

  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,

  timeout: 60_000,
  expect: { timeout: 10_000 },

  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
    // Resultado em JSON: é a matéria-prima do relatório gerado por `npm run relatorio`.
    // Cada script de npm define NOME_EXECUCAO para não sobrescrever o resultado do outro.
    ['json', { outputFile: `resultados/${process.env.NOME_EXECUCAO ?? 'ultima'}.json` }],
  ],

  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 15_000,
    navigationTimeout: 30_000,
    // Interface em pt-BR, como o público-alvo da aplicação.
    locale: 'pt-BR',
    timezoneId: 'America/Sao_Paulo',
  },

  projects: [
    {
      name: 'api',
      testDir: './tests/api',
      use: {
        baseURL: config.apiBaseURL,
        extraHTTPHeaders: { Accept: 'application/json' },
      },
    },
    {
      name: 'setup-portal',
      testDir: './tests/setup',
      testMatch: /.*\.setup\.js/,
      use: { baseURL: config.apiBaseURL },
    },
    {
      name: 'evidencias',
      testDir: './tests/evidencias',
      dependencies: ['setup-portal'],
      // Vídeo e screenshot SEMPRE, não só na falha: aqui o artefato é o entregável.
      // `slowMo` existe para o vídeo ficar assistível por uma pessoa.
      use: {
        ...devices['Desktop Chrome'],
        baseURL: config.webBaseURL,
        storageState: config.arquivoSessao,
        viewport: { width: 1280, height: 720 },
        video: { mode: 'on', size: { width: 1280, height: 720 } },
        screenshot: 'on',
        trace: 'on',
        launchOptions: { slowMo: 250 },
      },
      timeout: 180_000,
    },
    {
      name: 'web',
      testDir: './tests/web',
      dependencies: ['setup-portal'],
      use: {
        ...devices['Desktop Chrome'],
        baseURL: config.webBaseURL,
        storageState: config.arquivoSessao,
      },
    },
  ],

  webServer: config.subirServidores ? servidores : undefined,
});
