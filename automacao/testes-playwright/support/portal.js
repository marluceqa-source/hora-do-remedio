/**
 * Ações de API reutilizáveis (helpers de pré-condição).
 *
 * Nenhum teste deve "montar o cenário clicando": quando o objetivo do teste é outra
 * coisa, a pré-condição é criada por API — mais rápido e mais estável. É o padrão que a
 * documentação do Playwright chama de "Sending API requests from UI tests".
 *
 * Importante: a sessão do profissional é um cookie httpOnly. Quem guarda esse cookie é o
 * APIRequestContext usado nas chamadas, e é dele que sai o storageState reaproveitado
 * pelo navegador nos testes de web.
 */

const { expect } = require('@playwright/test');

const { gerarCodigoDaUri, gerarCodigoTotp } = require('./totp');
const { SENHA_PADRAO, novoPaciente, novoProfissional } = require('./dados');

/** POST /api/v1/professionals — solicita o cadastro do profissional (RF01). */
async function cadastrarProfissional(api, dados = novoProfissional()) {
  const resposta = await api.post('/api/v1/professionals', { data: dados });
  expect(resposta.status(), await textoDoErro(resposta)).toBe(201);
  return { dados, profissional: await resposta.json() };
}

/**
 * Login completo do profissional: senha (1ª etapa) + código TOTP (2ª etapa).
 *
 * No primeiro acesso o backend responde purpose="mfa_setup" e entrega a URI otpauth://,
 * de onde tiramos o segredo. Nos acessos seguintes responde purpose="mfa_verify" e o
 * segredo precisa ser informado por quem chama.
 *
 * Ao final, o cookie de sessão está no contexto `api`.
 */
async function autenticarProfissional(api, { email, password = SENHA_PADRAO, segredo = null } = {}) {
  const login = await api.post('/api/v1/auth/professional/login', { data: { email, password } });
  expect(login.status(), await textoDoErro(login)).toBe(200);
  const { pre_auth_token: preAuthToken, purpose } = await login.json();

  if (purpose === 'mfa_setup') {
    const setup = await api.post('/api/v1/auth/professional/mfa/setup', {
      data: { pre_auth_token: preAuthToken },
    });
    expect(setup.status(), await textoDoErro(setup)).toBe(200);
    const { provisioning_uri: provisioningUri } = await setup.json();

    const confirmacao = await api.post('/api/v1/auth/professional/mfa/confirm', {
      data: { pre_auth_token: preAuthToken, code: gerarCodigoDaUri(provisioningUri) },
    });
    expect(confirmacao.status(), await textoDoErro(confirmacao)).toBe(200);

    return {
      profissional: await confirmacao.json(),
      provisioningUri,
      segredo: new URL(provisioningUri).searchParams.get('secret'),
      purpose,
    };
  }

  if (!segredo) {
    throw new Error('Este profissional já tem MFA ativo: informe o segredo TOTP para concluir o login.');
  }

  const verificacao = await api.post('/api/v1/auth/professional/mfa/verify', {
    data: { pre_auth_token: preAuthToken, code: gerarCodigoTotp(segredo) },
  });
  expect(verificacao.status(), await textoDoErro(verificacao)).toBe(200);

  return { profissional: await verificacao.json(), provisioningUri: null, segredo, purpose };
}

/** Cadastra e já deixa o profissional logado no contexto `api` informado. */
async function criarProfissionalAutenticado(api, sobrescritas = {}) {
  const { dados } = await cadastrarProfissional(api, novoProfissional(sobrescritas));
  const { profissional, segredo } = await autenticarProfissional(api, {
    email: dados.email,
    password: dados.password,
  });
  return { dados, profissional, segredo };
}

/** POST /api/v1/patients — exige sessão de profissional clínico (RF03). */
async function criarPaciente(api, sobrescritas = {}) {
  const dados = novoPaciente(sobrescritas);
  const resposta = await api.post('/api/v1/patients', { data: dados });
  expect(resposta.status(), await textoDoErro(resposta)).toBe(201);
  return { dados, paciente: await resposta.json() };
}

/** POST /api/v1/auth/token — token JWT do app do paciente (usado pelo bot do Telegram). */
async function obterTokenPaciente(api, telegramUserId) {
  const resposta = await api.post('/api/v1/auth/token', {
    data: { telegram_user_id: telegramUserId },
  });
  expect(resposta.status(), await textoDoErro(resposta)).toBe(200);
  const { access_token: accessToken } = await resposta.json();
  return accessToken;
}

/** Cabeçalho de autorização do app do paciente. */
function cabecalhoBearer(token) {
  return { Authorization: `Bearer ${token}` };
}

/** Mensagem de diagnóstico para quando uma pré-condição falha. */
async function textoDoErro(resposta) {
  let corpo = '';
  try {
    corpo = (await resposta.text()).slice(0, 500);
  } catch {
    corpo = '(sem corpo)';
  }
  return `${resposta.url()} respondeu ${resposta.status()} ${resposta.statusText()}: ${corpo}`;
}

module.exports = {
  autenticarProfissional,
  cabecalhoBearer,
  cadastrarProfissional,
  criarPaciente,
  criarProfissionalAutenticado,
  obterTokenPaciente,
  textoDoErro,
};
