# Gerenciamento de Requisitos

Como os requisitos deste projeto são **armazenados, atribuídos, versionados, alterados e
reportados**. É a contraparte da especificação: a especificação diz o que o sistema deve ser;
esta página diz como esse conjunto se mantém confiável com o tempo.

---

## 1. O que é, e o que compõe um plano

> **Gerenciamento de requisitos:** "O processo de gerenciar os requisitos existentes e os
> produtos de trabalho relacionados a requisitos, incluindo o armazenamento, a alteração e o
> rastreamento (rastreabilidade) dos requisitos."
> — Glossário, verbete *Gerenciamento de requisitos*, p. 15

O Handbook de Gerenciamento de Requisitos lista o conteúdo de um **plano de gerenciamento de
requisitos (RMP)** (Definição 1-2, p. 16): cenário de requisitos; atributos e visualizações;
critérios e métodos de priorização; versionamento e processo de mudança; rastreabilidade;
gerenciamento de variantes; relatórios; o processo de ER e seu aprimoramento; ferramentas.

Esta tabela é o RMP do Hora do Remédio, com o estado honesto de cada item:

| Item do RMP (Definição 1-2) | Onde está neste projeto | Estado |
|---|---|---|
| Cenário de requisitos | [Engenharia de Requisitos §2](Engenharia-de-Requisitos#2-os-produtos-de-trabalho-de-requisitos-deste-projeto) | definido |
| Atributos e visualizações | [§2](#2-esquema-de-atributos) e [§3](#3-visualizações) desta página | definido |
| Critérios e métodos de priorização | [Priorização e Backlog](Priorizacao-e-Backlog) | definido |
| Versionamento e processo de mudança | [§4](#4-versionamento) e [§5](#5-processo-de-mudança) desta página | **parcial** — baseline 1.0.0 existe; falta versão por requisito |
| Rastreabilidade | [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade) | definido |
| Gerenciamento de variantes | — | **não se aplica hoje** (ver [§7](#7-o-que-este-projeto-não-gerencia)) |
| Relatórios | [§6](#6-relatórios) desta página | **parcial** |
| Processo de ER e aprimoramento | [Validação e Verificação](Validacao-e-Verificacao) | parcial |
| Ferramentas | GitHub Issues, labels e wiki; sem ferramenta de ER | definido, com limitação |

---

## 2. Esquema de atributos

O handbook recomenda seis etapas para projetar um esquema de atributos (§3.4, p. 46):
identificar fontes de atributos, selecionar atributos, definir valores permitidos, definir
dependências, dar suporte ao registro e documentar o esquema. E adverte: o esquema "deve ser
definido **antes** do início da documentação dos requisitos (…) Melhorias e alterações
posteriores geralmente só são possíveis com grande esforço" (§3.4, p. 46).

> **Neste projeto o esquema foi definido depois** — a documentação já existia. É uma inversão em
> relação à recomendação, e explica por que alguns atributos estão vazios para requisitos
> antigos.

### Atributos adotados

As Tabelas 2 e 3 do handbook (p. 41–42) listam os atributos de uso frequente. Seguindo a
orientação de só adotar o que alguém realmente usa (§3.4.1, p. 47), este projeto usa **nove**:

| Atributo | Valores permitidos | Onde é registrado | Origem no handbook |
|---|---|---|---|
| **ID** | `RFxx`, `RNxx`, `RNFxx`, `RESxx`, `HUxx`, `UCxx`, `CTxx`, `CFxx` | Tabelas da wiki; comentários no código | Identificação (§3.1, p. 42) |
| **Tipo** | funcional · qualidade · restrição · regra de negócio | Página onde o requisito vive | Tabela 3, "Tipos de requisito" |
| **Fonte** | prompt master · espec. do portal · decisão de arquitetura · desconhecida | Coluna "Origem" das tabelas | Tabela 2, "Fonte" |
| **Justificativa** | texto livre | Notas em bloco de citação nas páginas de regras | Tabela 2, "Justificativa" |
| **Estado de garantia** | `garantido` · `parcial` · `declarado` | [Requisitos Não Funcionais](Requisitos-Nao-Funcionais); [Limitações Conhecidas](Limitacoes-Conhecidas) | Tabela 3, "Status do conteúdo" (adaptado) |
| **Status de verificação** | tem teste · sem teste | [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade) | Tabela 3, "Status da verificação" |
| **Prioridade** | ver [Priorização e Backlog](Priorizacao-e-Backlog) | Labels e ordem do card | Tabela 2, "Prioridade" |
| **Componente técnico** | caminho do arquivo | Coluna "Implementação" | Recomendação explícita do handbook, p. 42 |
| **Casos de teste** | `CTxx` / arquivo de teste | Coluna "Verificação" | Recomendação explícita do handbook, p. 42 |
| **Referências cruzadas** | IDs relacionados | Links entre páginas | Tabela 3, "Referências cruzadas" |

### Atributos deliberadamente **não** adotados

| Atributo do handbook | Por que não |
|---|---|
| **Esforço** (Tabela 3) | Não há estimativa por requisito; o projeto não trabalha com orçamento de horas. |
| **Estabilidade** e **Criticidade** (Tabela 2) | Seriam úteis, mas não há dado histórico para preenchê-los sem inventar. **Candidatos a adoção** — criticidade ajudaria a priorizar RN13 ([#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34)) e RN17 ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)). |
| **Liberação** (Tabela 3) | Não existem releases nem marcos no repositório (ver [§4](#4-versionamento)). |
| **Proprietária** (Tabela 3) | Projeto de uma pessoa; o atributo seria constante. |
| **Responsabilidade legal** (Tabela 3) | Relevante para LGPD, mas exigiria análise jurídica que não foi feita. |

O handbook também trata o **gerenciamento de mudanças do próprio esquema de atributos**
(§3.5, p. 56): adotar "Criticidade" depois exige preencher o campo para os requisitos já
existentes, não só para os novos.

---

## 3. Visualizações

O handbook define visualizações como recortes do conjunto de requisitos para um público
específico, com objetivos e riscos próprios (§3.6 e §3.7, p. 58–60) — o risco principal sendo
tomar a parte pelo todo.

| Visualização | Público | Filtro |
|---|---|---|
| [Requisitos Funcionais](Requisitos-Funcionais) | Desenvolvimento | tipo = funcional |
| [Requisitos Não Funcionais](Requisitos-Nao-Funcionais) | Arquitetura, segurança | tipo = qualidade ou restrição |
| [Histórias de Usuário](Historias-de-Usuario) | Produto, QA | recorte por papel de usuário |
| [Limitações Conhecidas](Limitacoes-Conhecidas) | Quem avalia o projeto | estado ≠ garantido |
| [Pendências abertas](https://github.com/marluceqa-source/hora-do-remedio/issues?q=is%3Aissue+is%3Aopen+label%3Apend%C3%AAncia) | Execução | label `pendência`, aberto |
| [Entregas concluídas](https://github.com/marluceqa-source/hora-do-remedio/issues?q=is%3Aissue+label%3A%22conclu%C3%ADdo%22) | Avaliação | label `concluído` |

> **Risco aceito:** a página de limitações é uma visualização **negativa** — quem lê só ela
> conclui que nada funciona, e quem lê só as páginas de regras conclui que tudo funciona. As
> duas se referenciam mutuamente por isso.

---

## 4. Versionamento

O handbook distingue o nível em que se versiona (§5.1.1, p. 88):

- **Nível de documento:** cada alteração de conteúdo gera uma nova versão do documento.
- **Nível de requisito:** cada alteração do conteúdo de um requisito gera uma nova versão
  daquele requisito.

> **Neste projeto o versionamento é de documento**, não de requisito: as páginas da wiki e os
> arquivos do repositório têm histórico no Git; **um requisito individual não tem número de
> versão nem data de alteração.** Para saber quando RN12 mudou, é preciso ler o histórico da
> página.

### Baseline

> **Baseline:** "Uma configuração estável, com mudança controlada, de produtos de trabalho."
> — Glossário, verbete *Baseline, linha de base*, p. 3

**A primeira baseline existe desde o card [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38):**
**1.0.0**, de 25 de novembro de 2026, marcada pela tag anotada
[`v1.0.0`](https://github.com/marluceqa-source/hora-do-remedio/releases/tag/v1.0.0) no
repositório e declarada na [Home](Home#baseline-da-especificação) da wiki, com o escopo coberto
e — igualmente importante — o escopo **não** coberto.

O handbook aponta que baselines servem ao planejamento e à definição de releases (Glossário,
p. 3; §5.1, p. 85). Com a 1.0.0 é possível dizer "esta é a especificação da versão X" com
precisão: a tag congela o código e a documentação de requisitos no mesmo ponto.

> **O que continua faltando:** a baseline é de **documento**, não de **item**. Ela congela o
> conjunto, mas cada requisito ainda não carrega a sua própria versão — então continua
> impossível responder "em que versão RN12 mudou?" sem ler o histórico do Git. É a limitação
> registrada logo acima, e o handbook a trata como controle de versão em nível de item
> (§5.1, p. 85).

### Ciclo de vida que o projeto **de fato** versiona bem

Ironia útil: o produto versiona **prescrições** com rigor maior do que o projeto versiona seus
próprios requisitos. `TreatmentMedication.previous_version_id` encadeia versões, nunca
sobrescreve, e preserva o histórico dependente (RN27) — exatamente o que o handbook descreve
como controle de versão em nível de item (§5.1, p. 85). Ver
[Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento).

---

## 5. Processo de mudança

> **Gerenciamento de mudanças:** "Uma maneira controlada de efetuar ou negar uma mudança
> solicitada em um produto de trabalho." — Glossário, verbete *Gerenciamento de mudanças*, p. 14

O handbook descreve o processo de gerenciamento de mudança em §5.3 (p. 105), incluindo a
avaliação da solicitação antes da decisão. O processo em vigor aqui, na prática:

```
1. A necessidade aparece (bug, lacuna, pedido novo)
        ↓
2. Abre-se um card (issue) com label de tipo e de estado
        ↓
3. Análise de impacto na Matriz de Rastreabilidade
   — quais RN, RF, testes e páginas são afetados
        ↓
4. Implementação: código + teste + atualização da wiki no mesmo movimento
        ↓
5. O card é fechado com a label "concluído";
   se a entrega for parcial, a lacuna vai para Limitações Conhecidas
```

**Regra de ouro adotada:** nenhuma mudança de regra de negócio é considerada concluída sem (a)
teste que falharia antes, (b) atualização da página de regras e (c) atualização da matriz. É o
que impede a documentação de divergir do código — o risco que o handbook associa à falta de
rastreabilidade (§6.1, p. 111).

**Não há comitê de mudanças**, e não deveria haver em um projeto desta escala. A decisão é de
quem mantém o repositório.

---

## 6. Relatórios

O handbook dedica o capítulo 8 (p. 167) aos relatórios no gerenciamento de requisitos:
estabelecer um sistema de relatórios, com objetivos, benefícios e riscos de uso (§8.1 e §8.3).

O que existe hoje:

| Relatório | Fonte | Periodicidade |
|---|---|---|
| Cobertura de testes | `pytest-cov` → `htmlcov/`, `reports/` | A cada execução manual |
| Contagem de cenários CT rastreados | `grep -rioE "ct[0-9]{2}" tests` | Manual |
| Estado das pendências | Labels e issues do GitHub | Contínuo |
| Divergência entre OpenAPI e rotas | `tests/contract/test_openapi_contract.py` | A cada execução da suíte |
| Suíte na CI | [`.github/workflows/tests.yml`](../blob/main/.github/workflows/tests.yml) | A cada push |

**O que falta** (card [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44)): nenhum relatório mostra *o estado dos requisitos* (quantos garantidos, parciais,
declarados) de forma automática — hoje isso é contado à mão nas páginas desta wiki, e por isso
pode envelhecer. O handbook alerta justamente contra relatórios que dão falsa confiança
(§8.3, p. 185).

---

## 7. O que este projeto **não** gerencia

| Tema do handbook | Situação aqui |
|---|---|
| **Variantes** (cap. 7, p. 145) | Não há linha de produto nem variantes. Bot e portal são **dois públicos do mesmo produto**, não duas variantes — compartilham a mesma camada `services/`. Se amanhã existir uma versão para outra instituição, o capítulo 7 passa a valer. |
| **Ferramenta de ER** (cap. 11, p. 219) | Nenhuma. Os requisitos vivem em Markdown versionado; a rastreabilidade é mantida à mão. Para o tamanho do projeto é adequado; o risco é o envelhecimento silencioso. |
| **Gerenciamento ágil formal** (cap. 10, p. 207) | O projeto usa backlog de issues com labels, sem sprints, sem estimativa e sem velocidade. O handbook mapeia atividades de gerenciamento de requisitos para papéis ágeis (§10.3) — aqui todos os papéis são a mesma pessoa. |
| **Processo de ER medido** (cap. 9, p. 189) | Não há métrica de processo (tempo de ciclo, retrabalho). |

---

## Resumo

- O RMP existe e está documentado, mas **versionamento por requisito e baseline não existem**.
- O esquema de atributos usa nove atributos das Tabelas 2 e 3 do handbook, e declara os que
  recusou.
- O processo de mudança é simples e tem uma regra forte: código, teste e wiki mudam juntos.
- A maior fragilidade é a **manutenção manual** da rastreabilidade e a ausência de relatório
  automático sobre o estado dos requisitos.

---

## Próximo

- [Priorização e Backlog](Priorizacao-e-Backlog)
- [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade)
- [Validação e Verificação](Validacao-e-Verificacao)
