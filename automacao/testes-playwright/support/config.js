/**
 * Configuração central da automação.
 *
 * Tudo que é endereço, caminho ou credencial de ambiente mora aqui — os testes nunca
 * repetem uma URL literal. Valores podem ser sobrescritos por variáveis de ambiente
 * ou por um arquivo `.env` na raiz deste projeto (veja `.env.example`).
 */

const fs = require('node:fs');
const path = require('node:path');

const RAIZ_PROJETO = path.resolve(__dirname, '..');

/** Carrega o `.env` deste projeto sem depender de biblioteca externa. */
function carregarEnvLocal() {
  const arquivo = path.join(RAIZ_PROJETO, '.env');
  if (!fs.existsSync(arquivo)) return;

  for (const linha of fs.readFileSync(arquivo, 'utf-8').split(/\r?\n/)) {
    const conteudo = linha.trim();
    if (!conteudo || conteudo.startsWith('#')) continue;

    const separador = conteudo.indexOf('=');
    if (separador === -1) continue;

    const chave = conteudo.slice(0, separador).trim();
    const valor = conteudo.slice(separador + 1).trim().replace(/^["']|["']$/g, '');
    // Variável já exportada no shell tem prioridade sobre o arquivo.
    if (process.env[chave] === undefined) process.env[chave] = valor;
  }
}

carregarEnvLocal();

function caminhoAbsoluto(valor, padrao) {
  const bruto = valor ?? padrao;
  return path.isAbsolute(bruto) ? bruto : path.resolve(RAIZ_PROJETO, bruto);
}

const DIRETORIO_APP = caminhoAbsoluto(process.env.APP_DIR, '../..');

const config = {
  raizProjeto: RAIZ_PROJETO,

  /** Portal web de profissionais (React + Vite). */
  webBaseURL: process.env.WEB_BASE_URL ?? 'http://localhost:5173',

  /**
   * API REST (FastAPI). Usar `localhost` (e não 127.0.0.1) é proposital: o cookie de
   * sessão é emitido para o domínio `localhost` e precisa valer também para o portal,
   * que roda em `localhost:5173` — cookie não distingue porta, mas distingue domínio.
   */
  apiBaseURL: process.env.API_BASE_URL ?? 'http://localhost:8000',

  /** Aplicação sob teste. */
  diretorioApp: DIRETORIO_APP,
  diretorioFrontend: path.join(DIRETORIO_APP, 'frontend'),
  pythonBin: caminhoAbsoluto(process.env.PYTHON_BIN, path.join(DIRETORIO_APP, '.venv/bin/python')),

  /** Banco exclusivo da automação — o banco de desenvolvimento nunca é tocado. */
  testDatabaseUrl: process.env.TEST_DATABASE_URL ?? 'sqlite:///./database/playwright_test.db',

  /**
   * A API usa slowapi com limite por IP. O padrão da aplicação (60/min) estoura quando
   * vários workers rodam em paralelo e gera 429 em teste que não é de rate limit — por
   * isso a automação sobe a API com um limite alto. O cenário de rate limit (pilar
   * Responsiveness do VADER) está documentado em docs/casos-de-teste-api-vader.md.
   */
  rateLimitPorMinuto: process.env.TEST_RATE_LIMIT_PER_MINUTE ?? '1000',

  /** 0 = os servidores já estão de pé; 1 = a automação sobe API e portal. */
  subirServidores: (process.env.START_SERVERS ?? '1') !== '0',

  /** Arquivos produzidos pelo projeto de setup e consumidos pelos testes de web. */
  arquivoSessao: path.join(RAIZ_PROJETO, '.auth/profissional-sessao.json'),
  arquivoProfissional: path.join(RAIZ_PROJETO, '.auth/profissional-dados.json'),
};

module.exports = config;
