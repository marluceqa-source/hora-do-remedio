/**
 * Apaga o banco da automação e recria o schema do zero.
 * Uso: npm run db:reset
 */

const { execFileSync } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

const config = require('../support/config');

const caminhoRelativo = config.testDatabaseUrl.replace(/^sqlite:\/\/\//, '');
const arquivo = path.resolve(config.diretorioApp, caminhoRelativo);

if (fs.existsSync(arquivo)) {
  fs.unlinkSync(arquivo);
  console.log(`[reset] removido ${arquivo}`);
} else {
  console.log(`[reset] nada a remover em ${arquivo}`);
}

execFileSync(config.pythonBin, ['-m', 'alembic', 'upgrade', 'head'], {
  cwd: config.diretorioApp,
  env: { ...process.env, DATABASE_URL: config.testDatabaseUrl },
  stdio: 'inherit',
});
console.log('[reset] banco da automação recriado.');
