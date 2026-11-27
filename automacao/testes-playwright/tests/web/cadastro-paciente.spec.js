/**
 * WEB — cadastro de paciente pelo portal (/patients/new), com o profissional já logado.
 *
 * Cenários em Gherkin: docs/casos-de-teste-web-gherkin.md — CT-WEB-P01 a CT-WEB-P05.
 *
 * A sessão vem do projeto "setup-portal" (storageState), então nenhum teste precisa
 * refazer login pela interface — quem testa login é tests/web/login-portal.spec.js.
 */

const { test, expect } = require('../../fixtures');
const { HEURISTICAS_STRING, novoPaciente } = require('../../support/dados');

test.beforeEach(async ({ page }) => {
  await page.goto('/patients/new');
  await expect(page.getByRole('heading', { name: 'Cadastrar paciente', level: 1 })).toBeVisible();
});

test.describe('Cadastro de paciente', () => {
  test('CT-WEB-P01 · cadastro de paciente realizado com sucesso', async ({ page }) => {
    // Dado que possuo os dados do paciente
    const paciente = novoPaciente();

    // Quando preencho o formulário e clico em "Cadastrar"
    await page.getByLabel('Nome completo').fill(paciente.full_name);
    await page.getByLabel('Identificador interno').fill(paciente.internal_identifier);
    await page.getByLabel('Data de nascimento').fill(paciente.birth_date);
    await page.getByRole('button', { name: 'Cadastrar' }).click();

    // Então sou levada à ficha do paciente, com nome e identificador
    await expect(page).toHaveURL(/\/patients\/\d+$/);
    await expect(page.getByRole('heading', { name: paciente.full_name, level: 1 })).toBeVisible();
    await expect(page.getByText(`Identificador: ${paciente.internal_identifier}`)).toBeVisible();

    // E a ficha abre nas abas de acompanhamento do tratamento
    await expect(page.getByRole('tab', { name: 'Vínculo Telegram' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Medicamentos' })).toBeVisible();
    await expect(page.getByRole('tab', { name: 'Histórico' })).toBeVisible();
  });

  test('CT-WEB-P02 · cadastro recusado quando os campos obrigatórios estão vazios', async ({ page }) => {
    // Quando clico em "Cadastrar" sem preencher nada
    await page.getByRole('button', { name: 'Cadastrar' }).click();

    // Então cada campo obrigatório aponta o próprio erro e nada é cadastrado
    await expect(page.getByText('Informe o nome completo')).toBeVisible();
    await expect(page.getByText('Informe o identificador interno')).toBeVisible();
    await expect(page).toHaveURL(/\/patients\/new$/);
  });

  test('CT-WEB-P03 · cadastro recusado quando o identificador interno já existe', async ({
    page,
    contextoProfissional,
  }) => {
    // Dado um paciente já cadastrado com um identificador (pré-condição por API)
    const existente = novoPaciente();
    const criacao = await contextoProfissional.api.post('/api/v1/patients', { data: existente });
    expect(criacao.status()).toBe(201);

    // Quando tento cadastrar outro paciente com o mesmo identificador
    await page.getByLabel('Nome completo').fill('Outro Paciente Fictício');
    await page.getByLabel('Identificador interno').fill(existente.internal_identifier);
    await page.getByRole('button', { name: 'Cadastrar' }).click();

    // Então a mensagem de conflito é exibida
    await expect(page.getByRole('alert')).toContainText('Já existe um paciente com este identificador interno');
  });

  test('CT-WEB-P04 · o paciente cadastrado aparece na lista como não vinculado ao Telegram', async ({
    page,
  }) => {
    // Dado um paciente cadastrado pela interface
    const paciente = novoPaciente();
    await page.getByLabel('Nome completo').fill(paciente.full_name);
    await page.getByLabel('Identificador interno').fill(paciente.internal_identifier);
    await page.getByRole('button', { name: 'Cadastrar' }).click();
    await expect(page.getByRole('heading', { name: paciente.full_name, level: 1 })).toBeVisible();

    // Quando abro a lista de pacientes
    await page.goto('/patients');

    // Então ele está lá, com o identificador e o status de vínculo
    const item = page.getByRole('link').filter({ hasText: paciente.full_name });
    await expect(item).toBeVisible();
    await expect(item).toContainText(`Identificador: ${paciente.internal_identifier}`);
    await expect(item).toContainText('Não vinculado');
  });

  test('CT-WEB-P05 · nome de paciente com mais de 200 caracteres é recusado', async ({ page }) => {
    // Heurística de strings: nome longo. O limite é do backend e a mensagem precisa
    // chegar traduzida na tela.
    await page.getByLabel('Nome completo').fill(HEURISTICAS_STRING.textoLongo(201));
    await page.getByLabel('Identificador interno').fill(novoPaciente().internal_identifier);
    await page.getByRole('button', { name: 'Cadastrar' }).click();

    await expect(page.getByRole('alert')).toContainText('Nome completo: deve ter no máximo 200 caracteres');
    await expect(page).toHaveURL(/\/patients\/new$/);
  });
});
