# Engenharia de Requisitos no Hora do Remédio

Esta página explica **como os requisitos deste projeto são especificados e gerenciados**, usando
o vocabulário e a estrutura do CPRE/IREB. Ela é o ponto de entrada da trilha de requisitos da
wiki: as demais páginas desta seção desenvolvem cada atividade.

> **Nota sobre as fontes.** As páginas desta seção citam explicitamente o material de referência
> utilizado. Quando a afirmação é uma decisão **deste projeto**, e não uma recomendação do
> material, isso está dito. As referências completas estão [ao final desta página](#referências).

---

## 1. Os termos, como o IREB os define

| Termo | Definição (tradução direta do glossário) | Fonte |
|---|---|---|
| **Engenharia de Requisitos (ER)** | "A abordagem sistemática e disciplinada para a especificação e o gerenciamento de requisitos, com o objetivo de entender os desejos e as necessidades dos stakeholders e minimizar o risco de entregar um sistema que não atenda a esses desejos e necessidades." | Glossário, verbete *Engenharia de Requisitos*, p. 11 |
| **Requisito** | "1. Uma necessidade percebida por um stakeholder. 2. Uma capacidade ou propriedade que um sistema deve ter. 3. Uma representação documentada de uma necessidade, capacidade ou propriedade." | Glossário, verbete *Requisito*, p. 26 |
| **Elicitação de requisitos** | "O processo de buscar, capturar e consolidar requisitos a partir das fontes disponíveis, potencialmente incluindo a reconstrução ou a criação de requisitos." | Glossário, verbete *Elicitação de Requisitos*, p. 11 |
| **Especificação de requisitos** | "Uma coleção representada sistematicamente de requisitos, tipicamente para um sistema, que satisfaz critérios dados." | Glossário, verbete *Especificação de requisitos*, p. 13 |
| **Gerenciamento de requisitos** | "O processo de gerenciar os requisitos existentes e os produtos de trabalho relacionados a requisitos, incluindo o armazenamento, a alteração e o rastreamento (rastreabilidade) dos requisitos." | Glossário, verbete *Gerenciamento de requisitos*, p. 15 |

A distinção que organiza esta seção da wiki é exatamente a da definição de ER: **especificação**
(o que o sistema deve ser) e **gerenciamento** (como esses requisitos são mantidos ao longo do
tempo).

---

## 2. Os produtos de trabalho de requisitos deste projeto

O Handbook de Gerenciamento de Requisitos trata o "cenário de requisitos" — os tipos de
artefato gerenciados e o nível de detalhe de cada um — como o primeiro item do plano de
gerenciamento de requisitos (Definição 1-2, p. 16). No Hora do Remédio, esse cenário é este:

| Produto de trabalho | Onde está | Papel |
|---|---|---|
| **Prompt master** | **Não versionado** — pasta local `Criacao/` | Especificação de requisitos do cliente: RF01–RF14, RN01–RN18, CT01–CT42 e critérios de aceite do bot/API. Citado nesta wiki por seção (ex.: "prompt §7"). |
| **Especificação do portal** | **Não está no repositório** | Origem declarada de RF01–RF08 e RN19–RN32 do portal. Ver [limitação](#5-pontos-de-atenção-e-riscos). |
| **Requisitos funcionais** | [Requisitos Funcionais](Requisitos-Funcionais) | RF do bot/API e RF do portal, com apontamento para o código. |
| **Requisitos de qualidade e restrições** | [Requisitos Não Funcionais](Requisitos-Nao-Funcionais) | RNF01–RNF16, especificados nesta documentação a partir do prompt master e do código. |
| **Regras de negócio** | [Bot e API](Regras-de-Negocio-Bot-e-API) · [Portal](Regras-de-Negocio-Portal) | RN01–RN32, com o local de garantia e o teste correspondente. |
| **Histórias de usuário e critérios de aceitação** | [Histórias de Usuário](Historias-de-Usuario) | HU01–HU16, com critérios em Gherkin. |
| **Modelos** | [Modelagem de Requisitos](Modelagem-de-Requisitos) | Visões de contexto, estrutura de informações, casos de uso, estados e cenários. |
| **Rastreabilidade** | [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade) | Requisito → código → teste → card. |
| **Backlog** | [Issues do repositório](https://github.com/marluceqa-source/hora-do-remedio/issues) | Itens de trabalho priorizados. Ver [Priorização e Backlog](Priorizacao-e-Backlog). |
| **Especificação de interface** | [`docs/openapi.yaml`](../blob/main/docs/openapi.yaml) | Contrato da API, com teste de contrato em `tests/contract/`. |
| **Glossário do domínio** | [Glossário](Glossario) | Termos do domínio e termos de ER usados nesta wiki. |

O glossário do IREB distingue **especificação de requisitos do cliente** ("uma descrição
grosseira das capacidades requeridas de um sistema a partir da perspectiva do cliente",
p. 14) de especificação de requisitos de sistema. O prompt master é do primeiro tipo: ele
descreve o que se espera do produto, não como o sistema realiza. Esta wiki é a especificação
derivada dele.

---

## 3. O processo de requisitos que de fato ocorreu

Ser honesto sobre a ordem dos fatos importa para quem lê esta documentação: **o sistema foi
construído a partir do prompt master e a especificação estruturada foi reconstruída depois, a
partir do prompt e do código existente.**

A própria definição de elicitação do IREB admite esse caminho — ela inclui "potencialmente a
**reconstrução** ou a criação de requisitos" (Glossário, p. 11). O Handbook de Elicitação
classifica as técnicas aplicáveis a essa situação como **técnicas baseadas em artefatos**:
leitura baseada em perspectiva, **arqueologia de sistemas** e reutilização de requisitos
(§3.1, p. 68, e §3.1.4, p. 98).

Qual técnica foi usada em cada artefato está em
[Stakeholders e Fontes de Requisitos](Stakeholders-e-Fontes-de-Requisitos#3-técnicas-de-elicitação-aplicadas).

### Consequência metodológica

Reconstruir requisitos a partir do código tem um limite conhecido: **o código mostra o que o
sistema faz, não o que os stakeholders precisam.** Requisitos que ninguém implementou não
aparecem nessa leitura. Por isso esta documentação separa, em todas as páginas, o que está
**garantido no código** do que está apenas **declarado** — e mantém a página
[Limitações Conhecidas](Limitacoes-Conhecidas) como contrapeso.

---

## 4. Classificação dos requisitos adotada

O Handbook de Gerenciamento de Requisitos responde à pergunta "que tipos de requisitos devem
ser considerados?" com a classificação do CPRE Foundation Level (§2.1.1, p. 25):

| Tipo | Definição citada no handbook | Nesta wiki |
|---|---|---|
| **Requisito funcional** | "Um requisito relativo a um resultado de comportamento que deve ser fornecido por uma função do sistema." (Definição 2-3, p. 25) | Prefixo `RF` — [Requisitos Funcionais](Requisitos-Funcionais) |
| **Requisito de qualidade** | "Um requisito que diz respeito a uma preocupação de qualidade que não é coberta por requisitos funcionais." (Definição 2-4, p. 25) | Prefixo `RNF` — [Requisitos Não Funcionais](Requisitos-Nao-Funcionais) |
| **Restrição** | "Especificações organizacionais, legais ou técnicas (geralmente limitações) para a realização do sistema planejado." (§2.1.1, p. 25) | Prefixo `RES` — [Requisitos Não Funcionais](Requisitos-Nao-Funcionais#restrições) |

As **regras de negócio** (RN01–RN32) não são uma quarta categoria do IREB. Neste projeto elas
funcionam como um **conjunto nomeado de restrições de domínio e de comportamento**, referenciado
pelos RF e pelos testes. Essa é uma convenção deste projeto, herdada do prompt master
(seção 7), e está mantida porque é a numeração que o código já cita.

---

## 5. Pontos de atenção e riscos

| Ponto | Por que importa |
|---|---|
| **Nenhuma elicitação direta com usuários reais** ([#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40)) | O público-alvo declarado é composto por pessoas idosas, não alfabetizadas ou com baixa visão. Nenhuma entrevista, observação de campo ou investigação contextual foi realizada — são exatamente as técnicas que o Handbook de Elicitação indica para esse perfil (§3.1.1 e §3.1.2, p. 68 e p. 79). As decisões de acessibilidade são, hoje, **hipóteses bem fundamentadas, não achados validados**. |
| **A especificação do portal não está no repositório** ([#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)) | RN29 e RN31 não têm correspondência no código e não há documento-fonte para conferir. Sem a fonte, a lacuna não pode ser fechada — só registrada. |
| **As duas fontes primárias ficam fora do repositório** | O prompt master é mantido apenas localmente e a especificação do portal não existe aqui. Quem clonar o projeto **não alcança** as fontes dos requisitos: depende desta wiki, que por isso cita prompt e seção em cada afirmação em vez de só apontar o arquivo. É uma escolha deliberada de quem mantém o projeto, e o custo dela é este. |
| **Dois cenários de teste sem cobertura rastreável** ([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35), [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36)) | Dos 42 cenários CT do prompt master, **40 estão anotados** nos testes. Faltam CT17 e CT28 — e o estado `expired` de um lembrete **nunca é atribuído por nenhum código**. Ver [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade#4-análise-de-cobertura). |
| **Requisitos de qualidade eram implícitos** ([#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43)) | Antes desta documentação, os requisitos não funcionais existiam espalhados pelo prompt master (seções 8, 11, 12 e 13) e pelo `core/config.py`, sem identificador. Sem ID não há priorização nem rastreabilidade — é a motivação do Handbook de Gerenciamento de Requisitos para o esquema de atributos (§3.1, p. 41). |

---

## 6. Por onde seguir

| Se você quer... | Vá para |
|---|---|
| Saber de onde vieram os requisitos | [Stakeholders e Fontes de Requisitos](Stakeholders-e-Fontes-de-Requisitos) |
| Ver o que o sistema faz | [Requisitos Funcionais](Requisitos-Funcionais) |
| Ver as exigências de qualidade | [Requisitos Não Funcionais](Requisitos-Nao-Funcionais) |
| Ver os requisitos na forma ágil | [Histórias de Usuário](Historias-de-Usuario) |
| Entender o sistema por modelos | [Modelagem de Requisitos](Modelagem-de-Requisitos) |
| Conferir requisito × código × teste | [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade) |
| Saber como mudanças são tratadas | [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos) |
| Saber o que vem primeiro | [Priorização e Backlog](Priorizacao-e-Backlog) |
| Saber como isso é conferido | [Validação e Verificação](Validacao-e-Verificacao) |

---

## Referências

Material de referência utilizado nesta seção da wiki. As páginas indicadas são as do próprio
documento (rodapé/cabeçalho), não as do leitor de PDF.

| Sigla usada | Documento |
|---|---|
| **Glossário** | *Glossary of Requirements Engineering Terminology* — IREB CPRE, versão 2.2 (`ireb_cpre_glossary_br_2.2.pdf`) |
| **Handbook de Elicitação** | *Requirements Elicitation — Handbook*, Practitioner/Specialist, IREB, v2.1.0 (`advanced_level_elicitation_handbook_br_v2.1.0.pdf`) |
| **Handbook de Gerenciamento de Requisitos** | *Requirements Management — Handbook*, IREB, v2.1.0 (`ireb-cpre-handbook-for-requirements-management-br-v2.1.0.pdf`) |
| **Syllabus de Modelagem** | *CPRE Advanced Level — Requirements Modeling, Syllabus*, IREB, v3.1.0 (`syllabus-cpre-al-requirements-modeling_br_v3.1.0.pdf`) |

> Estes quatro documentos são do **IREB (CPRE)**. Não há material do BSTQB entre as fontes
> consultadas, e nenhuma afirmação desta wiki é atribuída a ele.
