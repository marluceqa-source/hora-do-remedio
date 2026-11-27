/**
 * Gera `relatorio.html`: o relatório de testes em uma página só, para leitura humana.
 *
 * Nada aqui é escrito à mão. O conteúdo vem de três fontes reais:
 *   resultados/*.json        → resultado de cada execução (reporter json do Playwright)
 *   evidencias/_itens/*.json → manifesto de vídeo e screenshots de cada item
 *   docs/relatorio-de-sessao.md → notas, riscos, defeitos e perguntas da sessão
 *
 * Uso:
 *   node scripts/gerar-relatorio.js              → imagens por link relativo (arquivo leve)
 *   node scripts/gerar-relatorio.js --embutir    → imagens embutidas (arquivo único, pesado)
 *
 * O relatório do Playwright (`npm run report`) continua existindo e é complementar: aquele
 * é a ferramenta de quem investiga uma falha; este é o documento de quem lê o trabalho.
 */

const fs = require('node:fs');
const path = require('node:path');

const config = require('../support/config');

const RAIZ = config.raizProjeto;
const PASTA_RESULTADOS = path.join(RAIZ, 'resultados');
const PASTA_EVIDENCIAS = path.join(RAIZ, 'evidencias');
const RELATORIO_SESSAO = path.join(RAIZ, 'docs/relatorio-de-sessao.md');

const EMBUTIR = process.argv.includes('--embutir');
const SAIDA = path.join(RAIZ, EMBUTIR ? 'relatorio-completo.html' : 'relatorio.html');

// ---------------------------------------------------------------- utilidades

const escapar = (texto) =>
  String(texto).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Markdown inline mínimo: **negrito**, `código` e links. */
function inline(texto) {
  return escapar(texto)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>');
}

const duracaoLegivel = (ms) => (ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`);

// ------------------------------------------------- leitura dos resultados JSON

/** Achata a árvore de suítes do reporter json em uma lista de casos. */
function extrairCasos(suites, acumulado = []) {
  for (const suite of suites ?? []) {
    for (const spec of suite.specs ?? []) {
      for (const teste of spec.tests ?? []) {
        const resultado = teste.results?.[teste.results.length - 1] ?? {};
        acumulado.push({
          arquivo: spec.file,
          titulo: spec.title,
          projeto: teste.projectName,
          situacao: resultado.status ?? 'unknown',
          duracao: resultado.duration ?? 0,
        });
      }
    }
    extrairCasos(suite.suites, acumulado);
  }
  return acumulado;
}

function lerExecucao(nome) {
  const arquivo = path.join(PASTA_RESULTADOS, `${nome}.json`);
  if (!fs.existsSync(arquivo)) return null;

  const dados = JSON.parse(fs.readFileSync(arquivo, 'utf-8'));
  return {
    nome,
    inicio: dados.stats?.startTime ? new Date(dados.stats.startTime) : null,
    duracao: dados.stats?.duration ?? 0,
    aprovados: dados.stats?.expected ?? 0,
    reprovados: dados.stats?.unexpected ?? 0,
    instaveis: dados.stats?.flaky ?? 0,
    ignorados: dados.stats?.skipped ?? 0,
    casos: extrairCasos(dados.suites),
  };
}

/**
 * Resultado da suíte do bot do Telegram (pytest), em JUnit XML.
 *
 * O bot é Python e roda em polling: não há como exercitá-lo por Playwright, então aquela
 * suíte vive em `../testes-bot-telegram` e deposita o XML aqui. Sem dependência de
 * parser: o formato do JUnit é raso e os atributos que interessam são poucos.
 */
function lerSuiteDoBot() {
  const arquivo = path.join(PASTA_RESULTADOS, 'bot.xml');
  if (!fs.existsSync(arquivo)) return null;

  const xml = fs.readFileSync(arquivo, 'utf-8');
  const cabecalho = xml.match(/<testsuite\b[^>]*>/)?.[0] ?? '';
  const atributo = (nome) => Number((cabecalho.match(new RegExp(`${nome}="([^"]*)"`)) ?? ['', '0'])[1]);

  const casos = [...xml.matchAll(/<testcase\b([^>]*?)(\/>|>([\s\S]*?)<\/testcase>)/g)].map((achado) => {
    const atributos = achado[1];
    const corpo = achado[3] ?? '';
    const pegar = (nome) => (atributos.match(new RegExp(`${nome}="([^"]*)"`)) ?? ['', ''])[1];

    let situacao = 'passed';
    if (/<failure\b/.test(corpo)) situacao = 'failed';
    else if (/<error\b/.test(corpo)) situacao = 'failed';
    else if (/<skipped\b/.test(corpo)) situacao = 'skipped';

    return {
      arquivo: `${pegar('classname').replace(/^testes\./, '')}.py`,
      titulo: pegar('name'),
      projeto: 'bot (pytest)',
      situacao,
      duracao: Number(pegar('time') || 0) * 1000,
    };
  });

  const total = atributo('tests');
  const reprovados = atributo('failures') + atributo('errors');
  const ignorados = atributo('skipped');

  return {
    nome: 'bot',
    duracao: atributo('time') * 1000,
    aprovados: total - reprovados - ignorados,
    reprovados,
    ignorados,
    casos,
  };
}

