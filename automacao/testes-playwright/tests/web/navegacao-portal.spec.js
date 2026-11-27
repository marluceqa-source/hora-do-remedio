/**
 * WEB — proteção de rotas, navegação do menu e encerramento de sessão.
 *
 * Cenários em Gherkin: docs/casos-de-teste-web-gherkin.md — CT-WEB-N01 a CT-WEB-N05.
 */

const { test, expect } = require('../../fixtures');
const config = require('../../support/config');

test.describe('Acesso sem sessão', () => {
  test.use({ storageState: { cookies: [], origins: [] } });

  test('CT-WEB-N01 · rotas protegidas redirecionam para o login quando não há sessão', async ({ page }) => {
    for (const rota of ['/', '/patients', '/patients/new', '/profile', '/admin']) {
      await page.goto(rota);

      await expect(page, `rota ${rota} deveria exigir login`).toHaveURL(/\/login$/);
      await expect(page.getByRole('button', { name: 'Entrar' })).toBeVisible();
    }
  });
});

test.describe('Portal com profissional autenticado', () => {
  test('CT-WEB-N02 · o dashboard apresenta os indicadores operacionais', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();

    for (const indicador of [
      'Pacientes vinculados',
      'Tratamentos ativos',
      'Terminando em breve',
      'Lembretes enviados',
      'Doses confirmadas',
      'Doses não tomadas',
      'Sem confirmação',
    ]) {
      await expect(page.getByText(indicador, { exact: true })).toBeVisible();
    }

    // RN12/RN29: ausência de resposta nunca é apresentada como "não tomou"
    await expect(page.getByText('Não significa que não foi tomado (RN12)')).toBeVisible();
  });

  test('CT-WEB-N03 · o menu principal navega entre dashboard, pacientes e perfil', async ({ page }) => {
    await page.goto('/');
    const menu = page.getByRole('navigation', { name: 'Menu principal' });

    await menu.getByText('Pacientes', { exact: true }).click();
    await expect(page).toHaveURL(/\/patients$/);
    await expect(page.getByRole('heading', { name: 'Pacientes', level: 1 })).toBeVisible();

    await menu.getByText('Meu perfil', { exact: true }).click();
    await expect(page).toHaveURL(/\/profile$/);
    await expect(page.getByRole('heading', { name: 'Meu perfil', level: 1 })).toBeVisible();

    await menu.getByText('Dashboard', { exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
  });

  test('CT-WEB-N04 · profissional sem papel de administrador não acessa a administração', async ({ page }) => {
    // O menu nem oferece o item, e a rota digitada na mão volta para o dashboard
    await page.goto('/');
    await expect(
      page.getByRole('navigation', { name: 'Menu principal' }).getByText('Administração'),
    ).toHaveCount(0);

    await page.goto('/admin');
    await expect(page).toHaveURL(`${config.webBaseURL}/`);
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
  });

  test('CT-WEB-N05 · ao sair, a sessão é encerrada e as rotas voltam a exigir login', async ({
    paginaComSessaoPropria,
  }) => {
    // Este teste usa uma sessão exclusiva: encerrar a sessão compartilhada derrubaria os
    // outros testes de web.
    const { pagina } = paginaComSessaoPropria;

    await pagina.goto('/');
    await expect(pagina.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();

    // Quando clico em "Sair"
    await pagina.getByRole('navigation', { name: 'Menu principal' }).getByText('Sair', { exact: true }).click();

    // Então volto ao login e a rota protegida não abre mais
    await expect(pagina).toHaveURL(/\/login$/);
    await pagina.goto('/');
    await expect(pagina).toHaveURL(/\/login$/);
  });
});
