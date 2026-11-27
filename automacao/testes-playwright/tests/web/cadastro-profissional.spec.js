/**
 * WEB — formulário de cadastro de profissional de saúde (/signup).
 *
 * Os cenários estão escritos em Gherkin (Dado / Quando / Então) em
 * docs/casos-de-teste-web-gherkin.md — CT-WEB-C01 a CT-WEB-C08 — e o comentário de cada
 * teste repete o cenário correspondente.
 *
 * Esta tela é pública: a sessão herdada do projeto de setup é descartada de propósito.
 */

const { test, expect } = require('../../fixtures');
const { HEURISTICAS_STRING, novoProfissional } = require('../../support/dados');
const { cadastrarProfissional } = require('../../support/portal');

test.use({ storageState: { cookies: [], origins: [] } });

/** Preenche o formulário de cadastro; campos não informados ficam como estão. */
async function preencherCadastro(page, dados) {
  if (dados.full_name !== undefined) await page.getByLabel('Nome completo').fill(dados.full_name);
  if (dados.email !== undefined) await page.getByLabel('E-mail').fill(dados.email);
  if (dados.password !== undefined) await page.getByLabel('Senha').fill(dados.password);
  if (dados.profession !== undefined) await page.getByLabel('Profissão').fill(dados.profession);
  if (dados.council_number !== undefined) {
    await page.getByLabel('Número do conselho profissional').fill(dados.council_number);
  }
  if (dados.council_state !== undefined) await page.getByLabel('UF do conselho').fill(dados.council_state);
}

test.beforeEach(async ({ page }) => {
  await page.goto('/signup');
  await expect(page.getByRole('heading', { name: 'Criar conta de profissional' })).toBeVisible();
});

test.describe('Cadastro de profissional de saúde', () => {
  test('CT-WEB-C01 · cadastro realizado com sucesso', async ({ page }) => {
    // Dado que possuo todos os dados do profissional
    const dados = novoProfissional();

    // Quando preencho o formulário e clico em "Criar conta"
    await preencherCadastro(page, dados);
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // Então vejo a confirmação de que o cadastro ainda passa por verificação do administrador
    const confirmacao = page.getByText(/Cadastro recebido!/);
    await expect(confirmacao).toBeVisible();
    await expect(confirmacao).toContainText('precisa ser verificada por um administrador');

    // E tenho o caminho para o login
    await expect(page.getByRole('link', { name: 'Ir para o login' })).toBeVisible();
  });

  test('CT-WEB-C02 · cadastro recusado quando o e-mail é inválido', async ({ page }) => {
    // Dado que informo um e-mail sem domínio
    await preencherCadastro(page, novoProfissional({ email: 'profissional-sem-arroba' }));

    // Quando tento criar a conta
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // Então a mensagem "Informe um e-mail válido" é exibida e o cadastro não acontece
    await expect(page.getByText('Informe um e-mail válido')).toBeVisible();
    await expect(page.getByText(/Cadastro recebido!/)).toHaveCount(0);
  });

  test('CT-WEB-C03 · cadastro recusado quando a senha tem menos de 8 caracteres', async ({ page }) => {
    await preencherCadastro(page, novoProfissional({ password: '1234567' }));

    await page.getByRole('button', { name: 'Criar conta' }).click();

    await expect(page.getByText('A senha deve ter pelo menos 8 caracteres')).toBeVisible();
  });

  test('CT-WEB-C04 · cadastro recusado quando os campos obrigatórios estão vazios', async ({ page }) => {
    // Dado que não preencho nada
    // Quando clico em "Criar conta"
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // Então cada campo obrigatório aponta o próprio erro
    await expect(page.getByText('Informe o nome completo')).toBeVisible();
    await expect(page.getByText('Informe um e-mail válido')).toBeVisible();
    await expect(page.getByText('A senha deve ter pelo menos 8 caracteres')).toBeVisible();
    await expect(page.getByText('Informe a profissão')).toBeVisible();
  });

  test('CT-WEB-C05 · UF do conselho aceita apenas 2 letras e é gravada em maiúsculas', async ({ page }) => {
    // Heurística de tipos de dados: limite de tamanho do campo e normalização de valor
    const campoUf = page.getByLabel('UF do conselho');

    await campoUf.fill('mg');
    await expect(campoUf).toHaveValue('MG');

    // Quando tento digitar além do limite, o campo não aceita o excedente
    await campoUf.fill('');
    await campoUf.pressSequentially('spsp');
    await expect(campoUf).toHaveValue('SP');
  });

  test('CT-WEB-C06 · cadastro recusado quando o e-mail já está cadastrado', async ({ page, api }) => {
    // Dado um profissional já cadastrado (pré-condição criada por API)
    const { dados } = await cadastrarProfissional(api);

    // Quando tento cadastrar o mesmo e-mail pelo portal
    await preencherCadastro(page, { ...novoProfissional(), email: dados.email });
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // Então a mensagem "E-mail já cadastrado" é exibida
    await expect(page.getByRole('alert')).toContainText('E-mail já cadastrado');
  });

  test('CT-WEB-C07 · cadastro com papel de enfermeiro(a)', async ({ page }) => {
    // Dado que escolho outro papel na lista
    await preencherCadastro(page, novoProfissional({ profession: 'Enfermeiro' }));
    await page.getByLabel('Papel').click();
    await page.getByRole('option', { name: 'Enfermeiro(a)' }).click();

    // Quando crio a conta
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // Então o cadastro é aceito
    await expect(page.getByText(/Cadastro recebido!/)).toBeVisible();
  });

  test('CT-WEB-C08 · nome com mais de 200 caracteres é recusado pelo servidor', async ({ page }) => {
    // Heurística de strings: nome longo. O frontend não limita o tamanho, então o erro
    // vem do backend — e precisa chegar traduzido na tela, não cru em inglês.
    await preencherCadastro(page, novoProfissional({ full_name: HEURISTICAS_STRING.textoLongo(201) }));

    await page.getByRole('button', { name: 'Criar conta' }).click();

    await expect(page.getByRole('alert')).toContainText('Nome completo: deve ter no máximo 200 caracteres');
  });
});
