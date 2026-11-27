/**
 * VADER — pilar A (Authorization): quem não está autenticado não entra, quem está
 * autenticado só alcança o que é seu, e cada papel só faz o que o RBAC permite.
 *
 * Vale lembrar a separação deliberada da aplicação: a autenticação do paciente/bot é um
 * JWT no cabeçalho Authorization; a do portal de profissionais é um cookie httpOnly de
 * sessão. São dois públicos e dois segredos diferentes (RN19) — um não vale pelo outro.
 *
 * Casos de teste: CT-API-A01 a CT-API-A13.
 */

const { test, expect } = require('../../fixtures');
const config = require('../../support/config');
const { novoMedicamento, novoPaciente } = require('../../support/dados');
const {
  cabecalhoBearer,
  criarPaciente,
  criarProfissionalAutenticado,
  obterTokenPaciente,
} = require('../../support/portal');

test.describe('VADER · Authorization — app do paciente (JWT)', () => {
  test('CT-API-A01 · requisição sem token é rejeitada com 401', async ({ api }) => {
    const resposta = await api.get('/api/v1/medications');

    expect(resposta.status()).toBe(401);
    expect((await resposta.json()).detail).toBe('Credenciais ausentes, inválidas ou expiradas');
  });

  test('CT-API-A02 · token malformado ou adulterado é rejeitado com 401', async ({ api }) => {
    for (const token of ['token-invalido', 'a.b.c', 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI5OTkifQ.assinatura-falsa']) {
      const resposta = await api.get('/api/v1/medications', { headers: cabecalhoBearer(token) });

      expect(resposta.status(), `token "${token}" deveria ser recusado`).toBe(401);
    }
  });

  test('CT-API-A03 · um paciente não alcança o medicamento de outro (RN09)', async ({
    contextoPaciente,
    playwright,
  }) => {
    // Dado um medicamento do paciente A
    const criacao = await contextoPaciente.api.post('/api/v1/medications', { data: novoMedicamento() });
    const medicamentoDoOutro = await criacao.json();

    // E um paciente B autenticado com o próprio token
    const semAuth = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    const token = await obterTokenPaciente(semAuth, 955500001);
    await semAuth.dispose();
    const apiPacienteB = await playwright.request.newContext({
      baseURL: config.apiBaseURL,
      extraHTTPHeaders: cabecalhoBearer(token),
    });

    // Quando o paciente B tenta ler e alterar o medicamento do paciente A
    const leitura = await apiPacienteB.get(`/api/v1/medications/${medicamentoDoOutro.id}`);
    const alteracao = await apiPacienteB.patch(`/api/v1/medications/${medicamentoDoOutro.id}`, {
      data: { dosage: '999mg' },
    });

    // Então o recurso simplesmente não existe para ele — nem confirma, nem vaza dado
    expect(leitura.status()).toBe(404);
    expect(alteracao.status()).toBe(404);
    expect((await leitura.json()).detail).toBe('Medicamento não encontrado');

    await apiPacienteB.dispose();
  });
});

test.describe('VADER · Authorization — portal do profissional (cookie de sessão)', () => {
  test('CT-API-A04 · consulta de perfil sem sessão é rejeitada com 401', async ({ api }) => {
    const resposta = await api.get('/api/v1/professionals/me');

    expect(resposta.status()).toBe(401);
    expect((await resposta.json()).detail).toBe('Sessão inválida, expirada ou ausente');
  });

  test('CT-API-A05 · endpoints de paciente exigem sessão (401 sem cookie)', async ({ api }) => {
    const listagem = await api.get('/api/v1/patients');
    const cadastro = await api.post('/api/v1/patients', { data: novoPaciente() });
    const painel = await api.get('/api/v1/dashboard');

    expect([listagem.status(), cadastro.status(), painel.status()]).toEqual([401, 401, 401]);
  });

  test('CT-API-A06 · cookie de sessão inválido não autentica (401)', async ({ playwright }) => {
    const contexto = await playwright.request.newContext({
      baseURL: config.apiBaseURL,
      extraHTTPHeaders: { Cookie: 'hdr_professional_session=sessao-que-nunca-existiu' },
    });

    const resposta = await contexto.get('/api/v1/professionals/me');
    expect(resposta.status()).toBe(401);

    await contexto.dispose();
  });

  test('CT-API-A07 · token JWT do paciente não vale no portal (401)', async ({ contextoPaciente, api }) => {
    // Dado o token do app do paciente, válido no próprio contexto
    const proprioRecurso = await contextoPaciente.api.get('/api/v1/medications');
    expect(proprioRecurso.status()).toBe(200);

    // Quando uso esse mesmo token em um endpoint do portal
    const resposta = await api.get('/api/v1/professionals/me', {
      headers: cabecalhoBearer(contextoPaciente.token),
    });

    // Então não autentica: as duas autenticações são independentes (RN19)
    expect(resposta.status()).toBe(401);
  });

  test('CT-API-A08 · papel médico não acessa recursos de administrador (403)', async ({
    contextoProfissional,
  }) => {
    const listagem = await contextoProfissional.api.get('/api/v1/professionals');
    const auditoria = await contextoProfissional.api.get('/api/v1/audit-logs');

    expect(listagem.status()).toBe(403);
    expect(auditoria.status()).toBe(403);
    expect((await listagem.json()).detail).toBe('Seu papel não tem permissão para este recurso');
  });

  test('CT-API-A09 · administrador não cadastra paciente — é papel de profissional clínico (403)', async ({
    contextoAdministrador,
  }) => {
    const resposta = await contextoAdministrador.api.post('/api/v1/patients', { data: novoPaciente() });

    expect(resposta.status()).toBe(403);
  });

  test('CT-API-A10 · administrador lista profissionais e enxerga a trilha de auditoria (200)', async ({
    contextoAdministrador,
  }) => {
    const listagem = await contextoAdministrador.api.get('/api/v1/professionals');
    const auditoria = await contextoAdministrador.api.get('/api/v1/audit-logs');

    expect(listagem.status()).toBe(200);
    expect(auditoria.status()).toBe(200);
    expect(Array.isArray(await listagem.json())).toBe(true);
  });

  test('CT-API-A11 · profissional não alcança paciente de outro profissional (RN22)', async ({
    contextoProfissional,
    playwright,
  }) => {
    // Dado um paciente cadastrado pelo profissional A
    const { paciente } = await criarPaciente(contextoProfissional.api);

    // E um profissional B autenticado
    const apiProfissionalB = await playwright.request.newContext({ baseURL: config.apiBaseURL });
    await criarProfissionalAutenticado(apiProfissionalB, { role: 'enfermeiro', profession: 'Enfermeiro' });

    // Quando o profissional B tenta consultar esse paciente e o histórico dele
    const consulta = await apiProfissionalB.get(`/api/v1/patients/${paciente.id}`);
    const historico = await apiProfissionalB.get(`/api/v1/patients/${paciente.id}/history`);
    const listagem = await apiProfissionalB.get('/api/v1/patients');

    // Então não encontra o paciente e a própria lista dele vem sem esse registro
    expect(consulta.status()).toBe(404);
    expect(historico.status()).toBe(404);
    expect((await consulta.json()).detail).toBe('Paciente não encontrado ou sem vínculo autorizado');
    expect((await listagem.json()).map((item) => item.id)).not.toContain(paciente.id);

    await apiProfissionalB.dispose();
  });

  test('CT-API-A13 · profissional ainda não verificado já cadastra paciente — risco R1', async ({
    contextoProfissional,
  }) => {
    // A tela de cadastro avisa que a conta "precisa ser verificada por um administrador
    // antes de ter acesso clínico pleno". Na API, porém, o controle de acesso olha só o
    // PAPEL (require_roles), nunca o verification_status.
    //
    // Este teste registra o comportamento ATUAL, para que uma mudança futura apareça como
    // falha deliberada. O risco está em docs/relatorio-de-sessao.md (R1).
    expect(contextoProfissional.profissional.verification_status).toBe('pending');

    const cadastro = await contextoProfissional.api.post('/api/v1/patients', { data: novoPaciente() });
    const painel = await contextoProfissional.api.get('/api/v1/dashboard');

    expect(cadastro.status()).toBe(201);
    expect(painel.status()).toBe(200);
  });

  test('CT-API-A12 · depois do logout a sessão deixa de valer (401)', async ({ contextoProfissional }) => {
    // Dado uma sessão ativa
    expect((await contextoProfissional.api.get('/api/v1/professionals/me')).status()).toBe(200);

    // Quando encerro a sessão
    const logout = await contextoProfissional.api.post('/api/v1/auth/professional/logout');
    expect(logout.status()).toBe(204);

    // Então o mesmo cookie não autentica mais
    const depois = await contextoProfissional.api.get('/api/v1/professionals/me');
    expect(depois.status()).toBe(401);
  });
});
