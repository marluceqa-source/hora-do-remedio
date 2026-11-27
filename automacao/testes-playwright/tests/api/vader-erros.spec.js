/**
 * VADER — pilar E (Errors): o erro precisa dizer a causa, no código de status certo e
 * com um corpo previsível, sem vazar detalhe interno nem transformar entrada inválida
 * em 500.
 *
 * Casos de teste: CT-API-E01 a CT-API-E15.
 */

const { test, expect } = require('../../fixtures');
const { SENHA_PADRAO, novoMedicamento, novoPaciente, novoProfissional } = require('../../support/dados');
const { cadastrarProfissional, criarPaciente } = require('../../support/portal');

/** Igual a PROFESSIONAL_MAX_FAILED_LOGINS no .env da aplicação. */
const TENTATIVAS_ATE_BLOQUEIO = Number(process.env.TENTATIVAS_ATE_BLOQUEIO ?? 5);

test.describe('VADER · Errors — validação de entrada (422)', () => {
  test('CT-API-E01 · o erro de validação tem sempre o mesmo formato', async ({ contextoPaciente }) => {
    const resposta = await contextoPaciente.api.post('/api/v1/medications', { data: {} });

    expect(resposta.status()).toBe(422);
    const corpo = await resposta.json();
    expect(corpo.code).toBe('validation_error');
    expect(Array.isArray(corpo.detail)).toBe(true);
    expect(corpo.detail.length).toBeGreaterThan(0);
    for (const item of corpo.detail) {
      expect(item).toHaveProperty('type');
      expect(item).toHaveProperty('loc');
      expect(item).toHaveProperty('msg');
    }
  });

  test('CT-API-E02 · campo obrigatório ausente aponta exatamente o campo', async ({ contextoPaciente }) => {
    const { start_date: _ignorado, ...semDataInicio } = novoMedicamento();

    const resposta = await contextoPaciente.api.post('/api/v1/medications', { data: semDataInicio });

    expect(resposta.status()).toBe(422);
    const detalhe = (await resposta.json()).detail;
    expect(detalhe).toEqual(
      expect.arrayContaining([expect.objectContaining({ type: 'missing', loc: ['body', 'start_date'] })]),
    );
  });

  test('CT-API-E03 · data de término anterior ao início é recusada com a regra em texto', async ({
    contextoPaciente,
  }) => {
    const resposta = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ start_date: '2026-11-20', end_date: '2026-11-10' }),
    });

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).detail[0].msg).toContain('end_date não pode ser anterior a start_date');
  });

  test('CT-API-E04 · medicamento sem nenhum horário é recusado (RN02)', async ({ contextoPaciente }) => {
    const resposta = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ schedules: [] }),
    });

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).detail[0]).toMatchObject({ type: 'too_short', loc: ['body', 'schedules'] });
  });

  test('CT-API-E05 · recorrência diária sem horário e semanal sem dias são recusadas', async ({
    contextoPaciente,
  }) => {
    const diariaSemHorario = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ schedules: [{ recurrence_type: 'daily' }] }),
    });
    const semanalSemDias = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ schedules: [{ recurrence_type: 'weekly', schedule_time: '09:00' }] }),
    });

    expect(diariaSemHorario.status()).toBe(422);
    expect((await diariaSemHorario.json()).detail[0].msg).toContain('schedule_time é obrigatório');

    expect(semanalSemDias.status()).toBe(422);
    expect((await semanalSemDias.json()).detail[0].msg).toContain('weekdays é obrigatório');
  });

  test('CT-API-E06 · identificador de recurso com tipo errado devolve 422, não 500', async ({
    contextoPaciente,
  }) => {
    const resposta = await contextoPaciente.api.get('/api/v1/medications/abc');

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).detail[0].loc).toEqual(['path', 'medication_id']);
  });

  test('CT-API-E07 · senha curta no cadastro de profissional é recusada (mínimo 8)', async ({ api }) => {
    const resposta = await api.post('/api/v1/professionals', {
      data: novoProfissional({ password: '1234567' }),
    });

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).detail[0]).toMatchObject({
      type: 'string_too_short',
      loc: ['body', 'password'],
    });
  });

  test('CT-API-E08 · e-mail com domínio reservado é recusado pelo validador (ex.: .test)', async ({ api }) => {
    // Heurística de tipos de dados: nome/domínio inexistente ou reservado. Vale registrar
    // porque é uma pegadinha de massa de teste — e-mail "@exemplo.test" nunca é aceito.
    const resposta = await api.post('/api/v1/professionals', {
      data: novoProfissional({ email: 'qa.dominio.reservado@exemplo.test' }),
    });

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).detail[0].loc).toEqual(['body', 'email']);
  });
});

