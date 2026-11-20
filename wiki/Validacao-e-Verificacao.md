# Validação e Verificação de Requisitos

Duas perguntas diferentes, frequentemente confundidas: **os requisitos certos foram
especificados?** (validação) e **os requisitos foram especificados corretamente?** (verificação).

---

## 1. A distinção

> **Validação:** "O processo de confirmar que um item (um sistema, um produto de trabalho ou
> parte dele) corresponde às necessidades de seus stakeholders. Nota: em ER, validação é o
> processo de confirmar que os requisitos documentados correspondem às necessidades de seus
> stakeholders; em outras palavras: **se os requisitos certos foram especificados**."
> — Glossário, verbete *Validação*, p. 33

> **Verificação:** "O processo de confirmar que um item (um sistema, um produto de trabalho ou
> parte dele) cumpre sua especificação. Nota: verificação de requisitos é o processo de confirmar
> que os requisitos foram documentados adequadamente e satisfazem os critérios de qualidade para
> requisitos; em outras palavras, **se os requisitos foram especificados corretamente**."
> — Glossário, verbete *Verificação*, p. 34

### O veredito deste projeto, em uma linha

| | Estado |
|---|---|
| **Verificação** | **Forte.** 160 testes automatizados, 40 dos 42 cenários do prompt master rastreados, contrato OpenAPI testado, CI a cada push. |
| **Validação** | **Ausente.** Nenhum stakeholder confirmou que os requisitos correspondem às suas necessidades. Nenhum paciente, cuidador ou profissional de saúde foi consultado. |

Essa assimetria é o fato mais importante desta página. Um sistema pode cumprir perfeitamente uma
especificação que não resolve o problema de ninguém — e, por definição, os testes não detectam
isso.

---

## 2. Verificação dos requisitos (qualidade da documentação)

> **Revisão:** "Uma avaliação de um produto de trabalho por um indivíduo ou um grupo a fim de
> encontrar problemas ou sugerir melhorias. Nota: a avaliação pode ser realizada tanto em relação
> ao conteúdo quanto à conformidade." — Glossário, verbete *Revisão*, p. 28

