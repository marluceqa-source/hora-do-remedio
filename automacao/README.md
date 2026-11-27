# Automação de testes — Hora do Remédio

Suíte de testes de caixa-preta do **Hora do Remédio**, escrita do ponto de vista de quem
usa o sistema.

> **Este branch tem apenas os testes.** O código da aplicação não está aqui — ele vive no
> `main`. Para rodar, aponte a automação para um diretório onde a aplicação esteja (veja
> [Como rodar](#como-rodar)).

A automação não importa código do projeto e não altera nenhum arquivo dele. A relação é de
fora para dentro: ela sobe a aplicação, usa pelas portas públicas — navegador, API e bot —
e observa o resultado.

**161 testes: 160 aprovados e 1 ignorado por decisão.**

| Projeto | O que cobre | Ferramenta | Testes |
| --- | --- | --- | --- |
| [`testes-playwright/`](testes-playwright/README.md) | Portal web e API REST | Playwright (JavaScript) | 85 |
| [`testes-bot-telegram/`](testes-bot-telegram/README.md) | Bot do Telegram | pytest (Python) | 76 |

## Técnicas de teste usadas

Cada grupo de testes nasceu de uma técnica, e cada teste cita a sua no próprio código:

| Técnica | Onde | Documentação |
| --- | --- | --- |
| **VADER** (Verbs, Authorization, Data, Errors, Responsiveness) | API REST | [casos de API](testes-playwright/docs/casos-de-teste-api-vader.md) |
| **Gherkin** (Dado / Quando / Então) | Portal web | [cenários de web](testes-playwright/docs/casos-de-teste-web-gherkin.md) |
| **Heurísticas de Elisabeth Hendrickson** | Bot do Telegram | [casos do bot](testes-bot-telegram/docs/casos-de-teste-bot-heuristicas.md) |
| **ISO/IEC/IEEE 29119-3** (template de caso de teste) | API REST | [casos de API](testes-playwright/docs/casos-de-teste-api-vader.md) |
| **Session-Based Test Management** | Toda a sessão | [relatório de sessão](testes-playwright/docs/relatorio-de-sessao.md) |

## Como rodar

Você precisa dos dois lados: **este branch** (os testes) e **a aplicação** (o `main`).
O caminho mais simples é ter dois diretórios lado a lado:

```bash
git clone git@github.com:marluceqa-source/hora-do-remedio.git aplicacao
```

```bash
git clone -b ci/automacao-testes git@github.com:marluceqa-source/hora-do-remedio.git testes
```

A aplicação precisa estar pronta para subir: ambiente virtual Python criado (`.venv`),
dependências instaladas, `frontend/` com `npm install` feito e `.env` configurado — é o
que o README dela explica.

Depois, aponte a automação para ela com `APP_DIR`:

```bash
cd testes/automacao/testes-playwright && npm install && npx playwright install chromium
```

```bash
APP_DIR=../../../aplicacao npm test
```

```bash
cd testes/automacao/testes-bot-telegram && APP_DIR=../../../aplicacao ../../../aplicacao/.venv/bin/python -m pytest
```

Para não repetir `APP_DIR` a cada comando, no projeto de Playwright basta copiar
`.env.example` para `.env` e preencher uma vez.

> Se um dia este branch for integrado ao `main`, a aplicação passa a estar na própria
> árvore e nada disso é necessário: o padrão `../..` já encontra tudo.

A automação sobe a API e o portal por conta própria e usa um banco SQLite exclusivo
(`database/playwright_test.db`): **o banco de desenvolvimento não é tocado**, e nenhum
teste fala com o Telegram de verdade.

## O que não é versionado

Os artefatos de execução ficam fora do git — são reproduzidos por comando, sempre pelo
mesmo caminho:

| Artefato | Como reproduzir |
| --- | --- |
| `testes-playwright/evidencias/` — vídeos e telas de cada achado | `npm run evidencias` |
| `testes-playwright/relatorio.html` — relatório em HTML | `npm run relatorio` |
| `playwright-report/`, `test-results/`, `resultados/` | saem de qualquer execução |
| `node_modules/` | `npm install` |

## O que a sessão encontrou

Sete achados ainda sem correção, registrados como issue em Backlog no board do projeto:

| | Achado | Issue |
| --- | --- | --- |
| R1 | Profissional não verificado já tem acesso clínico | [#177](https://github.com/marluceqa-source/hora-do-remedio/issues/177) |
| R2 | Campo obrigatório aceita apenas espaços | [#178](https://github.com/marluceqa-source/hora-do-remedio/issues/178) |
| R3 | A normalização de texto depende da porta de entrada | [#179](https://github.com/marluceqa-source/hora-do-remedio/issues/179) |
| R4 | O limite de requisições é por IP, não por usuário | [#180](https://github.com/marluceqa-source/hora-do-remedio/issues/180) |
| R5 | O venv da aplicação tem shebang quebrado | [#181](https://github.com/marluceqa-source/hora-do-remedio/issues/181) |
| R6 | O bot aceita dois medicamentos com o mesmo nome | [#182](https://github.com/marluceqa-source/hora-do-remedio/issues/182) |
| R7 | Um erro de validação no último passo descarta o cadastro | [#183](https://github.com/marluceqa-source/hora-do-remedio/issues/183) |

O caminho completo — o que acontece, como reproduzir, a causa e a evidência — está no
[relatório de sessão](testes-playwright/docs/relatorio-de-sessao.md).
