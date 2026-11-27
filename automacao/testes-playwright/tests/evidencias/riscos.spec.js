/**
 * Evidências dos RISCOS do relatório de sessão (R1 a R5).
 *
 * Cada teste reproduz o risco pelo caminho em que ele é observável e grava vídeo +
 * screenshots em `evidencias/`. Os testes também ASSERTAM o comportamento: se a
 * aplicação for corrigida, a evidência falha e avisa que o relatório ficou desatualizado.
 *
 * Arquivos gerados: evidencias/R<n>-<seq>-<rótulo>.png e evidencias/R<n>-video.webm
 */

const { execSync } = require('node:child_process');
const { spawn } = require('node:child_process');
const path = require('node:path');

const { test, expect } = require('../../fixtures/evidencias');
const config = require('../../support/config');
const { gerarCodigoDaUri } = require('../../support/totp');
const { novoPaciente, novoProfissional } = require('../../support/dados');

const SEM_SESSAO = { storageState: { cookies: [], origins: [] } };

/** Texto da página sem normalização de espaços — necessário para evidenciar o R3. */
async function textoCru(page) {
  return page.evaluate(() => document.body.textContent ?? '');
}

/** Faz o cadastro do profissional pela tela e devolve os dados usados. */
async function cadastrarPelaTela(page, dados) {
  await page.goto('/signup');
  await page.getByLabel('Nome completo').fill(dados.full_name);
  await page.getByLabel('E-mail').fill(dados.email);
  await page.getByLabel('Senha').fill(dados.password);
  await page.getByLabel('Profissão').fill(dados.profession);
  await page.getByRole('button', { name: 'Criar conta' }).click();
  return dados;
}

/** Faz o login completo pela tela (senha + TOTP lido da própria página). */
async function entrarPelaTela(page, dados) {
  await page.goto('/login');
  await page.getByLabel('E-mail').fill(dados.email);
  await page.getByLabel('Senha').fill(dados.password);

  const respostaSetup = page.waitForResponse(
    (resposta) => resposta.url().includes('/auth/professional/mfa/setup') && resposta.status() === 200,
  );
  await page.getByRole('button', { name: 'Entrar' }).click();
  const { provisioning_uri: provisioningUri } = await (await respostaSetup).json();

  return provisioningUri;
}

