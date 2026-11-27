/**
 * Evidências das NOTAS informativas do relatório de sessão (I1 a I5).
 *
 * São as observações que sustentam as decisões de automação e os pontos em que a
 * aplicação se comporta bem. Cada teste grava vídeo + screenshots em `evidencias/`.
 *
 * Arquivos gerados: evidencias/I<n>-<seq>-<rótulo>.png e evidencias/I<n>-video.webm
 */

const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');

const { test, expect } = require('../../fixtures/evidencias');
const config = require('../../support/config');
const { gerarCodigoDaUri, gerarCodigoTotp, extrairSegredoDaUri } = require('../../support/totp');
const { novoProfissional } = require('../../support/dados');

const SEM_SESSAO = { storageState: { cookies: [], origins: [] } };

const TIPOS = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.zip': 'application/zip',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webm': 'video/webm',
  '.woff2': 'font/woff2',
};

/** Servidor estático mínimo, em porta livre — usado para abrir o relatório HTML. */
async function servirPasta(pasta) {
  const servidor = http.createServer((requisicao, resposta) => {
    const caminho = decodeURIComponent((requisicao.url ?? '/').split('?')[0]);
    const arquivo = path.join(pasta, caminho === '/' ? 'index.html' : caminho);

    fs.readFile(arquivo, (erro, conteudo) => {
      if (erro) {
        resposta.writeHead(404).end();
        return;
      }
      resposta.writeHead(200, { 'Content-Type': TIPOS[path.extname(arquivo)] ?? 'application/octet-stream' });
      resposta.end(conteudo);
    });
  });

  await new Promise((resolver) => servidor.listen(0, '127.0.0.1', resolver));
  return { servidor, endereco: `http://127.0.0.1:${servidor.address().port}/` };
}

