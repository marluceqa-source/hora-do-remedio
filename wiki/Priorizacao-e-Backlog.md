# Priorização e Backlog

O que fazer primeiro, por quê, e com qual critério explícito — em vez de "o que parecer mais
urgente".

---

## 1. Os conceitos

> **Priorização:** "O processo de atribuir prioridades a um conjunto de itens."
> — Glossário, verbete *Priorização*, p. 24

> **Backlog do produto:** "Uma coleção ordenada, tipicamente priorizada, de itens de trabalho em
> que uma equipe de desenvolvimento tem de trabalhar ao desenvolver ou evoluir um sistema.
> Nota: itens incluem requisitos, defeitos a serem corrigidos ou refatorações a serem feitas."
> — Glossário, verbete *Backlog do produto*, p. 2

O backlog deste projeto são as **issues do repositório**. Esta página é a visualização
priorizada delas.

---

## 2. Qual técnica foi escolhida, e por quê

O Handbook de Gerenciamento de Requisitos separa **técnicas ad-hoc** (§4.5, p. 71) de
**técnicas analíticas** (§4.6, p. 79), e resume o trade-off: as ad-hoc "têm a vantagem de serem
fáceis de usar e muito eficientes. No entanto, seus resultados são subjetivos e, muitas vezes,
impossíveis de rastrear em um momento posterior. Eles não são ideais para decisões críticas ou
em um ambiente de segurança crítica" (§4.6, p. 79).