Esta documentação foi produzida por uma revisão do prompt master e do código. Os **achados** —
problemas encontrados, não suposições — estão abaixo, cada um com o card que o acompanha
([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35), [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36), [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37), [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38), [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39), [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40), [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41), [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42), [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43), [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44), [#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45)).

| # | Achado | Tipo | Onde |
|---|---|---|---|
| 1 | O status `expired` de `ReminderEvent` **nunca é atribuído** por nenhum código, mas é tratado em relatórios e tem rótulo no bot. | Inconsistência entre especificação e implementação | [Modelagem](Modelagem-de-Requisitos#52-evento-de-lembrete-reminderevent-status) · [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35) |
| 2 | **CT17** não tem teste nem implementação; **CT28** tem comportamento testado, mas sem identificador rastreável. | Lacuna de cobertura | [Matriz](Matriz-de-Rastreabilidade#4-análise-de-cobertura) · [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35), [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36) |
| 3 | O diretório `tests/accessibility/` existe e contém **apenas `__init__.py`** — a categoria de teste pedida no prompt master (§11) está vazia. Os testes de acessibilidade reais vivem em `tests/unit/`. | Estrutura prometida e não preenchida | `tests/accessibility/` · [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41) |
| 4 | **RN01, RN08 e RN14** estão implementadas, mas sem marcação `RNxx` no código. | Rastreabilidade implícita incompleta | [Matriz](Matriz-de-Rastreabilidade#3-matriz-principal--regras-de-negócio) · [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37) |
| 5 | **RN29 e RN31** não têm origem localizável — a especificação do portal não está no repositório. | Requisito órfão | [Limitações](Limitacoes-Conhecidas) · [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) |
| 6 | Os **19 critérios de aceite** do prompt master (§15) não têm registro de conferência item a item. | Verificação não documentada | [Priorização](Priorizacao-e-Backlog#5-o-backlog-priorizado) · [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) |
| 7 | Os requisitos não funcionais **não tinham identificador** antes desta documentação. | Especificação incompleta | [Requisitos Não Funcionais](Requisitos-Nao-Funcionais) · [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43) |
| 8 | Duas numerações `RFxx` independentes coexistem (bot/API e portal), e `RF02` significa coisas diferentes em cada uma. | Ambiguidade de identificação | [Requisitos Funcionais](Requisitos-Funcionais) · mitigado, sem card |
| 9 | Vários RNF são verificáveis mas **não quantificados** (sem valor-alvo nem forma de medição). | Qualidade do requisito | [Requisitos Não Funcionais](Requisitos-Nao-Funcionais#ponto-de-atenção-mensurabilidade) · [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43) |
| 10 | Não existe **baseline** da especificação: sem tags, sem releases, sem versão na wiki. | Gerenciamento de requisitos | [Gerenciamento](Gerenciamento-de-Requisitos#baseline) · [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38) |

> **Achado 8 não será corrigido renumerando.** Renumerar invalidaria as referências já presentes
> no código, nos testes e nas issues. A mitigação adotada é o aviso explícito no topo da página de
> requisitos funcionais. Essa é uma decisão, não um esquecimento.

---

## 3. Verificação do sistema (os testes)

O prompt master pediu cinco categorias de teste (§11). O que existe:

| Categoria | Diretório | Estado |
|---|---|---|
| Unitários | `tests/unit/` | 18 arquivos — serviços, handlers do bot, RBAC, acessibilidade |
| API | `tests/api/` | 10 arquivos — rotas, isolamento, autenticação do profissional |
| Contrato | `tests/contract/` | OpenAPI: CT31–CT38 |
| Integração | `tests/integration/` | Fluxo de cadastro acessível, seed e persistência |
| Acessibilidade | `tests/accessibility/` | **vazio** (achado 3) |

**Configuração** ([`pytest.ini`](../blob/main/pytest.ini)): `--cov` com relatório de cobertura em
HTML e relatório de testes em `reports/`. **CI**
([`.github/workflows/tests.yml`](../blob/main/.github/workflows/tests.yml)): roda a suíte a cada
push na `main` e em cada pull request, publicando os dois relatórios como artefatos.

Técnicas de verificação que o prompt master exigiu e que estão em uso:

- **Mocks das integrações externas** — o Telegram nunca é chamado de verdade nos testes.
- **Relógio controlado** — `tests/unit/test_scheduler_firing.py` testa o disparo sem esperar o
  horário real.
- **Teste de contrato** — garante que `docs/openapi.yaml`, `/openapi.json` e as rotas não
  divergem (RNF20).

> Os números de cobertura **não são reproduzidos aqui**. Eles mudam a cada execução, e esta wiki
> não deve afirmar um resultado que não foi medido no momento da leitura. O último valor
> registrado está no card [#21](https://github.com/marluceqa-source/hora-do-remedio/issues/21) e
> em [Limitações Conhecidas](Limitacoes-Conhecidas).

---

## 4. O que falta para haver validação

A validação exige confirmar com os stakeholders que os requisitos correspondem às suas
necessidades. O plano completo — hipóteses sob teste, participantes, roteiro de sessão, ética e
processamento dos resultados — está em
**[Roteiro de Validação com Usuários](Roteiro-de-Validacao-com-Usuarios)**. Em resumo, usando as
técnicas do Handbook de Elicitação:

| Passo | Técnica | O que produz |
|---|---|---|
| 1 | **Observação de campo / investigação contextual** (§3.1.2, p. 79) com 3 a 5 pacientes do perfil-alvo, na hora real da dose | Evidência de que o fluxo de confirmação funciona para quem não lê |
| 2 | **Entrevista** (§3.1.1, p. 68) com 2 a 3 cuidadores | Validação de RF12 e do que eles esperam sobre doses sem confirmação |
| 3 | **Entrevista** com 2 médicos e 1 enfermeiro | Validação de RN20 — hoje decidida sem contraditório clínico |
| 4 | **Protótipo** (§3.2.3, p. 111) dos ícones e dos áudios | Teste de compreensão dos símbolos, que vieram do prompt sem validação |
| 5 | Revisão das páginas desta wiki pelos participantes | Confirmação de que o documentado é o necessário — card [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) |

Sem os passos 1 a 4, as decisões de [acessibilidade](Acessibilidade) continuam sendo hipóteses
bem fundamentadas — e a wiki deve dizer isso, não o contrário.

---

## 5. Checklist de revisão para requisitos novos

Construído a partir das definições do glossário (verbetes *Requisito*, p. 26; *Critério de
qualidade (na ER)*, p. 8; *Rastreabilidade*, p. 26) e das colunas exigidas pelas páginas desta
wiki.

Antes de considerar um requisito novo documentado, ele tem:

- [ ] **ID** no espaço de numeração correto (`RF`, `RN`, `RNF`, `RES`, `HU`, `UC`)
- [ ] **Tipo** definido: funcional, qualidade ou restrição
- [ ] **Fonte** nomeada — e "desconhecida" é uma resposta válida, melhor que uma inventada
- [ ] **Justificativa**: por que existe
- [ ] **Critério de aceitação** verificável (Gherkin, quando couber)
- [ ] **Componente técnico**: onde será implementado
- [ ] **Caso de teste**: como será verificado
- [ ] **Referências cruzadas** para os requisitos que ele afeta
- [ ] **Estado de garantia** honesto: `garantido`, `parcial` ou `declarado`

> **Complemento baseado em conhecimento externo aos arquivos fornecidos:** os critérios clássicos
> de qualidade de requisito individual — não ambíguo, completo, consistente, verificável,
> necessário, rastreável — pertencem ao CPRE Foundation Level e a normas como a
> ISO/IEC/IEEE 29148, que **não estão** entre os documentos de referência usados nesta wiki. O
> checklist acima deriva das definições do glossário e das práticas deste projeto, não de um
> gabarito do IREB citado aqui.

---

## Resumo

- **Verificação forte, validação ausente** — e isso está registrado, não disfarçado.
- A revisão que produziu esta documentação encontrou **10 achados**, todos com card.
- O achado mais relevante tecnicamente é o estado `expired` inalcançável; o mais relevante
  estrategicamente é a falta de contato com usuários reais.
- Um checklist de revisão passa a existir para os próximos requisitos.

---

## Próximo

- [Priorização e Backlog](Priorizacao-e-Backlog)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
- [Engenharia de Requisitos](Engenharia-de-Requisitos)
