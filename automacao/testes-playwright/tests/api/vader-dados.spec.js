/**
 * VADER — pilar D (Data): estrutura e tipos do retorno, valores padrão, limites de
 * tamanho e tratamento de caracteres.
 *
 * Os dados de entrada seguem as heurísticas de ataque a tipos de dados e a strings
 * (material da Test Obsessed / Elisabeth Hendrickson): nome longo, caracteres acentuados
 * e asiáticos, delimitadores, injeção de SQL, campo em branco e espaços nas bordas.
 *
 * Casos de teste: CT-API-D01 a CT-API-D12.
 */

const { test, expect } = require('../../fixtures');
const { HEURISTICAS_STRING, dataISO, novoMedicamento } = require('../../support/dados');
const { criarPaciente } = require('../../support/portal');

test.describe('VADER · Data — contrato e tipos do recurso de medicamento', () => {
  test('CT-API-D01 · o medicamento criado devolve todos os campos do contrato com os tipos esperados', async ({
    contextoPaciente,
  }) => {
    const resposta = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const corpo = await resposta.json();

    expect(Object.keys(corpo).sort()).toEqual(
      [
        'active',
        'audio_text',
        'dosage',
        'end_date',
        'id',
        'instructions',
        'name',
        'photo_path',
        'quantity',
        'schedules',
        'start_date',
        'user_id',
      ].sort(),
    );

    expect(typeof corpo.id).toBe('number');
    expect(typeof corpo.user_id).toBe('number');
    expect(typeof corpo.name).toBe('string');
    expect(typeof corpo.active).toBe('boolean');
    expect(corpo.start_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    expect(Array.isArray(corpo.schedules)).toBe(true);
    expect(Object.keys(corpo.schedules[0]).sort()).toEqual(
      ['id', 'medication_id', 'recurrence_type', 'schedule_time', 'interval_hours', 'weekdays', 'timezone'].sort(),
    );
  });

  test('CT-API-D02 · campos opcionais vêm nulos e os padrões são aplicados', async ({ contextoPaciente }) => {
    // Dado um cadastro informando só os campos obrigatórios
    const minimo = {
      name: 'Medicamento Mínimo',
      dosage: '1mg',
      quantity: '1 gota',
      start_date: dataISO(0),
      schedules: [{ recurrence_type: 'daily', schedule_time: '06:00' }],
    };

    const resposta = await contextoPaciente.api.post('/api/v1/medications', { data: minimo });

    // Então os opcionais vêm nulos, o medicamento nasce ativo e o fuso é o do usuário
    expect(resposta.status()).toBe(201);
    const corpo = await resposta.json();
    expect(corpo).toMatchObject({
      instructions: null,
      audio_text: null,
      photo_path: null,
      end_date: null,
      active: true,
    });
    expect(corpo.schedules[0].timezone).toBe('America/Sao_Paulo');
    expect(corpo.schedules[0].interval_hours).toBeNull();
    expect(corpo.schedules[0].weekdays).toBeNull();
  });

  test('CT-API-D03 · nome aceita 200 caracteres e recusa 201 (heurística: nome longo)', async ({
    contextoPaciente,
  }) => {
    const noLimite = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ name: HEURISTICAS_STRING.textoLongo(200) }),
    });
    const acimaDoLimite = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ name: HEURISTICAS_STRING.textoLongo(201) }),
    });

    expect(noLimite.status()).toBe(201);
    expect((await noLimite.json()).name).toHaveLength(200);

    expect(acimaDoLimite.status()).toBe(422);
    expect((await acimaDoLimite.json()).detail[0]).toMatchObject({
      type: 'string_too_long',
      loc: ['body', 'name'],
    });
  });

  test('CT-API-D04 · acentos, caracteres asiáticos e delimitadores são preservados', async ({
    contextoPaciente,
  }) => {
    const nomes = [
      HEURISTICAS_STRING.acentuado,
      HEURISTICAS_STRING.asiatico,
      HEURISTICAS_STRING.delimitadores,
    ];

    const criados = [];
    for (const nome of nomes) {
      const resposta = await contextoPaciente.api.post('/api/v1/medications', {
        data: novoMedicamento({ name: nome }),
      });
      expect(resposta.status(), `nome recusado: ${nome}`).toBe(201);
      expect((await resposta.json()).name).toBe(nome);
      criados.push(nome);
    }

    // E a leitura posterior devolve exatamente o que foi gravado (sem perda de encoding)
    const lista = await contextoPaciente.api.get('/api/v1/medications');
    expect((await lista.json()).map((item) => item.name).sort()).toEqual(criados.sort());
  });

  test('CT-API-D05 · texto com injeção de SQL é gravado como literal e a base segue íntegra', async ({
    contextoPaciente,
  }) => {
    // Dado um nome com uma tentativa clássica de injeção
    const resposta = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ name: HEURISTICAS_STRING.injecaoSql }),
    });

    // Então ele é apenas um texto: nada é executado
    expect(resposta.status()).toBe(201);
    expect((await resposta.json()).name).toBe(HEURISTICAS_STRING.injecaoSql);

    // E a tabela continua respondendo normalmente depois disso
    const novoCadastro = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    expect(novoCadastro.status()).toBe(201);
    const lista = await contextoPaciente.api.get('/api/v1/medications');
    expect(lista.status()).toBe(200);
    expect(await lista.json()).toHaveLength(2);
  });

  test('CT-API-D06 · orientações aceitam 500 caracteres e recusam 501', async ({ contextoPaciente }) => {
    const noLimite = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ instructions: HEURISTICAS_STRING.textoLongo(500) }),
    });
    const acima = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ instructions: HEURISTICAS_STRING.textoLongo(501) }),
    });

    expect(noLimite.status()).toBe(201);
    expect(acima.status()).toBe(422);
    expect((await acima.json()).detail[0].loc).toEqual(['body', 'instructions']);
  });

  test('CT-API-D07 · intervalo entre doses respeita a faixa de 1 a 24 horas', async ({ contextoPaciente }) => {
    const casos = [
      { horas: 1, statusEsperado: 201 },
      { horas: 24, statusEsperado: 201 },
      { horas: 0, statusEsperado: 422 },
      { horas: 25, statusEsperado: 422 },
    ];

    for (const { horas, statusEsperado } of casos) {
      const resposta = await contextoPaciente.api.post('/api/v1/medications', {
        data: novoMedicamento({ schedules: [{ recurrence_type: 'interval', interval_hours: horas }] }),
      });

      expect(resposta.status(), `interval_hours=${horas}`).toBe(statusEsperado);
    }
  });

  test('CT-API-D08 · nome só com espaços é aceito hoje — risco R2 do relatório de sessão', async ({
    contextoPaciente,
  }) => {
    // Heurística "em branco": o campo exige no mínimo 1 caractere, e espaço conta como
    // caractere. O teste registra o comportamento ATUAL; o risco está no relatório de
    // sessão (docs/relatorio-de-sessao.md, R2) para decisão do time.
    const soEspacos = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ name: HEURISTICAS_STRING.somenteEspacos }),
    });
    const vazio = await contextoPaciente.api.post('/api/v1/medications', {
      data: novoMedicamento({ name: HEURISTICAS_STRING.vazio }),
    });

    expect(soEspacos.status()).toBe(201);
    expect((await soEspacos.json()).name).toBe(HEURISTICAS_STRING.somenteEspacos);

    expect(vazio.status()).toBe(422);
    expect((await vazio.json()).detail[0].type).toBe('string_too_short');
  });

  test('CT-API-D09 · relatório de adesão responde em JSON e em CSV', async ({ contextoPaciente }) => {
    const json = await contextoPaciente.api.get('/api/v1/reports');
    expect(json.status()).toBe(200);
    expect(json.headers()['content-type']).toContain('application/json');
    const resumo = await json.json();
    expect(Object.keys(resumo).sort()).toEqual(
      ['confirmation_rate', 'total_confirmed', 'total_not_taken', 'total_scheduled', 'total_unconfirmed'].sort(),
    );
    for (const [chave, valor] of Object.entries(resumo)) {
      expect(typeof valor, `campo ${chave}`).toBe('number');
    }

    const csv = await contextoPaciente.api.get('/api/v1/reports', { params: { format: 'csv' } });
    expect(csv.status()).toBe(200);
    expect(csv.headers()['content-type']).toContain('text/csv');
    expect(csv.headers()['content-disposition']).toContain('relatorio_hora_do_remedio.csv');
    const linhas = (await csv.text()).trim().split(/\r?\n/);
    expect(linhas[0]).toContain('total_scheduled');
    expect(linhas).toHaveLength(2);
  });
});

