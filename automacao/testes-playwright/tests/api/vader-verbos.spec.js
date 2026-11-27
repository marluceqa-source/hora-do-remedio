/**
 * VADER — pilar V (Verbs): cada verbo HTTP faz o que promete e o que não é suportado
 * responde 405 em vez de um comportamento inesperado.
 *
 * Casos de teste descritos em docs/casos-de-teste-api-vader.md (CT-API-V01 a CT-API-V10).
 */

const { test, expect } = require('../../fixtures');
const { novoMedicamento } = require('../../support/dados');

test.describe('VADER · Verbs — verbos HTTP dos recursos de medicamento', () => {
  test('CT-API-V01 · POST /api/v1/auth/token emite token de acesso do paciente', async ({ api }) => {
    // Dado um identificador de usuário do Telegram
    const telegramUserId = 912345678;

    // Quando solicito um token de acesso
    const resposta = await api.post('/api/v1/auth/token', {
      data: { telegram_user_id: telegramUserId, timezone: 'America/Sao_Paulo' },
    });

    // Então recebo 200 com um token bearer e o prazo de expiração
    expect(resposta.status()).toBe(200);
    const corpo = await resposta.json();
    expect(corpo).toMatchObject({ token_type: 'bearer' });
    expect(corpo.access_token).toMatch(/^[\w-]+\.[\w-]+\.[\w-]+$/);
    expect(typeof corpo.expires_in).toBe('number');
    expect(corpo.expires_in).toBeGreaterThan(0);
  });

  test('CT-API-V02 · POST /api/v1/medications cadastra o medicamento com o horário informado', async ({
    contextoPaciente,
  }) => {
    // Dado um medicamento válido com um horário diário (RN02)
    const medicamento = novoMedicamento();

    // Quando cadastro o medicamento
    const resposta = await contextoPaciente.api.post('/api/v1/medications', { data: medicamento });

    // Então recebo 201 com o recurso criado e o horário persistido
    expect(resposta.status()).toBe(201);
    const criado = await resposta.json();
    expect(criado).toMatchObject({
      name: medicamento.name,
      dosage: medicamento.dosage,
      quantity: medicamento.quantity,
      active: true,
    });
    expect(criado.id).toBeGreaterThan(0);
    expect(criado.schedules).toHaveLength(1);
    expect(criado.schedules[0]).toMatchObject({
      recurrence_type: 'daily',
      schedule_time: '08:00:00',
      timezone: 'America/Sao_Paulo',
    });
  });

  test('CT-API-V03 · GET /api/v1/medications lista os medicamentos do próprio usuário', async ({
    contextoPaciente,
  }) => {
    // Dado dois medicamentos cadastrados
    const primeiro = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const segundo = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    expect([primeiro.status(), segundo.status()]).toEqual([201, 201]);

    // Quando consulto a lista
    const resposta = await contextoPaciente.api.get('/api/v1/medications');

    // Então os dois aparecem — e somente eles
    expect(resposta.ok()).toBeTruthy();
    const lista = await resposta.json();
    expect(Array.isArray(lista)).toBe(true);
    expect(lista).toHaveLength(2);
    expect(lista.map((item) => item.id)).toEqual(
      expect.arrayContaining([(await primeiro.json()).id, (await segundo.json()).id]),
    );
  });

  test('CT-API-V04 · GET /api/v1/medications/{id} consulta um medicamento específico', async ({
    contextoPaciente,
  }) => {
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const criado = await criacao.json();

    const resposta = await contextoPaciente.api.get(`/api/v1/medications/${criado.id}`);

    expect(resposta.status()).toBe(200);
    expect(await resposta.json()).toMatchObject({ id: criado.id, name: criado.name });
  });

  test('CT-API-V05 · PATCH /api/v1/medications/{id} altera apenas o campo enviado', async ({
    contextoPaciente,
  }) => {
    // Dado um medicamento cadastrado com dose de 50mg
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const criado = await criacao.json();

    // Quando altero somente a dose
    const resposta = await contextoPaciente.api.patch(`/api/v1/medications/${criado.id}`, {
      data: { dosage: '100mg' },
    });

    // Então a dose muda e o resto permanece
    expect(resposta.status()).toBe(200);
    const atualizado = await resposta.json();
    expect(atualizado.dosage).toBe('100mg');
    expect(atualizado.name).toBe(criado.name);
    expect(atualizado.quantity).toBe(criado.quantity);
    expect(atualizado.schedules).toHaveLength(1);
  });

  test('CT-API-V06 · DELETE sem confirmação explícita é recusado (RN16)', async ({ contextoPaciente }) => {
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const criado = await criacao.json();

    // Quando tento excluir sem confirm=true
    const resposta = await contextoPaciente.api.delete(`/api/v1/medications/${criado.id}`);

    // Então a exclusão é recusada com 400 e o medicamento continua lá
    expect(resposta.status()).toBe(400);
    expect((await resposta.json()).detail).toContain('confirm=true');

    const consulta = await contextoPaciente.api.get(`/api/v1/medications/${criado.id}`);
    expect(consulta.status()).toBe(200);
  });

  test('CT-API-V07 · DELETE com confirm=true exclui e o recurso deixa de existir', async ({
    contextoPaciente,
  }) => {
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const criado = await criacao.json();

    const exclusao = await contextoPaciente.api.delete(`/api/v1/medications/${criado.id}`, {
      params: { confirm: true },
    });
    expect(exclusao.status()).toBe(204);

    const consulta = await contextoPaciente.api.get(`/api/v1/medications/${criado.id}`);
    expect(consulta.status()).toBe(404);
  });

  test('CT-API-V08 · PUT em /api/v1/medications/{id} não é suportado (405)', async ({ contextoPaciente }) => {
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const criado = await criacao.json();

    // A atualização é parcial, por PATCH — PUT não existe neste recurso
    const resposta = await contextoPaciente.api.put(`/api/v1/medications/${criado.id}`, {
      data: { name: 'Qualquer' },
    });

    expect(resposta.status()).toBe(405);
  });

  test('CT-API-V09 · DELETE em /health não é suportado (405)', async ({ api }) => {
    const resposta = await api.delete('/health');
    expect(resposta.status()).toBe(405);
  });

  test('CT-API-V10 · GET /api/v1/schedules devolve os horários dos medicamentos do usuário', async ({
    contextoPaciente,
  }) => {
    // Dado um medicamento com horário semanal
    const medicamento = novoMedicamento({
      schedules: [{ recurrence_type: 'weekly', schedule_time: '07:30', weekdays: 'mon,wed,fri' }],
    });
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: medicamento });
    const criado = await criacao.json();

    // Quando consulto os agendamentos
    const resposta = await contextoPaciente.api.get('/api/v1/schedules');

    // Então o horário semanal cadastrado aparece vinculado ao medicamento
    expect(resposta.ok()).toBeTruthy();
    const horarios = await resposta.json();
    expect(horarios).toHaveLength(1);
    expect(horarios[0]).toMatchObject({
      medication_id: criado.id,
      recurrence_type: 'weekly',
      schedule_time: '07:30:00',
      weekdays: 'mon,wed,fri',
    });
  });
});
