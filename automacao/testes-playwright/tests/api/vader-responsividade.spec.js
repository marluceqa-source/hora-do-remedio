/**
 * VADER — pilar R (Responsiveness): a API responde no tempo esperado, se comporta sob
 * requisições simultâneas e degrada com elegância diante de carga ou entrada hostil.
 *
 * Os limites de tempo aqui são deliberadamente folgados: o objetivo é pegar degradação
 * grosseira (segundos), não medir performance — medição de carga é outra ferramenta.
 *
 * Casos de teste: CT-API-R01 a CT-API-R07.
 */

const { test, expect } = require('../../fixtures');
const { HEURISTICAS_STRING, novoMedicamento } = require('../../support/dados');

/** Mede o tempo de uma chamada, em milissegundos. */
async function medir(acao) {
  const inicio = Date.now();
  const resultado = await acao();
  return { resultado, duracaoMs: Date.now() - inicio };
}

test.describe('VADER · Responsiveness — tempo de resposta e concorrência', () => {
  test('CT-API-R01 · health check responde rápido e com o estado do serviço', async ({ api }) => {
    await api.get('/health'); // aquecimento: a primeira chamada paga import e conexão

    const { resultado, duracaoMs } = await medir(() => api.get('/health'));

    expect(resultado.status()).toBe(200);
    expect(await resultado.json()).toMatchObject({ status: 'ok' });
    expect(duracaoMs, `health respondeu em ${duracaoMs}ms`).toBeLessThan(1_500);
  });

  test('CT-API-R02 · listagem com 20 medicamentos responde em tempo aceitável', async ({
    contextoPaciente,
  }) => {
    // Dado 20 medicamentos cadastrados
    const cadastros = Array.from({ length: 20 }, () =>
      contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() }),
    );
    const respostas = await Promise.all(cadastros);
    expect(respostas.every((resposta) => resposta.status() === 201)).toBe(true);

    // Quando consulto a listagem
    const { resultado, duracaoMs } = await medir(() => contextoPaciente.api.get('/api/v1/medications'));

    // Então os 20 vêm e o tempo segue aceitável
    expect(resultado.status()).toBe(200);
    expect(await resultado.json()).toHaveLength(20);
    expect(duracaoMs, `listagem respondeu em ${duracaoMs}ms`).toBeLessThan(3_000);
  });

  test('CT-API-R03 · 10 emissões de token simultâneas respondem todas com tokens distintos', async ({
    api,
  }) => {
    const chamadas = Array.from({ length: 10 }, (_, indice) =>
      api.post('/api/v1/auth/token', { data: { telegram_user_id: 930000000 + indice } }),
    );

    const respostas = await Promise.all(chamadas);

    expect(respostas.map((resposta) => resposta.status())).toEqual(Array(10).fill(200));
    const tokens = await Promise.all(respostas.map(async (resposta) => (await resposta.json()).access_token));
    expect(new Set(tokens).size).toBe(10);
  });

  test('CT-API-R04 · cadastros simultâneos do mesmo usuário não perdem registro', async ({
    contextoPaciente,
  }) => {
    // Dez cadastros disparados ao mesmo tempo pelo mesmo usuário
    const respostas = await Promise.all(
      Array.from({ length: 10 }, () =>
        contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() }),
      ),
    );

    expect(respostas.map((resposta) => resposta.status())).toEqual(Array(10).fill(201));

    // Todos os ids são distintos e a listagem reflete exatamente dez registros
    const ids = await Promise.all(respostas.map(async (resposta) => (await resposta.json()).id));
    expect(new Set(ids).size).toBe(10);

    const lista = await contextoPaciente.api.get('/api/v1/medications');
    expect(await lista.json()).toHaveLength(10);
  });

  test('CT-API-R05 · carga máxima permitida é aceita sem degradar a resposta', async ({
    contextoPaciente,
  }) => {
    // Dado o maior payload que o contrato permite: nome e orientações no limite e 24 horários
    const horarios = Array.from({ length: 24 }, (_, hora) => ({
      recurrence_type: 'daily',
      schedule_time: `${String(hora).padStart(2, '0')}:00`,
    }));

    const { resultado, duracaoMs } = await medir(() =>
      contextoPaciente.api.post('/api/v1/medications', {
        data: novoMedicamento({
          name: HEURISTICAS_STRING.textoLongo(200),
          instructions: HEURISTICAS_STRING.textoLongo(500),
          schedules: horarios,
        }),
      }),
    );

    expect(resultado.status()).toBe(201);
    expect((await resultado.json()).schedules).toHaveLength(24);
    expect(duracaoMs, `cadastro respondeu em ${duracaoMs}ms`).toBeLessThan(5_000);
  });

  test('CT-API-R06 · corpo JSON malformado devolve 422, nunca 500', async ({ contextoPaciente }) => {
    const resposta = await contextoPaciente.api.post('/api/v1/medications', {
      headers: { 'Content-Type': 'application/json' },
      data: '{"name": "Sem fechar o objeto"',
    });

    expect(resposta.status()).toBe(422);
    expect((await resposta.json()).code).toBe('validation_error');

    // E a API continua atendendo normalmente depois disso
    expect((await contextoPaciente.api.get('/api/v1/medications')).status()).toBe(200);
  });

  test('CT-API-R07 · a especificação OpenAPI é servida em tempo aceitável', async ({ api }) => {
    await api.get('/openapi.json'); // aquecimento: o schema é montado na primeira chamada

    const { resultado, duracaoMs } = await medir(() => api.get('/openapi.json'));

    expect(resultado.status()).toBe(200);
    expect(duracaoMs, `openapi.json respondeu em ${duracaoMs}ms`).toBeLessThan(3_000);
  });

  /**
   * Limitação de requisições (slowapi) — fica fora da execução padrão de propósito.
   *
   * A automação sobe a API com RATE_LIMIT_PER_MINUTE alto justamente para que o limite
   * não gere 429 em testes que são de outra coisa. Para exercitar o limite, suba a API
   * com um valor baixo e rode só este teste:
   *
   *   # terminal 1 (na pasta da aplicação)
   *   DATABASE_URL="sqlite:///./database/playwright_test.db" RATE_LIMIT_PER_MINUTE=5 \
   *     .venv/bin/python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
   *
   *   # terminal 2 (nesta pasta)
   *   START_SERVERS=0 RODAR_TESTE_RATE_LIMIT=1 LIMITE_POR_MINUTO=5 \
   *     npx playwright test --project=api -g "CT-API-R08"
   */
  test('CT-API-R08 · requisições acima do limite por minuto recebem 429', async ({ api }) => {
    test.skip(
      process.env.RODAR_TESTE_RATE_LIMIT !== '1',
      'Requer a API com RATE_LIMIT_PER_MINUTE baixo — veja o comentário acima do teste.',
    );

    const limite = Number(process.env.LIMITE_POR_MINUTO ?? 5);

    const respostas = [];
    for (let chamada = 0; chamada < limite + 2; chamada += 1) {
      respostas.push(await api.get('/health'));
    }

    const codigos = respostas.map((resposta) => resposta.status());
    expect(codigos.slice(0, limite)).toEqual(Array(limite).fill(200));
    expect(codigos).toContain(429);
  });
});
