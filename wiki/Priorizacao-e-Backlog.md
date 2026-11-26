# Priorização e Backlog

O que fazer primeiro, por quê, e com qual critério explícito — em vez de "o que parecer mais
urgente".

> **Mudança nesta versão.** A coluna "Custo" era uma nota subjetiva de 1 a 9. Foi substituída por
> uma **estimativa de três pontos** em horas, com desvio declarado, seguindo o material do
> BSTQB® (§5, pp. 13–14). Isso mudou a ordem do backlog — a seção 6 mostra o que mudou e por quê.
>
> **Concluídos desde então**, conforme a regra 6 da seção 9 — os cinco primeiros colocados,
> que somavam 6,6 h estimadas:
> [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30) (segredos padrão),
> [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36) (CT28),
> [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37) (RN01/RN08/RN14) e
> [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38) (baseline 1.0.0) e
> [#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) (validação dos
> formulários ao vivo). Os totais abaixo refletem os **16 cards** restantes.

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

Priorizar exige comparar valor com **esforço**. Por isso esta página usa duas técnicas, e não
uma: uma para **estimar** o esforço (seção 2) e outra para **ordenar** os itens (seção 5).

---

## 2. A técnica de estimativa: três pontos

### Por que três pontos, e não as outras

O material do BSTQB® apresenta quatro abordagens (§1, p. 4). Nem todas servem aqui:

| Técnica do material | Aplicável aqui? | Motivo |
|---|---|---|
| Baseada em índices (§2, p. 5) | **Não** | Exige um índice histórico de produtividade que este projeto nunca mediu. |
| Extrapolação — média ou regressão linear (§3, p. 7) | **Não** | Extrapola a partir de séries anteriores. Não há séries: cada pendência é diferente das outras. |
| Wideband Delphi (§4, p. 10) | **Não** | Depende de rodadas de estimativa entre **vários especialistas**. Aqui há uma pessoa. |
| Planning Poker (§4.2, p. 12) | **Não** | Mesmo impedimento: pressupõe uma equipe estimando em conjunto. |
| **Três pontos (§5, p. 13)** | **Sim** | Funciona com um estimador, e **declara a incerteza** em vez de esconder. |

O próprio material diz onde essa técnica se encaixa:

> "A técnica de três pontos é especialmente útil quando a incerteza é alta e as estimativas
> baseadas em dados históricos ou em experiências anteriores não são suficientes para capturar a
> complexidade do projeto."
> — BSTQB®, *Técnicas de Estimativa* v1.1, §5, p. 14

Que é exatamente a situação deste backlog: incerteza alta, zero histórico.

### Os três pontos

Definições conforme o material (§5, p. 13):

| Ponto | Definição |
|---|---|
| **o** — melhor caso | "A estimativa mais otimista, em que se supõe que todas as condições favoráveis ocorrerão e tudo funcionará perfeitamente sem nenhum contratempo." |
| **m** — caso mais provável | "A estimativa baseada em uma avaliação realista das condições prováveis da atividade, considerando riscos moderados e suposições mais realistas." |
| **p** — pior caso | "A estimativa mais pessimista, levando em consideração possíveis problemas, atrasos e dificuldades que possam ocorrer durante a execução da atividade." |

### As fórmulas

```
        o + 4m + p                    p − o
E  =  ──────────────          SD  =  ───────
             6                           6
```

O resultado é expresso como **E ± SD** (§5, p. 14). A média é ponderada porque, nas palavras do
material, "atribui maior peso à estimativa mais provável, pois ela reflete a avaliação realista
dos especialistas" (§5, p. 13).

Unidade usada aqui: **horas** de trabalho de uma pessoa — o material chama de "homens/hora"
(§5, p. 14).

> **Transparência obrigatória.** Estes três pontos são **avaliação do mantenedor do projeto**,
> não medição. O material é explícito quanto a isso ser um requisito da técnica: "é essencial
> envolver especialistas e profissionais experientes na estimativa" (§1, p. 4) — aqui há um
> estimador só, que é também quem escreveu o código. As estimativas estão abertas item a item
> justamente para poderem ser contestadas.