// --------------------------------------------------- leitura dos manifestos

function lerEvidencias() {
  const pasta = path.join(PASTA_EVIDENCIAS, '_itens');
  if (!fs.existsSync(pasta)) return new Map();

  const itens = fs
    .readdirSync(pasta)
    .filter((arquivo) => arquivo.endsWith('.json'))
    .map((arquivo) => JSON.parse(fs.readFileSync(path.join(pasta, arquivo), 'utf-8')));

  return new Map(itens.map((item) => [item.id, item]));
}

// ------------------------------------------- leitura do relatório de sessão

function lerRelatorioSessao() {
  if (!fs.existsSync(RELATORIO_SESSAO)) return { notas: [], riscos: [], perguntas: [], defeitos: [] };

  const linhas = fs.readFileSync(RELATORIO_SESSAO, 'utf-8').split(/\r?\n/);

  // Junta cada item de lista com suas linhas de continuação (indentadas).
  const itens = [];
  let atual = null;
  let secao = '';

  for (const linha of linhas) {
    if (linha.startsWith('## ')) {
      secao = linha.slice(3).trim();
      atual = null;
      continue;
    }
    if (/^[-\d]/.test(linha)) {
      atual = { secao, texto: linha.trim() };
      itens.push(atual);
      continue;
    }
    if (atual && /^\s+\S/.test(linha)) {
      atual.texto += ` ${linha.trim()}`;
      continue;
    }
    atual = null;
  }

  const notas = [];
  const riscos = [];

  for (const item of itens.filter((registro) => registro.secao === 'Notas')) {
    const encontrado = item.texto.match(/^- \*\*\((I|R)\)\s*((?:I|R)\d+)?\s*—?\s*(.*?)\*\*\s*(.*)$/);
    if (!encontrado) continue;

    const [, tipo, id, titulo, corpo] = encontrado;
    const registro = { tipo, id: id ?? null, titulo: titulo.replace(/\.$/, ''), corpo };
    (tipo === 'R' ? riscos : notas).push(registro);
  }

  const cabecalho = linhas.find((linha) => /^\| \d+ de /.test(linha.trim()));
  const [, data, testador, modulo] = cabecalho
    ? cabecalho.split('|').map((parte) => parte.trim())
    : [null, '—', '—', '—'];

  const charter = itens.length
    ? (linhas.join('\n').match(/\*\*Test Charter:\*\*\s*([\s\S]*?)\n\n/) ?? [, ''])[1].replace(/\s+/g, ' ').trim()
    : '';

  return {
    data,
    testador,
    modulo,
    charter,
    notas,
    riscos,
    perguntas: itens
      .filter((registro) => registro.secao === 'Perguntas')
      .map((registro) => registro.texto.replace(/^\d+\.\s*/, '')),
    defeitos: itens
      .filter((registro) => registro.secao === 'Defeitos')
      .map((registro) => registro.texto.replace(/^\d+\.\s*/, '')),
  };
}

// ------------------------------------------------------------- montagem HTML

function imagem(arquivo) {
  const caminhoRelativo = `evidencias/${arquivo}`;
  if (!EMBUTIR) return caminhoRelativo;

  const completo = path.join(PASTA_EVIDENCIAS, arquivo);
  if (!fs.existsSync(completo)) return caminhoRelativo;
  return `data:image/png;base64,${fs.readFileSync(completo).toString('base64')}`;
}