test.describe('Evidências dos riscos — fluxos públicos', () => {
  test.use(SEM_SESSAO);

  test('R1 · profissional não verificado já tem acesso clínico', async ({ page, evidencia }) => {
    const dados = novoProfissional();

    // 1. A tela de cadastro promete que a conta passa por verificação do administrador
    await cadastrarPelaTela(page, dados);
    await expect(page.getByText(/Cadastro recebido!/)).toBeVisible();
    await evidencia.capturar('promessa de verificacao pelo administrador');

    // 2. Mesmo assim, o primeiro acesso é concluído normalmente
    const provisioningUri = await entrarPelaTela(page, dados);
    await page.getByLabel('Código de 6 dígitos').fill(gerarCodigoDaUri(provisioningUri));
    await page.getByRole('button', { name: 'Confirmar e entrar' }).click();
    await expect(page.getByRole('heading', { name: 'Dashboard', level: 1 })).toBeVisible();
    await evidencia.capturar('dashboard aberto no primeiro acesso');

    // 3. O perfil devolvido pela API mostra verification_status "pending"
    await page.goto(`${config.apiBaseURL}/api/v1/professionals/me`);
    expect(await textoCru(page)).toContain('"verification_status":"pending"');
    await evidencia.capturar('perfil da api com verification status pending');

    // 4. E, pendente de verificação, a conta cadastra paciente — dado clínico
    const paciente = novoPaciente();
    await page.goto('/patients/new');
    await page.getByLabel('Nome completo').fill(paciente.full_name);
    await page.getByLabel('Identificador interno').fill(paciente.internal_identifier);
    await page.getByRole('button', { name: 'Cadastrar' }).click();
    await expect(page.getByRole('heading', { name: paciente.full_name, level: 1 })).toBeVisible();
    await evidencia.capturar('paciente cadastrado por conta pendente');

    // 5. Inclusive gera o convite de vínculo do paciente ao Telegram
    await page.getByRole('button', { name: 'Gerar convite' }).click();
    await expect(page.getByText(/Válido até/)).toBeVisible();
    await evidencia.capturar('convite de vinculo gerado por conta pendente', { paginaInteira: true });
  });

  test('R2 · campo obrigatório aceita um nome formado só por espaços', async ({ page, evidencia }) => {
    // O nome exige no mínimo 1 caractere — e espaço é um caractere. Nem a validação da
    // tela (zod) nem a do servidor (Pydantic) fazem trim antes de medir o tamanho.
    const dados = novoProfissional({ full_name: '   ' });

    await page.goto('/signup');
    await page.getByLabel('Nome completo').fill(dados.full_name);
    await page.getByLabel('E-mail').fill(dados.email);
    await page.getByLabel('Senha').fill(dados.password);
    await page.getByLabel('Profissão').fill(dados.profession);
    await evidencia.capturar('formulario com nome formado so por espacos');

    const respostaCadastro = page.waitForResponse(
      (resposta) => resposta.url().includes('/api/v1/professionals') && resposta.request().method() === 'POST',
    );
    await page.getByRole('button', { name: 'Criar conta' }).click();

    // O cadastro é aceito com 201 — nenhuma mensagem de erro aparece
    const resposta = await respostaCadastro;
    expect(resposta.status()).toBe(201);
    expect((await resposta.json()).full_name).toBe('   ');
    await expect(page.getByText(/Cadastro recebido!/)).toBeVisible();
    await evidencia.capturar('cadastro aceito com nome em branco');

    // Para contraste: o nome vazio de verdade é corretamente recusado
    await page.goto('/signup');
    await page.getByLabel('E-mail').fill(novoProfissional().email);
    await page.getByLabel('Senha').fill(dados.password);
    await page.getByLabel('Profissão').fill(dados.profession);
    await page.getByRole('button', { name: 'Criar conta' }).click();
    await expect(page.getByText('Informe o nome completo')).toBeVisible();
    await evidencia.capturar('contraste nome vazio e recusado');
  });
});

test.describe('Evidências dos riscos — portal autenticado', () => {
  test('R3 · nenhum campo de texto é normalizado (espaços nas bordas)', async ({ page, evidencia }) => {
    // Dois pacientes cujo nome a pessoa lê como igual: um com espaços nas bordas, outro sem.
    const nomeBase = `Ana Clara Fictícia ${Date.now().toString(36)}`;
    const comEspacos = novoPaciente({ full_name: `   ${nomeBase}   ` });
    const semEspacos = novoPaciente({ full_name: nomeBase });

    for (const paciente of [comEspacos, semEspacos]) {
      await page.goto('/patients/new');
      await page.getByLabel('Nome completo').fill(paciente.full_name);
      await page.getByLabel('Identificador interno').fill(paciente.internal_identifier);
      await page.getByRole('button', { name: 'Cadastrar' }).click();
      await expect(page).toHaveURL(/\/patients\/\d+$/);
    }
    await evidencia.capturar('segundo paciente cadastrado com o mesmo nome');

    // Na lista, os dois convivem e parecem o mesmo paciente
    await page.goto('/patients');
    const duplicados = page.getByRole('link').filter({ hasText: nomeBase });
    await expect(duplicados).toHaveCount(2);
    await evidencia.capturar('dois pacientes visualmente identicos na lista', { paginaInteira: true });

    // A API mostra que a diferença são apenas os espaços guardados no banco
    await page.goto(`${config.apiBaseURL}/api/v1/patients`);
    // textContent cru: o matcher de texto do Playwright normalizaria justamente os
    // espaços que são a evidência deste risco.
    expect(await textoCru(page)).toContain(`"full_name":"   ${nomeBase}   "`);
    await evidencia.capturar('api devolvendo o nome com os espacos preservados');
  });
});