---

## 3. As estimativas

| Item | Card | o | m | p | **E** | **SD** | Tam. |
|---|---|---|---|---|---|---|---|
| RN29 e RN31: documentar ou descartar | [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) | 1 | 2,5 | 8 | **3,17** | ±1,17 | S |
| Diretório `tests/accessibility/` vazio | [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41) | 1 | 3 | 8 | **3,50** | ±1,17 | S |
| Status `expired` nunca atribuído (CT17) | [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35) | 2 | 5 | 12 | **5,67** | ±1,67 | M |
| Envio real de e-mail na recuperação | [#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29) | 2 | 5 | 12 | **5,67** | ±1,67 | M |
| Docker: empacotar o portal | [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26) | 2 | 5 | 14 | **6,00** | ±2,00 | M |
| Relatório do estado dos requisitos | [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44) | 2 | 5 | 14 | **6,00** | ±2,00 | M |
| Conferir os 19 critérios de aceite | [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) | 3 | 6 | 14 | **6,83** | ±1,83 | M |
| RN17: expurgo automático | [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22) | 3 | 6 | 16 | **7,17** | ±2,17 | M |
| RN13: validação ativa de conteúdo | [#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) | 2 | 6 | 20 | **7,67** | ±3,00 | M |
| Quantificar os requisitos não funcionais | [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43) | 3 | 7 | 16 | **7,83** | ±2,17 | M |
| Testes de acessibilidade com axe-core | [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) | 3 | 8 | 20 | **9,17** | ±2,83 | M |
| Especificar os casos de uso em texto | [#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45) | 5 | 10 | 22 | **11,17** | ±2,83 | L |
| Agendador: evitar lembretes duplicados | [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33) | 4 | 10 | 28 | **12,00** | ±4,00 | L |
| Testes E2E do portal com Playwright | [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24) | 5 | 12 | 28 | **13,50** | ±3,83 | L |
| Exportação e exclusão de dados (LGPD) | [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42) | 5 | 12 | 30 | **13,83** | ±4,17 | L |
| **Elicitação com o público-alvo real** | [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) | 8 | 24 | 80 | **30,67** | ±12,00 | XL |

Conferência de uma linha, para o cálculo ser reproduzível à mão — [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23):

```
E  = (1 + 4×2,5 + 8) / 6 = 19 / 6 = 3,17 h
SD = (8 − 1) / 6         =  7 / 6 = 1,17 h      →  3,17 ± 1,17 h
```

**Tamanho** traduz E para o campo *Size* do quadro: XS < 2 h · S 2–5 h · M 5–10 h · L 10–20 h ·
XL > 20 h.

---

## 4. O total do backlog

Somando as 16 estimativas, e combinando os desvios pela raiz da soma dos quadrados:

```
E_total  = 149,8 h
SD_total = √(Σ SDᵢ²) = √246,2 = 15,7 h
```

| Faixa | Intervalo | Leitura |
|---|---|---|
| E ± 1·SD | **134 – 166 h** | cenário provável |
| E ± 2·SD | **118 – 181 h** | cenário conservador |

> Cinco cards concluídos tiraram 6,6 h do total e **não mexeram no desvio** (±15,7 h nas três
> versões desta página). Era previsível: eram os cinco itens de menor SD do backlog. Fechar
> tarefa previsível reduz trabalho, não incerteza.

> **Ressalva do método.** Somar desvios pela raiz da soma dos quadrados pressupõe que as
> atividades são **independentes**. Aqui elas não são totalmente: [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24)
> e [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) compartilham a montagem
> do ambiente de testes de navegador, e [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43)
> e [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44) dependem da mesma
> estrutura de requisitos. Então o SD real é **maior** que 15,7 h. O material não trata de
> agregação de desvios; a fórmula usada aqui é conhecimento geral de gerenciamento de projetos,
> não citação do BSTQB®.

### Onde está a incerteza

O desvio não está distribuído: **quatro itens concentram 78% de toda a variância** do backlog.

| Item | SD | Fatia da variância |
|---|---|---|
| [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) — elicitação com usuários | ±12,00 | **58,3%** |
| [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42) — LGPD | ±4,17 | 7,1% |
| [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33) — agendador | ±4,00 | 6,5% |
| [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24) — Playwright | ±3,83 | 6,0% |
| *12 itens restantes* | — | 22,0% |

**O que isso revela, e que a nota de custo 1–9 escondia:** a elicitação com usuários sozinha
responde por quase **três quintos** de toda a imprevisibilidade do projeto. Seu `p` é 80 h
contra `m` de 24 h, porque depende de recrutar pessoas, agendar sessões e lidar com ausências —
nada disso está sob controle de quem executa.

Tirando esse item, o backlog seria **119,2 ± 10,1 h**: a incerteza cai um terço.

**Consequência prática: [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40)
deve ser dividido.** O `p` alto é quase todo da **execução** (recrutar, conduzir, transcrever),
não do **planejamento** (hipóteses, roteiro, critérios de observação). Separar os dois tira o
item de maior variância do caminho crítico sem perder o item de maior valor:

| Fatia | o | m | p | E | SD |
|---|---|---|---|---|---|
| Planejar a elicitação (roteiro + hipóteses) | 2 | 4 | 8 | **4,33** | ±1,00 |
| Executar as sessões e analisar | 6 | 20 | 72 | **26,33** | ±11,00 |

Isso é uso da estimativa para **mudar o plano**, não apenas para descrevê-lo.

---

## 5. A técnica de priorização: matriz no estilo Wiegers

Estimar diz **quanto custa**; não diz **o que vem primeiro**. Para ordenar, o Handbook de
Gerenciamento de Requisitos separa técnicas ad-hoc (§4.5, p. 71) de analíticas (§4.6, p. 79), e
resume o trade-off: as ad-hoc "têm a vantagem de serem fáceis de usar e muito eficientes. No
entanto, seus resultados são subjetivos e, muitas vezes, impossíveis de rastrear em um momento
posterior" (§4.6, p. 79).

A escolha segue a mesma de antes — **matriz no estilo Wiegers** (§4.6.1, p. 80) combinada com a
leitura da **matriz de risco** (§4.5.6, Figura 5, p. 77). O handbook recomenda combinar técnicas
(§4.7, p. 83). O que mudou é o denominador.

| Critério | Escala | Origem |
|---|---|---|
| **Benefício** — valor de fazer | 1–9 | avaliação do mantenedor |
| **Dano** — prejuízo de não fazer | 1–9 | avaliação do mantenedor |
| **E** — esforço estimado | horas | **estimativa de três pontos** (seção 3) |

```
Pontuação = (2 × Benefício + Dano) ÷ E
```

A leitura é direta: **benefício por hora de trabalho**.

### Por que o risco saiu do denominador

A fórmula anterior era `(2B + D) ÷ (C + 0,5 × Risco)`. O risco técnico virava um acréscimo
artificial ao custo.

Com três pontos isso passou a ser **contagem dupla**: o risco de uma atividade já está dentro da
estimativa, no `p`. O material é explícito — o pior caso leva "em consideração possíveis
problemas, atrasos e dificuldades" (§5, p. 13), e a técnica inteira "é baseada na ideia de que as
estimativas são frequentemente afetadas por incertezas e riscos inerentes ao projeto" (§5, p. 13).

Então o risco agora aparece onde é mensurável: **no `p` e no `SD`**. O caso mais claro é
[#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) (validação ativa de
conteúdo), que tinha a maior nota de risco da lista: seu `m` é 6 h e seu `p` é 20 h — e o SD de
±3,00 h diz isso sem precisar de um fator inventado.

### A matriz

| Item | Card | Ben. | Dano | E (h) | Pontuação |
|---|---|---|---|---|---|
| RN29 e RN31: documentar ou descartar | [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23) | 5 | 4 | 3,17 | **4,4** |
| Status `expired` nunca atribuído | [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35) | 6 | 6 | 5,67 | **3,2** |
| Diretório `tests/accessibility/` vazio | [#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41) | 4 | 3 | 3,50 | **3,1** |
| RN17: expurgo automático | [#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22) | 6 | 7 | 7,17 | **2,7** |
| Conferir os 19 critérios de aceite | [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) | 6 | 6 | 6,83 | **2,6** |
| Docker: empacotar o portal | [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26) | 5 | 4 | 6,00 | **2,3** |
| Envio real de e-mail na recuperação | [#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29) | 4 | 5 | 5,67 | **2,3** |
| Testes de acessibilidade com axe-core | [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) | 7 | 6 | 9,17 | **2,2** |
| Relatório do estado dos requisitos | [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44) | 4 | 3 | 6,00 | **1,8** |
| Quantificar os requisitos não funcionais | [#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43) | 5 | 4 | 7,83 | **1,8** |
| RN13: validação ativa de conteúdo | [#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) | 4 | 5 | 7,67 | **1,7** |
| Exportação e exclusão de dados (LGPD) | [#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42) | 7 | 8 | 13,83 | **1,6** |
| Agendador: evitar lembretes duplicados | [#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33) | 5 | 8 | 12,00 | **1,5** |
| Testes E2E do portal com Playwright | [#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24) | 6 | 5 | 13,50 | **1,3** |
| Especificar os casos de uso em texto | [#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45) | 4 | 3 | 11,17 | **1,0** |
| **Elicitação com o público-alvo real** | [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) | 9 | 9 | 30,67 | **0,9** |

---

## 6. O que a estimativa mudou na ordem

Trocar a nota de custo 1–9 por horas estimadas **reordenou o backlog**. As mudanças que importam:

> As posições desta seção são as dos **21 cards** no momento da repriorização, antes de
> [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30) ser concluído. É o
> registro da comparação entre os dois métodos — recalculá-lo depois apagaria justamente o que
> ele documenta.

| Item | Antes | Agora | Por que mudou |
|---|---|---|---|
| [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36) Anotar CT28 | 6º | **2º** | É o item mais barato da lista: **38 minutos** estimados. A escala 1–9 não tinha como dizer "menos de uma hora" — o menor valor possível era 1, igualado a tarefas três vezes maiores. |
| [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) Conferir os 19 critérios | 4º | **10º** | Tinha custo 2; são **6,8 h** de conferência item a item. A nota subestimava o trabalho em cerca de três vezes. |
| [#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29) E-mail real | 20º | **12º** | Tinha custo 5 e risco 3, o que a jogava para o fim. Estimada de perto, são 5,7 h — integração conhecida, sem invenção. |
| [#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26) Docker do portal | 17º | **11º** | Mesma causa: 6 h de trabalho conhecido, penalizado antes por uma nota de risco alta. |
| [#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34) RN13 | 21º (último) | **16º** | O risco 6 no denominador o afundava. Agora o risco está no `p` (20 h) e no SD (±3 h), sem puni-lo duas vezes. |
| [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) axe-core | 10º | **13º** | 9,2 h, com `p` de 20 h: o custo de **corrigir** o que a ferramenta apontar é a parte incerta, e a nota 4 não a representava. |

O padrão: **a escala 1–9 comprimia os extremos.** Achatava tarefas de 40 minutos e de 3 horas no
mesmo "custo 1", e esticava o meio da tabela com notas de risco que agora estão onde devem estar.

### O que mudou no quadro do projeto

A ordem da pontuação mudou muito; o **quadro** mudou pouco. Cinco cards foram ajustados:

| Card | Campo | Antes | Agora | Motivo |
|---|---|---|---|---|
| [#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) | Priority | P1 | **P0** | 1,79 h estimadas — fecha uma lacuna de verificação por menos de 2 h. |
| [#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) | Size | S | **XS** | E < 2 h. |
| [#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35) | Size | S | **M** | 5,67 h. |
| [#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39) | Size | S | **M** | 6,83 h — era o subdimensionamento mais grave. |
| [#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44) | Size | S | **M** | 6,00 h. |
| [#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45) | Size | M | **L** | 11,17 h. |

**Uma só prioridade mudou, e quatro tamanhos estavam subestimados.** Vale dizer o que isso
significa: a priorização qualitativa anterior estava, no geral, correta — porque as correções pela
matriz de risco já faziam o trabalho que a pontuação sozinha errava. O que a estimativa de três
pontos corrigiu de fato foi o **dimensionamento**: quatro cards marcados como "S" eram de
5 a 7 horas, e um "M" era de 11.

Distribuição no momento da repriorização: **P0 = 9 cards · P1 = 5 · P2 = 7.** Com
[#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30),
[#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36),
[#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37) e
[#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38) e
[#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) concluídos, o quadro está
hoje em **P0 = 4 · P1 = 5 · P2 = 7**.

---

## 7. O que a pontuação continua errando

Duas distorções permanecem, e a seção existe para não fingir o contrário.

**Primeira: benefício por hora favorece o barato.** Na primeira rodada desta matriz, as quatro
primeiras posições somavam **4,8 h** e três delas eram dívidas de documentação — boas de fazer,
mas ninguém diria que eram as mais importantes do projeto.

E foi exatamente o que aconteceu: **os cinco primeiros colocados foram os cinco primeiros a
sair.** A distorção não é teórica, ela dirige a execução. Hoje as quatro primeiras posições
somam **18,0 h**, porque o barato acabou — **não há mais nenhum item abaixo de 2 h**. A fila
agora é de trabalho de verdade, e a pontuação deixa de dar atalhos.

**Segunda: ela afunda o item mais importante.** A elicitação com o público-alvo real tem
benefício 9 e dano 9 e cai para **último** lugar, agora por um motivo mais honesto do que antes:
30,7 h estimadas. Pela matriz de risco (§4.5.6, Figura 5, p. 77) — "risco possível e grave →
contramedidas devem ser tomadas a todo custo" — ela está na faixa vermelha: um sistema de
acessibilidade **nunca testado com pessoas não alfabetizadas, idosas ou com baixa visão** pode
falhar exatamente com quem deveria atender, e esse é o propósito declarado do produto.

**Correção aplicada:** itens de risco clínico, de segurança ou de propósito do produto são
promovidos acima da ordem numérica. A pontuação organiza; ela não decide.

Agora há uma correção a mais, que só a estimativa de três pontos permite: **itens de SD alto
entram divididos**, quando a divisão separa uma fatia previsível de uma imprevisível — como em
[#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) (seção 4).

---

## 8. O backlog priorizado

> **Nomenclatura.** Os níveis são os do campo **Priority** do
> [quadro do projeto](https://github.com/users/marluceqa-source/projects/9): `P0`, `P1`, `P2`. O
> campo **Size** traduz E pela faixa da seção 3. Usar a mesma escala nos dois lugares evita o
> tipo de homônimo registrado no [Glossário](Glossario#1-homônimos--leia-esta-seção-primeiro).

### P0 — fazer primeiro · **E ≈ 20,0 h** (±2,9 h) · 4 cards

| # | Item | Justificativa da posição |
|---|---|---|
| 1 | **RN29 e RN31** ([#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23)) · 3,17 h | Duas regras sem origem localizável: ou existem e faltam, ou não existem e poluem a numeração. |
| 2 | **Planejar a elicitação** ([#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40), fatia de planejamento) · 4,33 h | Promovido pela matriz de risco, e **dividido** pela análise de variância: entra o roteiro, não a execução. |
| 3 | **Corrigir o status `expired`** ([#35](https://github.com/marluceqa-source/hora-do-remedio/issues/35)) · 5,67 h | O sistema **declara** um estado que nunca atribui — relatórios tratam `expired`, o bot tem rótulo, nada o produz. Único caso de comportamento documentado e inexistente, e o último CT sem rastreabilidade. |
| 4 | **Conferir os 19 critérios de aceite** ([#39](https://github.com/marluceqa-source/hora-do-remedio/issues/39)) · 6,83 h | **Mantido no P0 contra a pontuação** (é o 5º colocado). É o critério de parada do escopo original: sem essa conferência, não há como afirmar que o projeto está pronto. |

> **Não há mais item abaixo de 2 h no backlog.** O mais barato agora é
> [#23](https://github.com/marluceqa-source/hora-do-remedio/issues/23), com 3,17 h.

> ✅ **Concluídos** — os cinco primeiros colocados da matriz, 6,6 h estimadas:
>
> | Card | O que ficou pronto |
> |---|---|
> | [#30](https://github.com/marluceqa-source/hora-do-remedio/issues/30) | A aplicação recusa iniciar com segredo de exemplo fora de desenvolvimento; segredos locais regerados. |
> | [#36](https://github.com/marluceqa-source/hora-do-remedio/issues/36) | CT28 anotado: 41 dos 42 cenários agora são rastreáveis por busca. |
> | [#37](https://github.com/marluceqa-source/hora-do-remedio/issues/37) | RN01, RN08 e RN14 marcadas no código: 29 das 32 regras. |
> | [#38](https://github.com/marluceqa-source/hora-do-remedio/issues/38) | Baseline **1.0.0** (tag `v1.0.0`) declarada na [Home](Home#baseline-da-especificação). |
> | [#32](https://github.com/marluceqa-source/hora-do-remedio/issues/32) | Formulários de paciente e de medicamento verificados ao vivo, campo a campo, em português. |

### P1 — próxima rodada · **E ≈ 45,7 h** (±6,9 h)

| # | Item | Justificativa |
|---|---|---|
| 8 | Testes de acessibilidade com axe-core ([#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25)) · 9,17 h | Acessibilidade é o propósito do produto e hoje nenhuma verificação automática a cobre. |
| 9 | RN17 — expurgo automático ([#22](https://github.com/marluceqa-source/hora-do-remedio/issues/22)) · 7,17 h | Regra declarada e não vigente, com implicação legal. |
| 10 | Diretório `tests/accessibility/` vazio ([#41](https://github.com/marluceqa-source/hora-do-remedio/issues/41)) · 3,50 h | Estrutura prometida no prompt master (§11) e nunca preenchida. |
| 11 | Agendador: lembretes duplicados ([#33](https://github.com/marluceqa-source/hora-do-remedio/issues/33)) · 12,00 h | Dano 8: duplicar lembrete de remédio é dano ao paciente. SD ±4 h — terceira maior incerteza. |
| 12 | Exportação e exclusão de dados (LGPD) ([#42](https://github.com/marluceqa-source/hora-do-remedio/issues/42)) · 13,83 h | RES06/LGPD está apenas declarada; não há rota alguma. SD ±4,2 h, a segunda maior. |

### P2 — quando houver folga · **E ≈ 84,2 h** (±13,0 h)

| Item | Justificativa |
|---|---|
| Executar a elicitação ([#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40), fatia de execução) · 26,33 h | Maior valor do backlog, maior incerteza (±11 h) e dependente de pessoas. Fica aqui por **capacidade**, não por importância — o plano (P0 item 5) é o que o destrava. |
| Testes E2E do portal ([#24](https://github.com/marluceqa-source/hora-do-remedio/issues/24)) · 13,50 h | A suíte de backend já cobre as regras. Compartilha montagem com [#25](https://github.com/marluceqa-source/hora-do-remedio/issues/25) — fazer depois reduz o custo real. |
| Especificar os casos de uso em texto ([#45](https://github.com/marluceqa-source/hora-do-remedio/issues/45)) · 11,17 h | Completa a modelagem; conteúdo já existe disperso. |
| Quantificar os RNF ([#43](https://github.com/marluceqa-source/hora-do-remedio/issues/43)) · 7,83 h | Melhora a especificação; nenhum risco imediato. |
| RN13 — validação ativa de conteúdo ([#34](https://github.com/marluceqa-source/hora-do-remedio/issues/34)) · 7,67 h | `p` de 20 h contra `m` de 6 h: um filtro mal calibrado bloquearia observações legítimas do paciente. Exige desenho cuidadoso, não pressa. |
| Docker para o portal ([#26](https://github.com/marluceqa-source/hora-do-remedio/issues/26)) · 6,00 h | Empacotamento, não funcionalidade. |
| Relatório do estado dos requisitos ([#44](https://github.com/marluceqa-source/hora-do-remedio/issues/44)) · 6,00 h | Automatiza o que hoje é contado à mão. |
| E-mail real na recuperação ([#29](https://github.com/marluceqa-source/hora-do-remedio/issues/29)) · 5,67 h | Contornável pelo administrador hoje. |

### Resumo

| Faixa | Itens | E | SD | Intervalo provável |
|---|---|---|---|---|
| **P0** | 4 | 20,0 h | ±2,9 h | 17 – 23 h |
| **P1** | 5 | 45,7 h | ±6,9 h | 39 – 53 h |
| **P2** | 8 | 84,2 h | ±13,0 h | 71 – 97 h |
| **Total** | 17 | **149,8 h** | **±15,0 h** | **135 – 165 h** |

> O total do plano tem **17 itens**, e não 16, porque
> [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40) entra dividido. E o SD cai
> de ±15,7 h (seção 4) para **±15,0 h** sem que nenhuma estimativa mude: dividir uma atividade de
> faixa muito larga em duas mais estreitas reduz a soma dos quadrados. Não é truque de
> contabilidade — é o efeito real de tirar a parte imprevisível do caminho crítico.

---

## 9. Como manter esta página viva

1. Todo card novo recebe **três pontos** (`o`, `m`, `p`) e as duas notas (benefício, dano) na
   descrição.
2. `E` e `SD` são calculados pelas fórmulas da seção 2 — nunca estimados "de cabeça" como valor
   único.
3. A pontuação é recalculada quando algo entra ou sai.
4. Mudança de ordem contra a pontuação precisa de **uma frase de justificativa** — como nos
   itens 5 e 7 do P0.
5. Quando o `SD` de um item passa de **um terço do seu `E`**, considere **dividi-lo**: costuma
   haver dentro dele uma fatia previsível presa a uma imprevisível (seção 4).
6. Item concluído sai da matriz e vira label `concluído`. Se o tempo real for registrado, ele
   alimenta a comparação com `E` — é assim que se constrói o histórico que hoje não existe e que
   permitiria, no futuro, usar as técnicas de **índice** ou **extrapolação** (§2 e §3 do material).
7. A prioridade e o tamanho vão também para os campos **Priority** e **Size** do
   [quadro do projeto](https://github.com/users/marluceqa-source/projects/9) — o quadro mostra a
   ordem, esta página explica o porquê dela.

> **Critério de parada:** a definição de "pronto" para o escopo original são os **19 critérios de
> aceite** da seção 15 do prompt master. Eles **não têm registro de conferência item a item** em
> nenhum lugar do repositório — o que não significa que não foram atendidos, significa que isso
> não está documentado. Fechar essa conferência é o item 7 do P0; os demais itens desta página são
> **evolução**, não conclusão pendente.

---

## Referências

- **BSTQB®**, *Material de Apoio — Técnicas de Estimativa*, v1.1, 28/06/2024. §1 (p. 4), §2
  (p. 5), §3 (p. 7), §4 (p. 10), §4.2 (p. 12), **§5 (pp. 13–14)**. Brazilian Software Testing
  Qualifications Board.
- **IREB CPRE**, *Handbook for Requirements Management*, v2.1.0. §4.1 (p. 65), §4.5 (p. 71),
  §4.5.6 (p. 75), Figura 5 (p. 77), §4.6 (p. 79), §4.6.1 (p. 80), §4.7 (p. 83).
- **IREB CPRE**, *Glossary of Requirements Engineering Terminology*, v2.2. Verbetes *Priorização*
  (p. 24) e *Backlog do produto* (p. 2).

A fórmula de agregação de desvios (√Σ SDᵢ²) é conhecimento geral de gerenciamento de projetos e
**não** consta do material do BSTQB®.

---

## Próximo

- [Gerenciamento de Requisitos](Gerenciamento-de-Requisitos)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
- [Validação e Verificação](Validacao-e-Verificacao)