function blocoEvidencia(item, registro = null) {
  if (!item) {
    // Itens vindos da suíte do bot não têm tela para filmar: a evidência é o teste.
    const casoDoBot = registro?.corpo?.match(/CT-BOT-[A-Z]\d+/)?.[0];
    if (casoDoBot) {
      return `<p class="vazio">O bot do Telegram não tem tela para gravar: a evidência deste item é o
        teste automatizado <code>${casoDoBot}</code>, em
        <a href="../testes-bot-telegram/docs/casos-de-teste-bot-heuristicas.md">casos de teste do bot</a>.</p>`;
    }
    return '<p class="vazio">Sem evidência gravada para este item.</p>';
  }

  const video = item.video
    ? `<video controls preload="metadata" src="evidencias/${item.video}"></video>
       <p class="legenda-video">Vídeo: <a href="evidencias/${item.video}">${item.video}</a></p>`
    : '';

  const telas = item.imagens
    .map(
      (captura, indice) => `
      <figure>
        <a href="evidencias/${captura.arquivo}">
          <img loading="lazy" src="${imagem(captura.arquivo)}" alt="${escapar(captura.rotulo)}">
        </a>
        <figcaption>${indice + 1}. ${escapar(captura.rotulo)}</figcaption>
      </figure>`,
    )
    .join('');

  return `<div class="evidencia">${video}<div class="telas">${telas}</div></div>`;
}

function tabelaCasos(casos) {
  const porArquivo = new Map();
  for (const caso of casos) {
    if (!porArquivo.has(caso.arquivo)) porArquivo.set(caso.arquivo, []);
    porArquivo.get(caso.arquivo).push(caso);
  }

  return [...porArquivo.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([arquivo, lista]) => {
      const linhas = lista
        .map(
          (caso) => `
        <tr>
          <td>${escapar(caso.titulo)}</td>
          <td><span class="situacao ${caso.situacao}">${rotuloSituacao(caso.situacao)}</span></td>
          <td class="numero">${duracaoLegivel(caso.duracao)}</td>
        </tr>`,
        )
        .join('');

      const aprovados = lista.filter((caso) => caso.situacao === 'passed').length;
      return `
      <details open>
        <summary><code>${escapar(arquivo)}</code> <span class="contagem">${aprovados}/${lista.length}</span></summary>
        <table>
          <thead><tr><th>Caso de teste</th><th>Situação</th><th class="numero">Duração</th></tr></thead>
          <tbody>${linhas}</tbody>
        </table>
      </details>`;
    })
    .join('');
}

const rotuloSituacao = (situacao) =>
  ({ passed: 'Aprovado', failed: 'Reprovado', skipped: 'Ignorado', timedOut: 'Estourou o tempo' })[situacao] ??
  situacao;

function secaoItens(titulo, registros, evidencias, descricao) {
  const blocos = registros
    .map((registro) => {
      const id = registro.id ?? '';
      const evidencia = evidencias.get(id);
      return `
      <article class="item" id="${id.toLowerCase()}">
        <h3><span class="chip ${registro.tipo === 'R' ? 'risco' : 'nota'}">${id || registro.tipo}</span> ${escapar(registro.titulo)}</h3>
        <p>${inline(registro.corpo)}</p>
        ${blocoEvidencia(evidencia, registro)}
      </article>`;
    })
    .join('');

  return `<section><h2>${titulo}</h2><p class="descricao">${descricao}</p>${blocos}</section>`;
}

