/**
 * Projeto de setup do portal web.
 *
 * Cria por API um profissional novo, faz o login completo (senha + TOTP) e grava em disco:
 *   .auth/profissional-sessao.json → storageState com o cookie de sessão
 *   .auth/profissional-dados.json  → e-mail, senha, segredo TOTP e perfil criado
 *
 * O projeto "web" depende deste e abre o navegador já autenticado. A documentação do
 * Playwright chama esse reaproveitamento de "Reusing authentication state": o
 * storageState é intercambiável entre APIRequestContext e BrowserContext.
 */

const fs = require('node:fs');
const path = require('node:path');

const { test: setup, expect } = require('@playwright/test');

const config = require('../../support/config');
const { criarProfissionalAutenticado } = require('../../support/portal');

setup('prepara a sessão de um profissional de saúde autenticado no portal', async ({ playwright }) => {
  const api = await playwright.request.newContext({ baseURL: config.apiBaseURL });

  const { dados, profissional, segredo } = await criarProfissionalAutenticado(api);

  // Confirma que a sessão realmente vale antes de salvar o estado.
  const perfil = await api.get('/api/v1/professionals/me');
  expect(perfil.status()).toBe(200);
  expect((await perfil.json()).email).toBe(dados.email);

  fs.mkdirSync(path.dirname(config.arquivoSessao), { recursive: true });
  await api.storageState({ path: config.arquivoSessao });

  fs.writeFileSync(
    config.arquivoProfissional,
    JSON.stringify({ ...dados, segredoTotp: segredo, id: profissional.id, role: profissional.role }, null, 2),
    'utf-8',
  );

  // O cookie de sessão é httpOnly e precisa ter sido capturado — sem ele o projeto "web"
  // abriria o navegador deslogado e todo teste autenticado cairia na tela de login.
  const estado = JSON.parse(fs.readFileSync(config.arquivoSessao, 'utf-8'));
  expect(estado.cookies.map((cookie) => cookie.name)).toContain('hdr_professional_session');

  await api.dispose();
});
