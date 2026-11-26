# Hora do Remédio 💊 — Wiki

Sistema de lembretes de medicamentos composto por **três entregas integradas**:

| Entrega | O que é | Público |
|---|---|---|
| **Bot Telegram** | Interface principal de uso diário, navegável só por botões, com áudio, OCR e voz. | Pessoas idosas, não alfabetizadas ou com baixa visão. |
| **API REST** | Camada de integração documentada em OpenAPI, usada pelo bot, pelo portal e por integrações externas. | Desenvolvedores / apps de cuidador. |
| **Portal Web** | Painel para profissionais de saúde prescreverem e acompanharem tratamentos. | Médicos, enfermeiros e outros profissionais. |

Nenhuma regra de negócio é duplicada entre os processos: bot, API e portal compartilham a
mesma camada `services/`.

---

## Baseline da especificação

> **Baseline:** "Uma configuração estável, com mudança controlada, de produtos de trabalho."
> — Glossário, verbete *Baseline, linha de base*, p. 3

| | |
|---|---|
| **Versão** | **1.0.0** |
| **Tag** | [`v1.0.0`](https://github.com/marluceqa-source/hora-do-remedio/tree/v1.0.0) |
| **Data** | 25 de novembro de 2026 |
| **Escopo** | Entrega do projeto final: bot do Telegram, API REST e portal web de profissionais, com a documentação de requisitos desta wiki. |

### O que esta baseline cobre

| Produto de trabalho | Estado em 1.0.0 |
|---|---|
| Requisitos funcionais | RF do bot/API e RF do portal — ver [Requisitos Funcionais](Requisitos-Funcionais) |
| Requisitos não funcionais | RNF01–RNF23 e restrições RES01–RES07 |
| Regras de negócio | **RN01–RN32**, com 29 marcadas no código |
| Histórias de usuário | HU01–HU16 com critérios em Gherkin |
| Cenários de teste | 41 dos 42 CT rastreáveis por busca nos testes |
| Suíte automatizada | 185 testes, 86% de cobertura |

### O que esta baseline **não** cobre

As 20 pendências abertas, estimadas em **155,2 ± 15,7 h** — ver
[Priorização e Backlog](Priorizacao-e-Backlog). Três lacunas conhecidas ficam explicitamente
**fora** desta baseline, e não devem ser lidas como atendidas:

- **RN17** — a política de retenção é configurável, mas não há expurgo automático ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)).
- **RN29 e RN31** — sem origem localizável na especificação ([#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)).
- **CT17** — o status `expired` de um lembrete nunca é atribuído por nenhum código ([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35)).

A lista completa está em [Limitações Conhecidas](Limitacoes-Conhecidas).

> **Como esta baseline muda.** Alteração de requisito depois de 1.0.0 segue o processo de
> mudança de [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos#5-processo-de-mudança) e
> entra na próxima versão — a tag `v1.0.0` continua apontando para a especificação como ela
> está nesta data.

---

## Índice

### Produto e requisitos
- **[Visão Geral do Sistema](Visao-Geral)** — objetivo, escopo, arquitetura e tecnologias.
- **[Requisitos Funcionais](Requisitos-Funcionais)** — RF do bot/API e RF do portal.
- **[Requisitos Não Funcionais](Requisitos-Nao-Funcionais)** — RNF01–RNF23 e restrições RES01–RES07.
- **[Histórias de Usuário](Historias-de-Usuario)** — HU01–HU16 com critérios de aceitação em Gherkin.
- **[Acessibilidade](Acessibilidade)** — decisões de acessibilidade e por que elas existem.

### Engenharia de Requisitos
Documentação de requisitos seguindo a estrutura e o vocabulário do **CPRE/IREB**, com a fonte de
cada definição indicada.
- **[Engenharia de Requisitos](Engenharia-de-Requisitos)** — o processo adotado, os produtos de trabalho e as referências.
- **[Stakeholders e Fontes de Requisitos](Stakeholders-e-Fontes-de-Requisitos)** — quem é afetado, de onde vieram os requisitos, quais técnicas foram usadas e quais conflitos existem.
- **[Modelagem de Requisitos](Modelagem-de-Requisitos)** — contexto, estrutura de informações, casos de uso, estados e cenários.
- **[Matriz de Rastreabilidade](Matriz-de-Rastreabilidade)** — requisito → código → teste → card.
- **[Gerenciamento de Requisitos](Gerenciamento-de-Requisitos)** — atributos, versionamento, mudanças e relatórios.
- **[Priorização e Backlog](Priorizacao-e-Backlog)** — qual técnica foi usada e em que ordem fazer.
- **[Validação e Verificação](Validacao-e-Verificacao)** — o que está verificado, o que **não** está validado e os 10 achados da revisão.
- **[Roteiro de Validação com Usuários](Roteiro-de-Validacao-com-Usuarios)** — plano de elicitação direta com o público-alvo: hipóteses, técnicas e sessões.
- **[Glossário](Glossario)** — termos do domínio, homônimos e vocabulário de ER.

### Regras de negócio
- **[Regras de Negócio — Bot e API](Regras-de-Negocio-Bot-e-API)** — RN01 a RN18.
- **[Regras de Negócio — Portal](Regras-de-Negocio-Portal)** — RN19 a RN32.
- **[Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento)** — rascunho → ativo → suspenso, e versionamento.

### Segurança e governança
- **[Papéis e Permissões](Papeis-e-Permissoes)** — RBAC, verificação de profissionais, vínculos.
- **[Segurança e Privacidade](Seguranca-e-Privacidade)** — autenticação, MFA, sessões, auditoria.

### Estado do projeto
- **[Limitações Conhecidas](Limitacoes-Conhecidas)** — o que **não** está garantido pelo código.
- **[Priorização e Backlog](Priorizacao-e-Backlog)** — o que vem primeiro, e por quê.

---

## Princípios que atravessam todo o sistema

1. **Nada clínico é assumido.** O sistema não prescreve, não sugere dosagem e não altera
   horários por conta própria. Tudo que é clínico vem de uma pessoa — o paciente ou um
   profissional identificado.
2. **Ausência de resposta não é um fato clínico.** Um lembrete sem confirmação nunca é
   registrado como "não tomou" (ver [RN12](Regras-de-Negocio-Bot-e-API)).
3. **Reconhecimento automático sempre pede confirmação.** OCR de foto e transcrição de voz
   são sugestões exibidas para conferência, nunca substituem o que a pessoa informou
   ([RN10](Regras-de-Negocio-Bot-e-API), [RN11](Regras-de-Negocio-Bot-e-API)).
4. **Acesso a dados é sempre por vínculo explícito.** Paciente vê o que é seu; cuidador e
   profissional só veem o que foi autorizado e não revogado.
5. **Operação sensível é auditável.** O portal registra quem fez o quê, quando
   ([RN32](Regras-de-Negocio-Portal)).
6. **A interface fala português.** Nenhuma mensagem crua de framework (Pydantic, navegador,
   Axios) chega ao usuário final.

---

## Sobre esta documentação

As páginas da seção **Engenharia de Requisitos** citam explicitamente a fonte de cada definição:
o *Glossary of Requirements Engineering Terminology* (IREB CPRE 2.2), o *Handbook Requirements
Elicitation* (v2.1.0), o *Handbook for Requirements Management* (v2.1.0) e o *Syllabus CPRE
Advanced Level — Requirements Modeling* (v3.1.0). As referências completas estão em
[Engenharia de Requisitos](Engenharia-de-Requisitos#referências).

Quando uma afirmação vem de conhecimento geral e não desses documentos, ela está marcada como
tal. Quando uma regra está apenas declarada e não garantida pelo código, isso também está dito —
é o papel de [Limitações Conhecidas](Limitacoes-Conhecidas) e das colunas "Estado" das tabelas.
