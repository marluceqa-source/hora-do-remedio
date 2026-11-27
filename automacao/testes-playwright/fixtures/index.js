/**
 * Fixtures customizadas.
 *
 * O `request` nativo do Playwright já respeita o baseURL do projeto, mas os testes
 * precisam de contextos com autenticação diferente:
 *
 *   api                    → sem autenticação (cadastro, login, erros de 401)
 *   contextoPaciente       → token JWT do app do paciente (Authorization: Bearer)
 *   contextoProfissional   → cookie de sessão do portal, após senha + MFA
 *   contextoAdministrador  → o mesmo, com o papel de administrador
 *   paginaComSessaoPropria → página do navegador com uma sessão descartável do portal
 *
 * Cada contexto é criado com `playwright.request.newContext()` e descartado no fim do
 * teste com `dispose()`, como recomenda a documentação de API testing do Playwright.
 */

const base = require('@playwright/test');

const config = require('../support/config');
const { novoTelegramUserId } = require('../support/dados');
const { cabecalhoBearer, criarProfissionalAutenticado, obterTokenPaciente } = require('../support/portal');

const test = base.test.extend({
  /** Contexto de API sem nenhuma credencial. */
  api: async ({ playwright }, use) => {
    const contexto = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    await use(contexto);
    await contexto.dispose();
  },

  /**
   * Contexto do app do paciente, já com `Authorization: Bearer <token>`.
   * Cada teste recebe um usuário novo (telegram_user_id único), então um teste nunca vê
   * o medicamento criado por outro — o que também permite rodar em paralelo.
   */
  contextoPaciente: async ({ playwright }, use) => {
    const semAuth = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    const telegramUserId = novoTelegramUserId();
    const token = await obterTokenPaciente(semAuth, telegramUserId);
    await semAuth.dispose();

    const contexto = await playwright.request.newContext({
      baseURL: config.apiBaseURL,
      extraHTTPHeaders: cabecalhoBearer(token),
    });

    await use({ api: contexto, token, telegramUserId });
    await contexto.dispose();
  },

  /**
   * Contexto do portal com um profissional novo já autenticado (senha + TOTP).
   * Devolve também os dados de cadastro e o segredo TOTP, úteis para testes que
   * precisam fazer login de novo ou validar o próprio fluxo de MFA.
   */
  contextoProfissional: async ({ playwright }, use) => {
    const contexto = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    const { dados, profissional, segredo } = await criarProfissionalAutenticado(contexto);

    await use({ api: contexto, dados, profissional, segredo });
    await contexto.dispose();
  },

  /** Igual ao anterior, mas com o papel de administrador (RBAC da seção 3). */
  contextoAdministrador: async ({ playwright }, use) => {
    const contexto = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    const { dados, profissional, segredo } = await criarProfissionalAutenticado(contexto, {
      role: 'admin',
      profession: 'Administração',
    });

    await use({ api: contexto, dados, profissional, segredo });
    await contexto.dispose();
  },

  /**
   * Página do portal autenticada com um profissional EXCLUSIVO deste teste.
   *
   * Os testes de web normalmente reaproveitam a sessão criada pelo projeto "setup-portal".
   * Testes que encerram a sessão (logout) precisam de uma sessão descartável, senão
   * invalidariam a sessão compartilhada e derrubariam os demais testes.
   */
  paginaComSessaoPropria: async ({ browser, playwright }, use) => {
    const apiSessao = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    const { dados, profissional } = await criarProfissionalAutenticado(apiSessao);

    // `browser.newContext()` não herda as opções do projeto: baseURL e locale vão na mão.
    const contextoNavegador = await browser.newContext({
      storageState: await apiSessao.storageState(),
      baseURL: config.webBaseURL,
      locale: 'pt-BR',
      timezoneId: 'America/Sao_Paulo',
    });
    const pagina = await contextoNavegador.newPage();

    await use({ pagina, dados, profissional, api: apiSessao });

    await contextoNavegador.close();
    await apiSessao.dispose();
  },
});

module.exports = { test, expect: base.expect };