test.describe('Evidências dos riscos — ambiente e infraestrutura', () => {
  test.use(SEM_SESSAO);

  test('R4 · o limite de requisições é por IP, e não por usuário', async ({ page, evidencia }) => {
    // Sobe uma segunda instância da API com limite baixo, só para esta evidência.
    const porta = 8001;
    const limite = 3;
    const servidor = spawn(
      config.pythonBin,
      ['-m', 'uvicorn', 'api.main:app', '--host', '0.0.0.0', '--port', String(porta)],
      {
        cwd: config.diretorioApp,
        env: { ...process.env, DATABASE_URL: config.testDatabaseUrl, RATE_LIMIT_PER_MINUTE: String(limite) },
        stdio: 'ignore',
      },
    );

    try {
      // Espera a instância responder
      await expect
        .poll(
          async () => {
            try {
              return (await page.request.get(`http://localhost:${porta}/health`)).status();
            } catch {
              return 0;
            }
          },
          { timeout: 60_000, intervals: [500] },
        )
        .toBe(200);

      // Sem nenhuma credencial: o navegador consome a cota do IP em poucas chamadas
      let statusFinal = 200;
      for (let chamada = 1; chamada <= limite + 2; chamada += 1) {
        const resposta = await page.goto(`http://localhost:${porta}/health?chamada=${chamada}`);
        statusFinal = resposta.status();
        if (chamada === 1) await evidencia.capturar('primeira chamada dentro do limite');
        if (statusFinal === 429) break;
      }

      expect(statusFinal).toBe(429);
      await expect(page.getByText(/Rate limit exceeded/i)).toBeVisible();
      await evidencia.capturar('limite estourado sem autenticacao nenhuma');

      await evidencia.exibirPainel('R4 — limite por IP, não por usuário', [
        {
          rotulo: `Configuração da instância usada nesta evidência (porta ${porta})`,
          conteudo: `RATE_LIMIT_PER_MINUTE=${limite}\nchave do limite: get_remote_address (IP de origem)`,
        },
        {
          rotulo: 'Resultado',
          conteudo:
            `Depois de ${limite} chamadas a GET /health, a seguinte respondeu ${statusFinal}.\n` +
            'Nenhuma credencial foi enviada: a cota é do IP. Bot e portal atrás do mesmo IP\n' +
            '(NAT, proxy, contêiner) dividem essa cota, e um pode derrubar o outro.',
        },
      ]);
      await evidencia.capturar('resumo do risco de limite por ip');
    } finally {
      servidor.kill('SIGTERM');
    }
  });

  test('R5 · o venv da aplicação tem shebang quebrado', async ({ page, evidencia }) => {
    /** Roda um comando no shell e devolve a saída real, com sucesso ou falha. */
    function rodar(comando) {
      try {
        const saida = execSync(`${comando} 2>&1`, {
          cwd: config.diretorioApp,
          encoding: 'utf-8',
          shell: '/bin/zsh',
        });
        return { ok: true, saida: saida.trim() };
      } catch (erro) {
        return { ok: false, saida: String(erro.stdout ?? erro.message).trim() };
      }
    }

    const executavelQuebrado = rodar('.venv/bin/alembic --version');
    const contorno = rodar('.venv/bin/python -m alembic --version');
    const configuracaoDoVenv = rodar('grep command .venv/pyvenv.cfg');

    await evidencia.exibirPainel('R5 — executáveis do venv com shebang quebrado', [
      {
        rotulo: '$ .venv/bin/alembic --version   (como a documentação da aplicação manda rodar)',
        conteudo: executavelQuebrado.saida,
      },
      {
        rotulo: '$ grep command .venv/pyvenv.cfg   (o venv aponta para o caminho ANTIGO da pasta)',
        conteudo: configuracaoDoVenv.saida,
      },
      {
        rotulo: '$ .venv/bin/python -m alembic --version   (contorno adotado pela automação)',
        conteudo: contorno.saida,
      },
    ]);
    await evidencia.capturar('saida real dos comandos do venv', { paginaInteira: true });

    // O risco está confirmado enquanto o executável falhar e o contorno funcionar
    expect(executavelQuebrado.ok).toBe(false);
    expect(executavelQuebrado.saida).toMatch(/bad interpreter|No such file|not found/i);
    expect(contorno.ok).toBe(true);
  });
});