test.describe('VADER · Data — contrato do portal de profissionais', () => {
  test('CT-API-D10 · o paciente criado devolve o contrato esperado e nasce sem vínculo', async ({
    contextoProfissional,
  }) => {
    const { dados, paciente } = await criarPaciente(contextoProfissional.api);

    expect(Object.keys(paciente).sort()).toEqual(
      [
        'birth_date',
        'contact',
        'created_at',
        'created_by_professional_id',
        'full_name',
        'id',
        'internal_identifier',
        'telegram_link_status',
      ].sort(),
    );
    expect(paciente).toMatchObject({
      full_name: dados.full_name,
      internal_identifier: dados.internal_identifier,
      telegram_link_status: 'not_linked',
      contact: null,
      created_by_professional_id: contextoProfissional.profissional.id,
    });
    expect(paciente.created_at).toMatch(/^\d{4}-\d{2}-\d{2}T/);
  });

  test('CT-API-D11 · o histórico aceita day, week e month e recusa período inválido', async ({
    contextoProfissional,
  }) => {
    const { paciente } = await criarPaciente(contextoProfissional.api);

    for (const period of ['day', 'week', 'month']) {
      const resposta = await contextoProfissional.api.get(`/api/v1/patients/${paciente.id}/history`, {
        params: { period },
      });
      expect(resposta.status(), `period=${period}`).toBe(200);
      // Paciente ainda não vinculado ao Telegram: histórico vazio, nunca erro.
      expect(await resposta.json()).toEqual([]);
    }

    const invalido = await contextoProfissional.api.get(`/api/v1/patients/${paciente.id}/history`, {
      params: { period: 'decada' },
    });
    expect(invalido.status()).toBe(422);
  });

  test('CT-API-D12 · a especificação OpenAPI é publicada em YAML e em JSON', async ({ api }) => {
    const yaml = await api.get('/openapi.yaml');
    expect(yaml.status()).toBe(200);
    expect(yaml.headers()['content-type']).toContain('application/yaml');
    const texto = await yaml.text();
    expect(texto).toContain('/api/v1/medications');
    expect(texto).toContain('Hora do Remédio API');

    const json = await api.get('/openapi.json');
    expect(json.status()).toBe(200);
    const especificacao = await json.json();
    expect(especificacao.info.title).toBe('Hora do Remédio API');
    expect(Object.keys(especificacao.paths)).toContain('/api/v1/patients');
  });
});
