/**
 * Preparação global: garante que o banco exclusivo da automação existe e está na última
 * migração antes de subir a API.
 *
 * A aplicação não cria tabelas no start — o schema vem do Alembic. Apontar DATABASE_URL
 * para um arquivo SQLite próprio mantém o banco de desenvolvimento intacto.
 */

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');

const config = require('./support/config');

module.exports = async () => {
  if (!config.subirServidores) {
    console.log('[setup] START_SERVERS=0 — migração e servidores por sua conta.');
    return;
  }

  if (!fs.existsSync(config.pythonBin)) {
    throw new Error(
      `Python da aplicação não encontrado em "${config.pythonBin}".\n\n` +
        'Este branch tem apenas os testes: o código da aplicação não está nesta árvore.\n' +
        'Aponte APP_DIR para um diretório onde a aplicação esteja, por exemplo:\n' +
        '    APP_DIR=../../../aplicacao npm test\n\n' +
        'Para não repetir a cada comando, copie .env.example para .env e preencha uma vez.',
    );
  }

  console.log(`[setup] aplicando migrações em ${config.testDatabaseUrl}`);
  execFileSync(config.pythonBin, ['-m', 'alembic', 'upgrade', 'head'], {
    cwd: config.diretorioApp,
    env: { ...process.env, DATABASE_URL: config.testDatabaseUrl },
    stdio: 'inherit',
  });
};