test.describe('VADER · Errors — recurso inexistente e conflito', () => {
  test('CT-API-E09 · medicamento inexistente devolve 404 com causa legível', async ({ contextoPaciente }) => {
    const resposta = await contextoPaciente.api.get('/api/v1/medications/99999999');

    expect(resposta.status()).toBe(404);
    expect((await resposta.json()).detail).toBe('Medicamento não encontrado');
  });

  test('CT-API-E10 · e-mail de profissional já cadastrado devolve 409', async ({ api }) => {
    // Dado um profissional já cadastrado
    const { dados } = await cadastrarProfissional(api);

    // Quando tento cadastrar o mesmo e-mail outra vez
    const resposta = await api.post('/api/v1/professionals', { data: dados });

    // Então o conflito é explícito — e não um 500 ou um 422 genérico
    expect(resposta.status()).toBe(409);
    expect((await resposta.json()).detail).toBe('E-mail já cadastrado');
  });

  test('CT-API-E11 · identificador interno de paciente repetido devolve 409', async ({
    contextoProfissional,
  }) => {
    const { dados } = await criarPaciente(contextoProfissional.api);

    const resposta = await contextoProfissional.api.post('/api/v1/patients', {
      data: novoPaciente({ internal_identifier: dados.internal_identifier }),
    });

    expect(resposta.status()).toBe(409);
    expect((await resposta.json()).detail).toBe('Já existe um paciente com este identificador interno');
  });
});

test.describe('VADER · Errors — autenticação do portal', () => {
  test('CT-API-E12 · senha errada e e-mail inexistente devolvem a MESMA mensagem (401)', async ({ api }) => {
    const { dados } = await cadastrarProfissional(api);

    const senhaErrada = await api.post('/api/v1/auth/professional/login', {
      data: { email: dados.email, password: 'SenhaCompletamenteErrada1' },
    });
    const emailInexistente = await api.post('/api/v1/auth/professional/login', {
      data: { email: `nao.existe.${Date.now()}@example.com`, password: SENHA_PADRAO },
    });

    // Mensagem genérica nos dois casos: não revela se o e-mail existe
    expect(senhaErrada.status()).toBe(401);
    expect(emailInexistente.status()).toBe(401);
    expect((await senhaErrada.json()).detail).toBe('E-mail ou senha inválidos');
    expect((await emailInexistente.json()).detail).toBe('E-mail ou senha inválidos');
  });

  test('CT-API-E13 · código MFA incorreto é recusado e token de recuperação inválido devolve 400', async ({
    api,
  }) => {
    const { dados } = await cadastrarProfissional(api);

    const login = await api.post('/api/v1/auth/professional/login', {
      data: { email: dados.email, password: dados.password },
    });
    const { pre_auth_token: preAuthToken } = await login.json();
    await api.post('/api/v1/auth/professional/mfa/setup', { data: { pre_auth_token: preAuthToken } });

    const codigoErrado = await api.post('/api/v1/auth/professional/mfa/confirm', {
      data: { pre_auth_token: preAuthToken, code: '000000' },
    });
    expect(codigoErrado.status()).toBe(401);
    expect((await codigoErrado.json()).detail).toBe('Código de verificação inválido');

    // Código com tamanho fora do contrato é barrado antes, na validação (6 dígitos)
    const codigoCurto = await api.post('/api/v1/auth/professional/mfa/confirm', {
      data: { pre_auth_token: preAuthToken, code: '123' },
    });
    expect(codigoCurto.status()).toBe(422);

    const resetInvalido = await api.post('/api/v1/auth/professional/password-reset/confirm', {
      data: { token: 'token-que-nunca-existiu', new_password: 'OutraSenha123' },
    });
    expect(resetInvalido.status()).toBe(400);
    expect((await resetInvalido.json()).detail).toBe('Token inválido ou expirado');
  });

  test('CT-API-E14 · recuperação de acesso responde 202 sem revelar se o e-mail existe', async ({ api }) => {
    const { dados } = await cadastrarProfissional(api);

    const existente = await api.post('/api/v1/auth/professional/password-reset/request', {
      data: { email: dados.email },
    });
    const inexistente = await api.post('/api/v1/auth/professional/password-reset/request', {
      data: { email: `fantasma.${Date.now()}@example.com` },
    });

    expect(existente.status()).toBe(202);
    expect(inexistente.status()).toBe(202);
    expect(await existente.json()).toEqual(await inexistente.json());
  });

  test(`CT-API-E15 · conta é bloqueada depois de ${TENTATIVAS_ATE_BLOQUEIO} senhas erradas (423)`, async ({
    api,
  }) => {
    // Dado um profissional recém-cadastrado
    const { dados } = await cadastrarProfissional(api);

    // Quando erro a senha o número de vezes configurado
    for (let tentativa = 1; tentativa <= TENTATIVAS_ATE_BLOQUEIO; tentativa += 1) {
      const resposta = await api.post('/api/v1/auth/professional/login', {
        data: { email: dados.email, password: `errada-${tentativa}` },
      });
      expect(resposta.status(), `tentativa ${tentativa}`).toBe(401);
    }

    // Então nem a senha correta entra: a conta está temporariamente bloqueada
    const comSenhaCorreta = await api.post('/api/v1/auth/professional/login', {
      data: { email: dados.email, password: dados.password },
    });

    expect(comSenhaCorreta.status()).toBe(423);
    expect((await comSenhaCorreta.json()).detail).toContain('Conta temporariamente bloqueada');
  });
});