test.describe('Evidências das notas — autenticação e automação', () => {
  test('I1 · as duas autenticações da aplicação são independentes (RN19)', async ({ page, evidencia }) => {
    // A sessão usada aqui é a do PORTAL (cookie httpOnly), criada pelo projeto de setup.

    // 1. Com o cookie de sessão, o endpoint do portal autentica
    await page.goto(`${config.apiBaseURL}/api/v1/professionals/me`);
    const perfil = await page.evaluate(() => document.body.textContent ?? '');
    expect(perfil).toContain('"email"');
    await evidencia.capturar('endpoint do portal autenticado pelo cookie', { paginaInteira: true });

    // 2. O MESMO navegador, com o MESMO cookie, não autentica no app do paciente:
    //    aquele endpoint espera um JWT no cabeçalho Authorization.
    await page.goto(`${config.apiBaseURL}/api/v1/medications`);
    const medicamentos = await page.evaluate(() => document.body.textContent ?? '');
    expect(medicamentos).toContain('Credenciais ausentes, inválidas ou expiradas');
    await evidencia.capturar('endpoint do paciente recusa o cookie do portal');

    // 3. O Swagger mostra os dois mundos documentados separadamente
    await page.goto(`${config.apiBaseURL}/docs`);
    await expect(page.getByText('Hora do Remédio API')).toBeVisible();
    await page.getByText('Portal — Autenticação', { exact: true }).first().scrollIntoViewIfNeeded();
    await evidencia.capturar('swagger com os dois grupos de autenticacao', { paginaInteira: true });
  });

  test('I3 · a sessão autenticada é reaproveitada do setup, sem passar pelo login', async ({
    page,
    evidencia,
  }) => {
    // O arquivo de sessão gravado pelo projeto "setup-portal"
    const estado = JSON.parse(fs.readFileSync(config.arquivoSessao, 'utf-8'));
    const cookie = estado.cookies.find((item) => item.name === 'hdr_professional_session');
    expect(cookie).toBeTruthy();

    await evidencia.exibirPainel('I3 — storageState reaproveitado pelo navegador', [
      {
        rotulo: `Arquivo gerado pelo projeto de setup: ${path.relative(config.raizProjeto, config.arquivoSessao)}`,
        conteudo: `cookie: ${cookie.name}\ndomínio: ${cookie.domain}\ncaminho: ${cookie.path}\nhttpOnly: ${cookie.httpOnly}\nvalor: ${cookie.value.slice(0, 12)}… (truncado nesta evidência)`,
      },
      {
        rotulo: 'Por que o domínio precisa ser "localhost", e não "127.0.0.1"',
        conteudo:
          'O cookie é emitido pela API (porta 8000) e precisa valer também no portal (porta 5173).\n' +
          'Cookie não distingue porta, mas distingue domínio: usar 127.0.0.1 na automação faria\n' +
          'o navegador abrir o portal deslogado.',
      },
    ]);
    await evidencia.capturar('cookie de sessao gravado em disco');

    // Abrir o portal direto na área protegida: nenhuma tela de login no caminho
    await page.goto('/');
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    expect(page.url()).not.toContain('/login');
    await evidencia.capturar('portal aberto direto no dashboard');

    await page.getByRole('navigation', { name: 'Menu principal' }).getByText('Pacientes', { exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Pacientes', level: 1 })).toBeVisible();
    await evidencia.capturar('navegacao autenticada em pacientes');

    await page.getByRole('navigation', { name: 'Menu principal' }).getByText('Meu perfil', { exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Meu perfil', level: 1 })).toBeVisible();
    await evidencia.capturar('perfil do profissional da sessao reaproveitada');
  });

  test('I4 · resultado da execução da suíte', async ({ page, evidencia }) => {
    const relatorio = path.join(config.raizProjeto, 'playwright-report/index.html');
    test.skip(
      !fs.existsSync(relatorio),
      'Relatório HTML ainda não existe. Rode `npm test` antes de `npm run evidencias`.',
    );

    // O relatório do Playwright não abre por file:// — precisa ser servido por HTTP.
    const { servidor, endereco } = await servirPasta(path.dirname(relatorio));

    try {
      await page.goto(endereco);
      await expect(page.getByText(/Passed/)).toBeVisible();

      // O relatório em disco é o da execução ANTERIOR (esta ainda não terminou). Se ele
      // não tiver nenhum teste aprovado, a evidência seria enganosa — melhor avisar.
      const resumo = (await page.evaluate(() => document.body.innerText ?? '')).slice(0, 600);
      const aprovados = Number((resumo.match(/Passed\s*(\d+)/) ?? ['', '0'])[1]);
      test.skip(
        aprovados === 0,
        'O relatório HTML atual não tem testes aprovados. Rode `npm test` antes de `npm run evidencias`.',
      );

      await evidencia.capturar('relatorio html da suite', { paginaInteira: true });
      await evidencia.exibirPainel('I4 — resultado da execução da suíte', [
        { rotulo: 'Comando', conteudo: 'npm test   (projetos api + setup-portal + web)' },
        { rotulo: 'Resumo lido do relatório HTML', conteudo: resumo },
      ]);
      await evidencia.capturar('resumo da execucao');
    } finally {
      await new Promise((resolver) => servidor.close(resolver));
    }
  });
});

test.describe('Evidências das notas — fluxos públicos', () => {
  test.use(SEM_SESSAO);

  test('I2 · o login com MFA é automatizado pelo cálculo do código TOTP', async ({ page, evidencia }) => {
    const dados = novoProfissional();

    // Pré-condição por API: o cadastro não é o objeto desta evidência
    const cadastro = await page.request.post(`${config.apiBaseURL}/api/v1/professionals`, { data: dados });
    expect(cadastro.status()).toBe(201);

    // 1ª etapa: senha
    await page.goto('/login');
    await page.getByLabel('E-mail').fill(dados.email);
    await page.getByLabel('Senha').fill(dados.password);
    await evidencia.capturar('primeira etapa com e-mail e senha');

    const respostaSetup = page.waitForResponse(
      (resposta) => resposta.url().includes('/auth/professional/mfa/setup') && resposta.status() === 200,
    );
    await page.getByRole('button', { name: 'Entrar' }).click();
    const { provisioning_uri: provisioningUri } = await (await respostaSetup).json();

    // 2ª etapa: a tela entrega o QR Code e o segredo otpauth://
    await expect(page.locator('svg[width="200"]')).toBeVisible();
    await evidencia.capturar('qr code e segredo otpauth na tela');

    // O código é calculado pela automação a partir desse segredo
    const segredo = extrairSegredoDaUri(provisioningUri);
    const codigo = gerarCodigoTotp(segredo);

    await page.getByLabel('Código de 6 dígitos').fill(codigo);
    await evidencia.capturar('codigo totp calculado e preenchido');

    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    await evidencia.capturar('login concluido com mfa');

    // Fecha a evidência explicando de onde saiu o código usado acima
    await evidencia.exibirPainel('I2 — cálculo do código TOTP pela automação', [
      {
        rotulo: 'Segredo entregue pela própria tela (provisioning_uri)',
        conteudo: `${provisioningUri}\n\nsecret = ${segredo}`,
      },
      {
        rotulo: 'Código calculado em support/totp.js (HMAC-SHA1, janela de 30 s, 6 dígitos)',
        conteudo: `${codigo}\n\nMesmo algoritmo que o backend valida com pyotp — conferido na sessão de teste.`,
      },
    ]);
    await evidencia.capturar('de onde saiu o codigo totp');
  });

  test('I5 · o que a aplicação faz bem: mensagens genéricas e exclusão com confirmação', async ({
    page,
    evidencia,
  }) => {
    const dados = novoProfissional();
    const cadastro = await page.request.post(`${config.apiBaseURL}/api/v1/professionals`, { data: dados });
    expect(cadastro.status()).toBe(201);

    // 1. Senha errada de um e-mail que EXISTE
    await page.goto('/login');
    await page.getByLabel('E-mail').fill(dados.email);
    await page.getByLabel('Senha').fill('SenhaErrada123');
    await page.getByRole('button', { name: 'Entrar' }).click();
    await expect(page.getByRole('alert')).toHaveText('E-mail ou senha inválidos');
    await evidencia.capturar('mensagem generica para e-mail existente');

    // 2. E-mail que NÃO existe: mensagem idêntica, não dá para descobrir quem tem conta
    await page.goto('/login');
    await page.getByLabel('E-mail').fill(`fantasma.${Date.now()}@example.com`);
    await page.getByLabel('Senha').fill(dados.password);
    await page.getByRole('button', { name: 'Entrar' }).click();
    await expect(page.getByRole('alert')).toHaveText('E-mail ou senha inválidos');
    await evidencia.capturar('mesma mensagem para e-mail inexistente');

    // 3. Recuperação de acesso também não revela se o e-mail existe
    await page.goto('/password-reset');
    await page.getByLabel('E-mail').fill(`fantasma.${Date.now()}@example.com`);
    await page.getByRole('button', { name: 'Solicitar recuperação' }).click();
    await expect(page.getByText(/Se o e-mail existir/)).toBeVisible();
    await evidencia.capturar('recuperacao de acesso sem revelar o e-mail');

    // 4. A exclusão de medicamento exige confirmação explícita (RN16), documentada no contrato
    await page.goto(`${config.apiBaseURL}/docs`);
    const resumoExclusao = page.getByText(/requer confirmação explícita/).first();
    await resumoExclusao.scrollIntoViewIfNeeded();
    await expect(resumoExclusao).toBeVisible();
    await evidencia.capturar('exclusao com confirmacao explicita no contrato');
  });
});
