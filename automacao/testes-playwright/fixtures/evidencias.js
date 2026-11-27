/**
 * Fixture de evidências.
 *
 * Grava, para cada item do relatório de sessão, um vídeo com nome previsível e uma
 * sequência de screenshots numeradas, tudo na pasta `evidencias/` da raiz deste projeto:
 *
 *   evidencias/R1-01-mensagem-de-cadastro-recebido.png
 *   evidencias/R1-02-...png
 *   evidencias/R1-video.webm
 *
 * O identificador (I1, R2, ...) sai do começo do título do teste, então o nome do arquivo
 * sempre aponta para o item correspondente no relatório. Cada arquivo também é anexado ao
 * relatório HTML do Playwright (`npm run report`).
 */

const fs = require('node:fs');
const path = require('node:path');

const base = require('@playwright/test');

const config = require('../support/config');

const PASTA_EVIDENCIAS = path.join(config.raizProjeto, 'evidencias');

function apelido(texto) {
  return texto
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60);
}

/** Página de painel usada para exibir saída real de terminal ou de API em uma imagem. */
function montarPainel(titulo, blocos) {
  const corpo = blocos
    .map(
      (bloco) => `
      <section>
        <h2>${bloco.rotulo}</h2>
        <pre>${String(bloco.conteudo)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')}</pre>
      </section>`,
    )
    .join('');

  return `<!doctype html>
  <html lang="pt-BR"><head><meta charset="utf-8"><title>${titulo}</title>
  <style>
    :root { color-scheme: dark; }
    body { margin: 0; padding: 32px; background: #11151c; color: #e8edf5;
           font: 15px/1.6 -apple-system, "Segoe UI", system-ui, sans-serif; }
    h1 { font-size: 22px; margin: 0 0 4px; }
    p.origem { margin: 0 0 24px; color: #8fa0b8; font-size: 13px; }
    section { margin-bottom: 20px; }
    h2 { font-size: 14px; margin: 0 0 8px; color: #7fd1a8; font-weight: 600; }
    pre { margin: 0; padding: 16px; background: #0a0d12; border: 1px solid #263040;
          border-radius: 8px; white-space: pre-wrap; word-break: break-word;
          font: 13px/1.55 ui-monospace, "SF Mono", Menlo, monospace; color: #dbe4f0; }
  </style></head>
  <body>
    <h1>${titulo}</h1>
    <p class="origem">Saída real capturada pela automação durante a execução — nada aqui foi digitado à mão.</p>
    ${corpo}
  </body></html>`;
}

const test = base.test.extend({
  evidencia: async ({ page }, use, testInfo) => {
    const id = (testInfo.title.match(/^(I\d+|R\d+)/) ?? ['sem-id'])[0];
    fs.mkdirSync(PASTA_EVIDENCIAS, { recursive: true });

    let sequencia = 0;
    const capturas = [];

    const ferramentas = {
      id,
      pasta: PASTA_EVIDENCIAS,

      /** Tira uma screenshot numerada e a anexa ao relatório HTML. */
      async capturar(rotulo, { paginaInteira = false } = {}) {
        sequencia += 1;
        const arquivo = path.join(
          PASTA_EVIDENCIAS,
          `${id}-${String(sequencia).padStart(2, '0')}-${apelido(rotulo)}.png`,
        );
        await page.screenshot({ path: arquivo, fullPage: paginaInteira });
        await testInfo.attach(`${id} · ${rotulo}`, { path: arquivo, contentType: 'image/png' });
        capturas.push({ rotulo, arquivo: path.basename(arquivo) });
        return arquivo;
      },

      /** Exibe saída de terminal/API em um painel na própria página, para virar imagem. */
      async exibirPainel(titulo, blocos) {
        await page.setContent(montarPainel(titulo, blocos), { waitUntil: 'load' });
      },
    };

    await use(ferramentas);

    // O vídeo só fica disponível depois que a página fecha; renomeá-lo aqui garante que
    // o arquivo final tenha o identificador do item, e não um nome aleatório.
    let video_arquivo = null;
    const video = page.video();
    if (video) {
      await page.close();
      const destino = path.join(PASTA_EVIDENCIAS, `${id}-video.webm`);
      await video.saveAs(destino);
      await testInfo.attach(`${id} · vídeo`, { path: destino, contentType: 'video/webm' });
      video_arquivo = path.basename(destino);
    }

    // Manifesto por item (um arquivo por teste, para não haver disputa entre workers).
    // `scripts/indice-evidencias.js` junta tudo e escreve o índice da pasta.
    const pastaManifesto = path.join(PASTA_EVIDENCIAS, '_itens');
    fs.mkdirSync(pastaManifesto, { recursive: true });
    fs.writeFileSync(
      path.join(pastaManifesto, `${id}.json`),
      JSON.stringify(
        {
          id,
          titulo: testInfo.title.replace(/^(I\d+|R\d+)\s*·\s*/, ''),
          situacao: testInfo.status,
          arquivo: path.relative(config.raizProjeto, testInfo.file),
          video: video_arquivo,
          imagens: capturas,
        },
        null,
        2,
      ),
      'utf-8',
    );
  },
});

module.exports = { test, expect: base.expect, PASTA_EVIDENCIAS };
