/**
 * Monta o índice da pasta `evidencias/` a partir dos manifestos que o projeto de
 * evidências grava em `evidencias/_itens/`.
 *
 * Roda automaticamente no fim de `npm run evidencias`.
 */

const fs = require('node:fs');
const path = require('node:path');

const config = require('../support/config');

const PASTA = path.join(config.raizProjeto, 'evidencias');
const PASTA_ITENS = path.join(PASTA, '_itens');

if (!fs.existsSync(PASTA_ITENS)) {
  console.error('[índice] nenhum manifesto encontrado — rode `npm run evidencias` primeiro.');
  process.exit(1);
}

const itens = fs
  .readdirSync(PASTA_ITENS)
  .filter((arquivo) => arquivo.endsWith('.json'))
  .map((arquivo) => JSON.parse(fs.readFileSync(path.join(PASTA_ITENS, arquivo), 'utf-8')))
  // Notas (I) primeiro, riscos (R) depois, cada grupo em ordem numérica.
  .sort((a, b) => a.id.localeCompare(b.id, 'pt-BR', { numeric: true }));

const linhas = [
  '# Evidências do relatório de sessão',
  '',
  'Vídeos e screenshots gerados por `npm run evidencias` (projeto `evidencias` do',
  'Playwright). Cada item do [relatório de sessão](../docs/relatorio-de-sessao.md) tem um',
  'vídeo e a sequência de telas que sustenta a observação.',
  '',
  'Os testes que geram estes arquivos também **asseguram o comportamento descrito**: se a',
  'aplicação for corrigida, a evidência falha e avisa que o relatório ficou desatualizado.',
  '',
  'A massa muda a cada execução (nomes e e-mails têm sufixo único), mas o caminho',
  'percorrido é sempre o mesmo.',
  '',
  `Gerado em ${new Date().toLocaleString('pt-BR', { timeZone: 'America/Sao_Paulo' })}.`,
  '',
  '| Item | Observação | Vídeo | Telas |',
  '| --- | --- | --- | --- |',
];

for (const item of itens) {
  const video = item.video ? `[🎬](${item.video})` : '—';
  linhas.push(`| [**${item.id}**](#${item.id.toLowerCase()}) | ${item.titulo} | ${video} | ${item.imagens.length} |`);
}

for (const item of itens) {
  linhas.push('', `## ${item.id}`, '', item.titulo, '');
  if (item.situacao !== 'passed') {
    linhas.push(`> Atenção: este item terminou como \`${item.situacao}\` na última geração.`, '');
  }
  if (item.video) linhas.push(`🎬 Vídeo: [\`${item.video}\`](${item.video})`, '');
  item.imagens.forEach((imagem, indice) => {
    linhas.push(`${indice + 1}. [${imagem.rotulo}](${encodeURI(imagem.arquivo)})`);
  });
  linhas.push('', `Gerado por \`${item.arquivo}\`.`);
}

fs.writeFileSync(path.join(PASTA, 'README.md'), `${linhas.join('\n')}\n`, 'utf-8');
console.log(`[índice] evidencias/README.md atualizado com ${itens.length} itens.`);
