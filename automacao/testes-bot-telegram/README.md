# Testes do bot do Telegram — Hora do Remédio

> **Este branch tem apenas os testes.** O código da aplicação está no `main`, não aqui.
> Aponte `APP_DIR` para um diretório onde a aplicação esteja — veja
> [como rodar](../README.md#como-rodar).

Automação de testes do **bot do Telegram** do Hora do Remédio, desenhada com as
**heurísticas de teste de Elisabeth Hendrickson** (Test Heuristics Cheat Sheet, Test
Obsessed): ataques a tipos de dados, testes de strings, CRUD, Siga os Dados, Interrupções
e "adote abordagem contrária".

**76 testes, cobrindo 43 casos.** Documentação completa em
[docs/casos-de-teste-bot-heuristicas.md](docs/casos-de-teste-bot-heuristicas.md).

---

## Por que este projeto é separado do de Playwright

O bot é **python-telegram-bot rodando em polling**: não tem porta HTTP, não tem tela e não
responde a requisição nenhuma. Playwright não alcança isso — e fingir que alcança seria
pior do que não testar.

O que este projeto faz é chamar **os handlers de verdade do bot** como funções, passando
um `update` falso (que registra o que o bot respondeu) e um `context` com estado real de
conversa. Nada é simulado do lado do bot: o código exercitado é exatamente o que roda em
produção quando alguém manda uma mensagem.

```
Telegram  →  [ não entra aqui ]  →  handler do bot  →  serviços  →  banco
                                   └──── é isto que os testes exercitam ────┘
```

| Camada | Onde é testada |
| --- | --- |
| Portal web e API REST | `../testes-playwright` (Playwright, JavaScript) |
| Bot do Telegram | **este projeto** (pytest, Python) |

---

## Como executar

Pré-requisito: a aplicação `hora-do-remedio` ao lado, com o ambiente virtual criado
(`.venv`) e as dependências instaladas. Nenhuma instalação é necessária neste projeto — ele
usa o Python da própria aplicação.

```bash
../../.venv/bin/python -m pytest
```

Por grupo de heurística:

```bash
../../.venv/bin/python -m pytest -m dados
```

| Marcador | Heurística |
| --- | --- |
| `-m dados` | Ataques de Tipos de Dados |
| `-m strings` | Testes de Strings |
| `-m crud` | CRUD e Siga os Dados |
| `-m interrupcoes` | Interrupções |
| `-m contraria` | Adote abordagem contrária |

Um caso específico, pelo ID:

```bash
../../.venv/bin/python -m pytest -k ct_bot_x01
```

Se a aplicação estiver em outro lugar, aponte com `APP_DIR`:

```bash
APP_DIR=/caminho/para/hora-do-remedio ../../.venv/bin/python -m pytest
```

> **Nada é enviado ao Telegram** e **nenhum token é necessário**. O banco é SQLite em
> memória, criado e destruído a cada teste: o banco de desenvolvimento da aplicação não é
> tocado.

---

## Estrutura

```
testes-bot-telegram/
├── conftest.py              # banco em memória por teste e redirecionamento dos handlers
├── pytest.ini               # modo assíncrono e marcadores por heurística
├── suporte/
│   ├── fakes.py             # dublês de Update e Context do python-telegram-bot
│   ├── conversa.py          # condutor da conversa de cadastro (16 estados)
│   ├── cenarios.py          # pré-condições montadas direto no banco
│   └── dados.py             # cargas de entrada de cada heurística
├── testes/
│   ├── test_ataques_tipos_de_dados.py
│   ├── test_ataques_de_strings.py
│   ├── test_crud_e_siga_os_dados.py
│   ├── test_interrupcoes.py
│   ├── test_abordagem_contraria.py
│   └── test_mapa_da_conversa.py
└── docs/casos-de-teste-bot-heuristicas.md
```

### Decisões que valem explicação

- **O condutor de conversa.** Cadastrar um remédio leva 16 estados. Repetir isso em cada
  teste esconderia o que está sendo investigado, então o percurso mora em
  `suporte/conversa.py` e o teste só diz o que foi digitado ou tocado:

  ```python
  pessoa = await Conversa().ate_a_data_de_inicio()
  await pessoa.digitar('30/02/2026')
  assert pessoa.disse('Data inválida')
  ```

- **O mapa de estados é conferido contra o bot.** `testes/test_mapa_da_conversa.py`
  compara o condutor com o `ConversationHandler` de verdade. Se alguém mudar a conversa do
  bot, a falha aparece ali, em três testes — e não espalhada por sessenta.

- **A voz é silenciada.** Cada mensagem do bot passa por `pyttsx3`, que abriria o
  sintetizador do sistema operacional. Uma fixture automática o substitui.

- **Massa única por teste.** Cada teste usa um `telegram_user_id` novo, então um teste
  nunca enxerga o dado do outro.

---

## O que estes testes encontraram

| | Observação | Caso |
| --- | --- | --- |
| **R6** | Dois medicamentos com o mesmo nome são aceitos sem aviso de duplicidade | CT-BOT-D01 |
| **R7** | Um erro de validação no último passo descarta o rascunho inteiro — a pessoa recomeça do primeiro campo | CT-BOT-S06 |
| — | O bot **faz** `strip()` nos textos, enquanto a API e o portal **não** fazem (ver R3): quem entra pelo bot fica com um dado mais limpo do que quem entra pelo portal | CT-BOT-S02 |
| — | A proteção entre usuários é consistente: confirmar, adiar ou marcar "não tomei" no lembrete de outra pessoa é recusado nos três caminhos | CT-BOT-X01 a X03 |

Tudo registrado no
[relatório de sessão](../testes-playwright/docs/relatorio-de-sessao.md), junto com os
riscos encontrados no portal e na API.