function montarHtml({ suite, bot, evidenciasExecucao, evidencias, sessao }) {
  const suites = [suite, bot].filter(Boolean);
  const somar = (campo) => suites.reduce((acumulado, atual) => acumulado + (atual[campo] ?? 0), 0);
  const todosOsCasos = suites.flatMap((execucao) => execucao.casos);
  const total = somar('aprovados') + somar('reprovados') + somar('ignorados');
  const geradoEm = new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' });

  const cartoes = [
    ['Casos executados', total, ''],
    ['Aprovados', somar('aprovados'), 'ok'],
    ['Reprovados', somar('reprovados'), somar('reprovados') ? 'erro' : ''],
    ['Ignorados', somar('ignorados'), 'neutro'],
    ['Duração', duracaoLegivel(somar('duracao')), ''],
  ]
    .map(
      ([rotulo, valor, classe]) =>
        `<div class="cartao ${classe}"><span class="valor">${valor}</span><span class="rotulo">${rotulo}</span></div>`,
    )
    .join('');

  const porProjeto = new Map();
  for (const caso of todosOsCasos) {
    const atual = porProjeto.get(caso.projeto) ?? { total: 0, aprovados: 0, ignorados: 0 };
    atual.total += 1;
    if (caso.situacao === 'passed') atual.aprovados += 1;
    if (caso.situacao === 'skipped') atual.ignorados += 1;
    porProjeto.set(caso.projeto, atual);
  }

  const linhasProjeto = [...porProjeto.entries()]
    .map(
      ([projeto, dados]) => `
      <tr>
        <td><code>${escapar(projeto)}</code></td>
        <td class="numero">${dados.total}</td>
        <td class="numero">${dados.aprovados}</td>
        <td class="numero">${dados.ignorados}</td>
      </tr>`,
    )
    .join('');

  return `<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Relatório de Testes — Hora do Remédio</title>
<style>
  :root {
    color-scheme: light dark;
    --fundo: #ffffff; --fundo-2: #f6f8fb; --borda: #dde3ec; --texto: #15202b;
    --suave: #5b6b80; --destaque: #0b5fa5; --ok: #1a7f52; --erro: #b3261e; --neutro: #8a6d1f;
  }
  @media (prefers-color-scheme: dark) {
    :root { --fundo: #0f1419; --fundo-2: #161c24; --borda: #26303d; --texto: #e6edf5;
            --suave: #93a3b8; --destaque: #4ea3f0; --ok: #4ac98a; --erro: #ff6b61; --neutro: #e0b64a; }
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--fundo); color: var(--texto); font: 16px/1.65 -apple-system,
         "Segoe UI", system-ui, sans-serif; }
  .folha { max-width: 1040px; margin: 0 auto; padding: 48px 24px 96px; }
  header.capa { border-bottom: 2px solid var(--borda); padding-bottom: 28px; margin-bottom: 36px; }
  h1 { font-size: 30px; margin: 0 0 6px; letter-spacing: -0.01em; }
  .subtitulo { color: var(--suave); margin: 0 0 20px; }
  .ficha { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 14px; }
  .ficha div { background: var(--fundo-2); border: 1px solid var(--borda); border-radius: 10px; padding: 12px 14px; }
  .ficha dt { font-size: 12px; text-transform: uppercase; letter-spacing: .05em; color: var(--suave); margin: 0 0 2px; }
  .ficha dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }
  .ficha dd code { font-size: 12.5px; }
  h2 { font-size: 21px; margin: 44px 0 6px; padding-top: 12px; border-top: 1px solid var(--borda); }
  h3 { font-size: 17px; margin: 28px 0 8px; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .descricao { color: var(--suave); margin: 0 0 20px; }
  .cartoes { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 18px 0 8px; }
  .cartao { background: var(--fundo-2); border: 1px solid var(--borda); border-radius: 12px;
            padding: 16px; display: flex; flex-direction: column; gap: 2px; }
  .cartao .valor { font-size: 26px; font-weight: 700; }
  .cartao .rotulo { font-size: 13px; color: var(--suave); }
  .cartao.ok .valor { color: var(--ok); }
  .cartao.erro .valor { color: var(--erro); }
  .cartao.neutro .valor { color: var(--neutro); }
  table { width: 100%; border-collapse: collapse; margin: 12px 0 4px; font-size: 14.5px; }
  th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--borda); vertical-align: top; }
  th { font-size: 12px; text-transform: uppercase; letter-spacing: .04em; color: var(--suave); }
  td.numero, th.numero { text-align: right; white-space: nowrap; }
  code { background: var(--fundo-2); border: 1px solid var(--borda); border-radius: 5px;
         padding: 1px 5px; font: 13px ui-monospace, Menlo, monospace; }
  details { border: 1px solid var(--borda); border-radius: 10px; padding: 10px 14px; margin-bottom: 12px;
            background: var(--fundo-2); }
  summary { cursor: pointer; font-weight: 600; }
  .contagem { float: right; color: var(--suave); font-weight: 400; font-size: 14px; }
  .situacao { font-size: 12.5px; font-weight: 600; padding: 2px 8px; border-radius: 999px;
              border: 1px solid currentColor; white-space: nowrap; }
  .situacao.passed { color: var(--ok); }
  .situacao.failed, .situacao.timedOut { color: var(--erro); }
  .situacao.skipped { color: var(--neutro); }
  .chip { font-size: 13px; font-weight: 700; padding: 2px 10px; border-radius: 999px; color: #fff; }
  .chip.risco { background: var(--erro); }
  .chip.nota { background: var(--destaque); }
  .item { border: 1px solid var(--borda); border-radius: 14px; padding: 4px 20px 20px; margin-bottom: 22px; }
  .evidencia { margin-top: 14px; }
  video { width: 100%; max-width: 760px; aspect-ratio: 16 / 9; border: 1px solid var(--borda);
          border-radius: 10px; background: #000; display: block; }
  .legenda-video { font-size: 13px; color: var(--suave); margin: 6px 0 14px; }
  .telas { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 14px; }
  figure { margin: 0; }
  figure img { width: 100%; border: 1px solid var(--borda); border-radius: 8px; display: block; background: var(--fundo-2); }
  figcaption { font-size: 12.5px; color: var(--suave); margin-top: 6px; }
  .vazio { color: var(--suave); font-style: italic; }
  ol.perguntas li, ol.defeitos li { margin-bottom: 10px; }
  footer { margin-top: 56px; padding-top: 18px; border-top: 1px solid var(--borda);
           color: var(--suave); font-size: 14px; }
  a { color: var(--destaque); }
  @media print {
    body { background: #fff; }
    .folha { max-width: none; padding: 0; }
    details { break-inside: avoid; }
    .item { break-inside: avoid; border-color: #bbb; }
    video { display: none; }
  }
</style>
</head>
<body>
<div class="folha">

<header class="capa">
  <h1>Relatório de Testes — Hora do Remédio</h1>
  <p class="subtitulo">Automação de WEB e API com Playwright · gerado em ${geradoEm}</p>
  <dl class="ficha">
    <div><dt>Testador</dt><dd>${escapar(sessao.testador)}</dd></div>
    <div><dt>Data da sessão</dt><dd>${escapar(sessao.data)}</dd></div>
    <div><dt>Módulo</dt><dd>${escapar(sessao.modulo)}</dd></div>
    <div><dt>Portal web</dt><dd><code>${escapar(config.webBaseURL)}</code></dd></div>
    <div><dt>API REST</dt><dd><code>${escapar(config.apiBaseURL)}</code></dd></div>
  </dl>
</header>

<section>
  <h2>1. Objetivo da sessão</h2>
  <p>${inline(sessao.charter)}</p>
  <p class="descricao">
    Os casos de API foram desenhados com a heurística <strong>VADER</strong> (Verbs, Authorization,
    Data, Errors, Responsiveness); os cenários de interface foram escritos em <strong>Gherkin</strong>;
    e as cargas de entrada vieram das <strong>heurísticas de ataque a tipos de dados e strings</strong>.
    O bot do Telegram, que não tem tela nem porta HTTP, foi testado à parte com as
    <strong>heurísticas de Elisabeth Hendrickson</strong> (ataques a tipos de dados, strings, CRUD,
    Siga os Dados, Interrupções e abordagem contrária).
    Detalhamento em <a href="docs/casos-de-teste-api-vader.md">casos de teste de API</a>,
    <a href="docs/casos-de-teste-web-gherkin.md">cenários de web</a>,
    <a href="../testes-bot-telegram/docs/casos-de-teste-bot-heuristicas.md">casos do bot</a> e
    <a href="docs/heuristicas-aplicadas.md">heurísticas aplicadas</a>.
  </p>
</section>

<section>
  <h2>2. Resumo da execução</h2>
  <div class="cartoes">${cartoes}</div>
  <table>
    <thead><tr><th>Projeto</th><th class="numero">Casos</th><th class="numero">Aprovados</th><th class="numero">Ignorados</th></tr></thead>
    <tbody>${linhasProjeto}</tbody>
  </table>
  <p class="descricao">
    O caso ignorado é o de limite de requisições por minuto (CT-API-R08): ele exige a API no ar com
    limite baixo e fica fora da execução padrão de propósito, para não gerar 429 em testes de outro assunto.
    ${
      evidenciasExecucao
        ? `A geração de evidências rodou à parte: ${evidenciasExecucao.aprovados} itens em ${duracaoLegivel(evidenciasExecucao.duracao)}.`
        : ''
    }
  </p>
</section>

<section>
  <h2>3. Casos executados</h2>
  <p class="descricao">
    Agrupados por arquivo de especificação: um arquivo por pilar do VADER, na API; um por fluxo de
    tela, na web; e um por grupo de heurística, no bot do Telegram.
  </p>
  ${tabelaCasos(todosOsCasos)}
</section>

${secaoItens(
  '4. Riscos encontrados',
  sessao.riscos,
  evidencias,
  'Pontos em que o comportamento observado diverge do que o contrato ou a tela prometem. Cada um tem vídeo e telas gravados pela automação.',
)}

<section>
  <h2>5. Defeitos</h2>
  <p class="descricao">Nenhum defeito que impeça o uso foi encontrado. Os itens abaixo são os riscos que mais pedem decisão do time.</p>
  <ol class="defeitos">${sessao.defeitos.map((texto) => `<li>${inline(texto)}</li>`).join('')}</ol>
</section>

${secaoItens(
  '6. Observações da sessão',
  sessao.notas,
  evidencias,
  'Informações que sustentam as decisões de automação e registram o que a aplicação faz bem.',
)}

<section>
  <h2>7. Perguntas em aberto</h2>
  <p class="descricao">Questões para o time — não são observações sobre o comportamento da aplicação, por isso não têm evidência de tela.</p>
  <ol class="perguntas">${sessao.perguntas.map((texto) => `<li>${inline(texto)}</li>`).join('')}</ol>
</section>

<section>
  <h2>8. Como reproduzir</h2>
  <table>
    <thead><tr><th>Passo</th><th>Comando</th></tr></thead>
    <tbody>
      <tr><td>Instalar</td><td><code>npm install &amp;&amp; npx playwright install chromium</code></td></tr>
      <tr><td>Rodar a suíte de web e API</td><td><code>npm test</code></td></tr>
      <tr><td>Rodar a suíte do bot</td><td><code>cd ../testes-bot-telegram &amp;&amp; ../../.venv/bin/python -m pytest</code></td></tr>
      <tr><td>Gravar as evidências</td><td><code>npm run evidencias</code></td></tr>
      <tr><td>Gerar este relatório</td><td><code>npm run relatorio</code></td></tr>
    </tbody>
  </table>
  <p class="descricao">
    A automação sobe a API e o portal sozinha e usa um banco SQLite exclusivo — o banco de
    desenvolvimento da aplicação não é tocado.
  </p>
</section>

<footer>
  Gerado por <code>scripts/gerar-relatorio.js</code> a partir dos resultados em
  <code>resultados/</code>, dos manifestos em <code>evidencias/_itens/</code> e de
  <code>docs/relatorio-de-sessao.md</code>. Para investigar uma falha caso a caso, use o
  relatório do Playwright: <code>npm run report</code>.
  ${EMBUTIR ? 'Imagens embutidas neste arquivo; os vídeos continuam na pasta <code>evidencias/</code>.' : 'Imagens e vídeos são lidos da pasta <code>evidencias/</code> — mantenha o relatório ao lado dela.'}
</footer>

</div>
</body>
</html>`;
}

// ------------------------------------------------------------------- execução

const suite = lerExecucao('suite');
if (!suite) {
  console.error('[relatório] resultados/suite.json não encontrado — rode `npm test` antes.');
  process.exit(1);
}

const html = montarHtml({
  suite,
  bot: lerSuiteDoBot(),
  evidenciasExecucao: lerExecucao('evidencias'),
  evidencias: lerEvidencias(),
  sessao: lerRelatorioSessao(),
});

fs.writeFileSync(SAIDA, html, 'utf-8');
const bot = lerSuiteDoBot();
console.log(
  `[relatório] ${path.relative(RAIZ, SAIDA)} gerado — ${suite.aprovados + (bot?.aprovados ?? 0)} aprovados, ` +
    `${suite.ignorados + (bot?.ignorados ?? 0)} ignorados, ${(fs.statSync(SAIDA).size / 1024).toFixed(0)} KB.`,
);
