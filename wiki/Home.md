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
