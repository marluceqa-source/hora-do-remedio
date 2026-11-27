/**
 * Fábricas de massa de teste e cargas derivadas de heurísticas.
 *
 * Toda massa é gerada única (sufixo com timestamp + contador) para que os testes rodem em
 * paralelo e repetidas vezes sem colidir em e-mail de profissional ou identificador
 * interno de paciente — ambos são campos únicos na aplicação.
 *
 * Os dados são fictícios e não representam orientação médica real.
 */

const crypto = require('node:crypto');

let contador = 0;

/** Sufixo único e legível, para dar rastreabilidade ao dado criado pelo teste. */
function sufixoUnico() {
  contador += 1;
  return `${Date.now().toString(36)}${contador}${crypto.randomBytes(2).toString('hex')}`;
}

/**
 * Domínio do e-mail: a API valida e-mail com a biblioteca email-validator, que REJEITA
 * TLDs reservados como `.test` e `.invalid` (erro 422). `example.com` é aceito.
 */
const DOMINIO_EMAIL = 'example.com';

const SENHA_PADRAO = 'SenhaForte123';

function dataISO(deslocamentoDias = 0) {
  const data = new Date();
  data.setDate(data.getDate() + deslocamentoDias);
  return data.toISOString().slice(0, 10);
}

/** Profissional de saúde válido para o portal (RF01). */
function novoProfissional(sobrescritas = {}) {
  const sufixo = sufixoUnico();
  return {
    full_name: `Dra. Automação ${sufixo}`,
    email: `qa.automacao.${sufixo}@${DOMINIO_EMAIL}`,
    password: SENHA_PADRAO,
    role: 'medico',
    profession: 'Médica',
    council_number: '123456',
    council_state: 'MG',
    ...sobrescritas,
  };
}

/** Paciente válido (RF03) — identificador interno nunca é CPF ou documento real. */
function novoPaciente(sobrescritas = {}) {
  const sufixo = sufixoUnico();
  return {
    full_name: `Paciente Fictício ${sufixo}`,
    internal_identifier: `PAC-${sufixo.toUpperCase()}`,
    birth_date: '1948-03-21',
    ...sobrescritas,
  };
}

/** Medicamento válido do app do paciente (RF02/RN02: ao menos um horário). */
function novoMedicamento(sobrescritas = {}) {
  const sufixo = sufixoUnico();
  return {
    name: `Losartana Fictícia ${sufixo}`,
    dosage: '50mg',
    quantity: '1 comprimido',
    instructions: 'Dado sintético de automação — sem valor clínico.',
    start_date: dataISO(0),
    schedules: [{ recurrence_type: 'daily', schedule_time: '08:00' }],
    ...sobrescritas,
  };
}

/** Esquema terapêutico criado pelo profissional para um paciente (RF05). */
function novoTratamento(sobrescritas = {}) {
  const sufixo = sufixoUnico();
  return {
    medication_name: `Enalapril Fictício ${sufixo}`,
    dosage: '10',
    dosage_unit: 'mg',
    quantity_per_administration: '1 comprimido',
    instructions: 'Dado sintético de automação — sem valor clínico.',
    start_date: dataISO(0),
    schedules: [{ recurrence_type: 'daily', schedule_time: '20:00' }],
    ...sobrescritas,
  };
}

/** telegram_user_id único para o token do app do paciente. */
function novoTelegramUserId() {
  contador += 1;
  return Number(`9${String(Date.now()).slice(-8)}${contador}`);
}

/**
 * Cargas de ataque das heurísticas de teste (Test Obsessed / Elisabeth Hendrickson):
 * strings longas, caracteres acentuados, delimitadores, injeção de SQL e espaços.
 */
const HEURISTICAS_STRING = {
  textoLongo: (tamanho) => 'A'.repeat(tamanho),
  acentuado: 'Ãçêñtõs àéîôü — Remédio Nº1',
  asiatico: '薬の時間です',
  delimitadores: `Nome com "aspas", 'apóstrofo', <tag> & ponto-e-vírgula;`,
  injecaoSql: "Losartana'); DROP TABLE medications; --",
  injecaoHtml: '<script>window.__xss = true</script>',
  somenteEspacos: '   ',
  vazio: '',
  espacosNasBordas: '  Losartana  ',
};

module.exports = {
  DOMINIO_EMAIL,
  SENHA_PADRAO,
  HEURISTICAS_STRING,
  dataISO,
  novoMedicamento,
  novoPaciente,
  novoProfissional,
  novoTelegramUserId,
  novoTratamento,
  sufixoUnico,
};
