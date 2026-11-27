/**
 * WEB — login do portal em duas etapas: senha e código TOTP (RF01).
 *
 * Cenários em Gherkin: docs/casos-de-teste-web-gherkin.md — CT-WEB-L01 a CT-WEB-L08.
 *
 * O código de 6 dígitos é calculado pela própria automação (support/totp.js) a partir do
 * segredo que a tela entrega no primeiro acesso — é assim que o login de ponta a ponta
 * roda sem aplicativo autenticador na mão.
 */

const { test, expect } = require('../../fixtures');
const config = require('../../support/config');
const { gerarCodigoDaUri } = require('../../support/totp');
const { cadastrarProfissional } = require('../../support/portal');

test.use({ storageState: { cookies: [], origins: [] } });

test.beforeEach(async ({ page }) => {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: /Hora do Remédio/ })).toBeVisible();
});

/** Faz a 1ª etapa (senha) e devolve a URI otpauth:// capturada da resposta da API. */
async function entrarComSenha(page, { email, password }) {
  await page.getByLabel('E-mail').fill(email);
  await page.getByLabel('Senha').fill(password);

  const respostaSetup = page.waitForResponse(
    (resposta) => resposta.url().includes('/auth/professional/mfa/setup') && resposta.status() === 200,
  );
  await page.getByRole('button', { name: 'Entrar' }).click();

  return (await (await respostaSetup).json()).provisioning_uri;
}

test.describe('Login do portal de profissionais', () => {
  test('CT-WEB-L01 · login recusado quando e-mail e senha estão vazios', async ({ page }) => {
    // Dado que não informo credenciais
    // Quando clico em "Entrar"
    await page.getByRole('button', { name: 'Entrar' }).click();

    // Então a mensagem "Preencha o e-mail e a senha." é exibida
    await expect(page.getByRole('alert')).toHaveText('Preencha o e-mail e a senha.');
  });

  test('CT-WEB-L02 · login recusado com senha inválida', async ({ page, api }) => {
    // Dado um profissional cadastrado
    const { dados } = await cadastrarProfissional(api);

    // Quando informo a senha errada
    await page.getByLabel('E-mail').fill(dados.email);
    await page.getByLabel('Senha').fill('SenhaErrada123');
    await page.getByRole('button', { name: 'Entrar' }).click();

    // Então a mensagem genérica "E-mail ou senha inválidos" é exibida
    await expect(page.getByRole('alert')).toHaveText('E-mail ou senha inválidos');
    // E continuo na etapa de credenciais
    await expect(page.getByLabel('Senha')).toBeVisible();
  });

  test('CT-WEB-L03 · primeiro acesso apresenta a configuração do MFA com QR Code', async ({ page, api }) => {
    // Dado um profissional que nunca acessou o portal
    const { dados } = await cadastrarProfissional(api);

    // Quando informo as credenciais corretas
    const provisioningUri = await entrarComSenha(page, dados);

    // Então a tela pede a configuração da autenticação em duas etapas
    await expect(page.getByText(/Primeiro acesso: configure a autenticação em duas etapas/)).toBeVisible();
    // E apresenta o QR Code e o código para digitação manual
    await expect(page.locator('svg[width="200"]')).toBeVisible();
    await expect(page.getByText(provisioningUri).first()).toBeVisible();
    expect(provisioningUri).toMatch(/^otpauth:\/\/totp\//);
    await expect(page.getByLabel('Código de 6 dígitos')).toBeVisible();
  });

  test('CT-WEB-L04 · código fora do formato de 6 dígitos é barrado na própria tela', async ({ page, api }) => {
    const { dados } = await cadastrarProfissional(api);
    await entrarComSenha(page, dados);

    // Quando informo um código curto
    await page.getByLabel('Código de 6 dígitos').fill('123');
    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();

    // Então a validação local avisa, sem ida ao servidor
    await expect(page.getByRole('alert')).toHaveText(
      'Informe o código de 6 dígitos do aplicativo autenticador.',
    );
  });

  test('CT-WEB-L05 · código de 6 dígitos incorreto é recusado pelo servidor', async ({ page, api }) => {
    const { dados } = await cadastrarProfissional(api);
    await entrarComSenha(page, dados);

    await page.getByLabel('Código de 6 dígitos').fill('000000');
    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();

    await expect(page.getByRole('alert')).toHaveText('Código de verificação inválido');
    // E não entro no portal
    await expect(page).toHaveURL(/\/login$/);
  });

  test('CT-WEB-L06 · primeiro acesso concluído com código válido abre o dashboard', async ({ page, api }) => {
    // Dado um profissional em primeiro acesso
    const { dados } = await cadastrarProfissional(api);
    const provisioningUri = await entrarComSenha(page, dados);

    // Quando informo o código TOTP gerado a partir do segredo apresentado na tela
    await page.getByLabel('Código de 6 dígitos').fill(gerarCodigoDaUri(provisioningUri));
    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();

    // Então entro no portal e vejo o painel com meu nome no topo
    await expect(page).toHaveURL(`${config.webBaseURL}/`);
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    await expect(page.getByText(dados.full_name)).toBeVisible();
  });

  test('CT-WEB-L07 · segundo acesso pede apenas o código do autenticador', async ({ page, api }) => {
    // Dado um profissional que já configurou o MFA
    const { dados } = await cadastrarProfissional(api);
    const provisioningUri = await entrarComSenha(page, dados);
    await page.getByLabel('Código de 6 dígitos').fill(gerarCodigoDaUri(provisioningUri));
    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();

    // Quando volto à tela de login e entro outra vez
    await page.goto('/login');
    await page.getByLabel('E-mail').fill(dados.email);
    await page.getByLabel('Senha').fill(dados.password);
    await page.getByRole('button', { name: 'Entrar' }).click();

    // Então a tela não pede configuração de novo: só o código
    await expect(page.getByText('Digite o código do seu aplicativo autenticador.')).toBeVisible();
    await expect(page.getByText(/Primeiro acesso/)).toHaveCount(0);

    await page.getByLabel('Código de 6 dígitos').fill(gerarCodigoDaUri(provisioningUri));
    await page.getByRole('button', { name: 'Entrar' }).click();

    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
  });

  test('CT-WEB-L08 · a tela de login dá acesso ao cadastro e à recuperação de senha', async ({ page }) => {
    await page.getByRole('link', { name: 'Criar conta' }).click();
    await expect(page).toHaveURL(/\/signup$/);
    await expect(page.getByRole('heading', { name: 'Criar conta de profissional' })).toBeVisible();

    await page.goto('/login');
    await page.getByRole('link', { name: 'Esqueci minha senha' }).click();
    await expect(page).toHaveURL(/\/password-reset$/);
  });
});