| Técnica do handbook | Aplicável aqui? | Motivo |
|---|---|---|
| Triagem de requisitos (§4.5.1, p. 71) | Sim, já feita | É o que a label `pendência` × `concluído` faz. |
| Ranking (§4.5.2) e Top-Ten (§4.5.3) | Parcialmente | Ordenam, mas não registram **por que** — perde-se o critério. |
| Classificação de critério único (§4.5.4) | Não | Um critério só não distingue "barato e útil" de "caro e indispensável". |
| Planning Poker (§4.5.5, p. 74) | **Não** | Pressupõe uma equipe estimando em conjunto. Aqui há uma pessoa. |
| **Classificação de dois critérios** (§4.5.6, p. 75) | **Sim** | Benefício × custo e a **matriz de risco** (Figura 5, p. 77). |
| Técnica dos 100 dólares (§4.5.7, p. 77) | **Não** | Projetada para vários stakeholders distribuindo pontos. |
| Classificação de Kano (§4.5.8, p. 78) | **Não** | Exige perguntar a usuários o grau de satisfação e insatisfação — e [nenhum usuário foi consultado](Stakeholders-e-Fontes-de-Requisitos#4-técnicas-de-elicitação-aplicadas). |
| **Matriz de Wiegers** (§4.6.1, p. 80) | **Sim, adaptada** | Usa mais de dois critérios: benefício, desvantagem de não fazer, custo e risco. |
| AHP (§4.6.2, p. 85) | Não | Comparação par a par; esforço desproporcional para ~19 itens. |

**Decisão:** uma **matriz no estilo Wiegers** com escala 1–9, combinada com a leitura da **matriz
de risco** para itens clínicos e de segurança. O handbook recomenda explicitamente combinar
técnicas (§4.7, p. 83).

> **Transparência obrigatória.** As notas abaixo são **avaliação do mantenedor do projeto**, não
> medição. O handbook aponta que mesmo as técnicas analíticas só tornam a priorização "mais
> neutra e mais rastreável" (§4.6, p. 79) — não objetiva. Elas estão aqui para poderem ser
> contestadas item por item.

### Como o número é calculado

| Critério | Escala | Peso |
|---|---|---|
| **Benefício** — valor de fazer | 1–9 | 2 |
| **Dano** — prejuízo de não fazer | 1–9 | 1 |
| **Custo** — esforço de implementar | 1–9 | 1 |
| **Risco** — risco técnico de fazer | 1–9 | 0,5 |

`Pontuação = (2 × Benefício + Dano) ÷ (Custo + 0,5 × Risco)`

Diferença em relação ao handbook: a etapa 7 de Wiegers normaliza cada coluna em percentual
(p. 80). Aqui usamos os valores brutos — mais simples de reproduzir à mão, e suficiente para
ordenar.

---

## 3. A matriz

| Item | Card | Ben. | Dano | Custo | Risco | Pontuação |
|---|---|---|---|---|---|---|
| Trocar os segredos padrão | [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30) | 7 | 9 | 1 | 1 | **15,3** |
| Criar a primeira baseline da especificação | [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38) | 5 | 4 | 1 | 1 | **9,3** |
| Marcar RN01, RN08 e RN14 no código | [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37) | 4 | 3 | 1 | 1 | **7,3** |
| Conferir os 19 critérios de aceite do prompt master | [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) | 6 | 6 | 2 | 1 | **7,2** |
| RN29 e RN31: documentar ou descartar | [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) | 5 | 4 | 2 | 1 | **5,6** |
| Anotar CT28 nos testes de cuidador | [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36) | 3 | 2 | 1 | 1 | **5,3** |
| Validar ao vivo os dois formulários | [#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) | 4 | 4 | 2 | 1 | **4,8** |
| Status `expired` nunca atribuído (CT17) | [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35) | 6 | 6 | 3 | 2 | **4,5** |
| Diretório `tests/accessibility/` vazio | [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41) | 4 | 3 | 2 | 1 | **4,4** |
| Testes de acessibilidade com axe-core | [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) | 7 | 6 | 4 | 2 | **4,0** |
| RN17: expurgo automático | [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22) | 6 | 7 | 4 | 3 | **3,5** |
| Exportação e exclusão de dados (LGPD) | [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42) | 7 | 8 | 6 | 3 | **2,9** |
| Quantificar os requisitos não funcionais | [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43) | 5 | 4 | 4 | 2 | **2,8** |
| Relatório do estado dos requisitos | [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44) | 4 | 3 | 3 | 2 | **2,8** |
| **Elicitação com o público-alvo real** | [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) | 9 | 9 | 8 | 4 | **2,7** |
| Especificar os casos de uso em texto | [#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45) | 4 | 3 | 4 | 1 | **2,4** |
| Docker: empacotar o portal | [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26) | 5 | 4 | 5 | 3 | **2,2** |
| Agendador: evitar lembretes duplicados | [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33) | 5 | 8 | 6 | 5 | **2,1** |
| Testes E2E do portal com Playwright | [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24) | 6 | 5 | 7 | 3 | **2,0** |
| Envio real de e-mail na recuperação | [#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29) | 4 | 5 | 5 | 3 | **2,0** |
| RN13: validação ativa de conteúdo | [#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) | 4 | 5 | 5 | 6 | **1,6** |

---

## 4. O que a pontuação erra — e a correção pela matriz de risco

O handbook abre o capítulo de priorização justamente pelas **dificuldades** da priorização
(§4.1, p. 65). Duas aparecem aqui com clareza:

**Primeira: a razão benefício/custo favorece o barato.** As três primeiras posições são dívidas
de documentação de custo 1. São boas de fazer — mas ninguém diria que são as mais importantes
do projeto.

**Segunda: ela empurra para baixo o item mais importante.** A **elicitação com o público-alvo
real** tem benefício 9 e dano 9, e cai para o meio da tabela só por causa do custo 8. Pela matriz de
risco (§4.5.6, Figura 5, p. 77) — "risco possível e grave → contramedidas devem ser tomadas a
todo custo" — ela está na faixa vermelha: um sistema de acessibilidade **nunca testado com
pessoas não alfabetizadas, idosas ou com baixa visão** pode falhar exatamente com quem deveria
atender, e esse é o propósito declarado do produto.

**Correção aplicada:** os itens de risco clínico, de segurança ou de propósito do produto são
promovidos acima da ordem numérica. A pontuação organiza; ela não decide.

---

## 5. O backlog priorizado

> **Nomenclatura.** Os níveis abaixo são os mesmos do campo **Priority** do
> [quadro do projeto](https://github.com/users/marluceqa-source/projects/9): `P0` (fazer primeiro),
> `P1` e `P2`. O campo **Size** do quadro traduz a coluna "Custo" desta matriz — XS para custo 1–2,
> S para 2–3, M para 4–5, L para 6–7 e XL para 8–9. Usar a mesma escala nos dois lugares evita o
> tipo de homônimo registrado no [Glossário](Glossario#1-homônimos--leia-esta-seção-primeiro).

### P0 — fazer primeiro

| # | Item | Justificativa da posição |
|---|---|---|
| 1 | **Trocar os segredos padrão** ([#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30)) | Maior pontuação e risco de segurança real. Custo 1. |
| 2 | **Corrigir o status `expired`** ([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35)) | O sistema **declara** um estado que nunca atribui — relatórios tratam `expired`, o bot tem rótulo, nada o produz. É o único caso de comportamento documentado e inexistente. |
| 3 | **Planejar a elicitação com o público-alvo** ([#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40)) | Promovido pela matriz de risco. "Planejar" porque executar depende de pessoas e tempo; o que entra no P0 é o **plano** e o roteiro de observação. |
| 4 | **Dívidas de rastreabilidade** ([#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38), [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37), [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36)) | Custo 1 cada, e são o que mantém esta wiki confiável. |
| 5 | **Conferir os critérios de aceite do prompt master** ([#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39)) | São 19 critérios na seção 15 do prompt master e **nenhum deles tem registro de conferência item a item** — nem no README, nem na wiki. Custo 2. |
| 6 | **RN29 e RN31** ([#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)) | Duas regras sem origem localizável: ou existem e faltam, ou não existem e poluem a numeração. |

### P1 — próxima rodada

| # | Item | Justificativa |
|---|---|---|
| 7 | Testes de acessibilidade com axe-core ([#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25)) | Acessibilidade é o propósito do produto e hoje nenhuma verificação automática a cobre. |
| 8 | RN17 — expurgo automático ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)) | Regra declarada e não vigente, com implicação legal. |
| 9 | Exportação e exclusão de dados do titular ([#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42)) | RES06/LGPD está apenas declarada; não há rota alguma. |
| 10 | Agendador: lembretes duplicados ([#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33)) | Dano 8: duplicar lembrete de remédio é dano ao paciente. Custo e risco altos, por isso não é P0. |
| 11 | Diretório `tests/accessibility/` vazio ([#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41)) | Estrutura prometida no prompt master (§11) e nunca preenchida. Custo 2. |
| 12 | Validar os formulários ao vivo ([#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32)) | Custo baixo; fecha uma lacuna conhecida de verificação. |

### P2 — quando houver folga

| Item | Justificativa |
|---|---|
| Quantificar os RNF ([#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43)) | Melhora a especificação; nenhum risco imediato. |
| Especificar os casos de uso em texto ([#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45)) | Completa a modelagem; conteúdo já existe disperso. |
| Relatório do estado dos requisitos ([#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44)) | Automatiza o que hoje é contado à mão. |
| Testes E2E do portal ([#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24)) | Custo 7; a suíte de backend já cobre as regras. |
| Docker para o portal ([#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26)) | Empacotamento, não funcionalidade. |
| E-mail real na recuperação ([#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29)) | Contornável pelo administrador hoje. |
| RN13 — validação ativa de conteúdo ([#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34)) | **Risco 6, o maior da lista.** Um filtro de conteúdo mal calibrado bloquearia observações legítimas do paciente. Exige desenho cuidadoso, não pressa. |

---

## 6. Como manter esta página viva

1. Todo card novo recebe as quatro notas (benefício, dano, custo, risco) na descrição.
2. A pontuação é recalculada quando algo entra ou sai.
3. Mudança de ordem contra a pontuação precisa de **uma frase de justificativa** — como nos
   itens 2 e 3 do P0.
4. Item concluído sai da matriz e vira label `concluído`.
5. A prioridade e o tamanho vão também para os campos **Priority** e **Size** do
   [quadro do projeto](https://github.com/users/marluceqa-source/projects/9) — o quadro mostra a
   ordem, esta página explica o porquê dela.

> **Critério de parada:** a definição de "pronto" para o escopo original são os **19 critérios de
> aceite** da seção 15 do prompt master. Eles **não têm registro de conferência item a item** em
> nenhum lugar do repositório — o que não significa que não foram atendidos, significa que isso
> não está documentado. Fechar essa conferência é o item 5 do P0; os demais itens desta página são
> **evolução**, não conclusão pendente.

---

## Próximo

- [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
- [Validação e Verificação](Validacao-e-Verificacao)
