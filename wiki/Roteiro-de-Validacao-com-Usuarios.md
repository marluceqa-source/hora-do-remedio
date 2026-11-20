# Roteiro de Validação com Usuários

Plano de elicitação direta para fechar a maior lacuna do projeto: as decisões de acessibilidade
nunca foram confrontadas com as pessoas que elas deveriam atender. Card:
[#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40).

> ⚠️ **Este é um plano, não um resultado.** Nada nesta página valida nada ainda. Enquanto as
> sessões não acontecerem, as decisões de [Acessibilidade](Acessibilidade) continuam sendo
> hipóteses — e é assim que a wiki deve descrevê-las.

---

## 1. Objetivo da elicitação

O Handbook de Elicitação insiste nesse ponto antes de qualquer sessão: "o objetivo da elicitação
é o seu farol: ele o ajuda a navegar pela observação e a decidir se algo é relevante ou não"
(§3.1.2.1, p. 80). Sem ele, a observação vira turismo.

> **Objetivo:** descobrir se uma pessoa idosa, não alfabetizada ou com baixa visão consegue, **sem
> ajuda e sem ler**, entender o lembrete, identificar o medicamento certo e confirmar a dose — e
> onde exatamente ela trava quando não consegue.

Tudo o que não serve a esse objetivo é secundário nestas sessões.

---

## 2. As hipóteses sob teste

Cada hipótese é uma afirmação que hoje está na documentação **sem evidência**. A sessão existe
para confirmá-la, refutá-la ou mostrar que a pergunta estava errada.

| ID | Hipótese hoje documentada | Requisito | Como se refuta |
|---|---|---|---|
| **H1** | A pessoa reconhece o próprio remédio pela **fotografia** cadastrada. | RNF04, RF11 regra 7 | Ela confunde dois remédios, ou ignora a foto e procura o nome. |
| **H2** | A pessoa consegue confirmar a dose **só com botões**, sem ler. | RNF01, HU05, CT23 | Ela não sabe qual botão tocar, ou toca em qualquer um para a mensagem sair da tela. |
| **H3** | Os ícones 💊 📷 🔊 🎤 ✅ ❌ ⏰ são compreendidos **sem texto**. | RF11 | Ela atribui a eles um significado diferente do previsto. |
| **H4** | O áudio em pt-BR é **inteligível e suficiente** para agir. | RNF03, RF06 | Ela não entende a voz sintética, ou entende e ainda assim não sabe o que fazer. |
| **H5** | Cadastrar **falando** é mais fácil do que digitar. | RF04, RN11 | Ela não sabe gravar áudio no Telegram, ou a transcrição erra sempre e ela desiste. |
| **H6** | A confirmação obrigatória do **OCR** protege sem atrapalhar. | RN10 | Ela confirma qualquer coisa sem conferir — o que torna a proteção decorativa. |
| **H7** | O cuidador entende que o relatório mede **adesão declarada**, não adesão real. | RN12, [CF02](Stakeholders-e-Fontes-de-Requisitos#4-conflitos-entre-requisitos) | Ele lê "sem confirmação" como "não tomou" e cobra o paciente por isso. |
| **H8** | Restringir a **ativação ao médico** corresponde à prática clínica real. | RN20 | Na prática, quem ajusta o esquema é o enfermeiro, e a regra inviabiliza o uso. |

> **H7 e H8 são as hipóteses de maior consequência.** Se H7 cair, o sistema produz exatamente o
> julgamento que a RN12 existe para evitar. Se H8 cair, a regra mais restritiva do portal está
> errada.

---

## 3. Participantes

| Grupo | Quantidade | Critério | Técnica |
|---|---|---|---|
| **Pacientes do perfil-alvo** | 3 a 5 | Pelo menos uma pessoa não alfabetizada e uma com baixa visão; todas em uso contínuo de medicamento | Investigação contextual + observação de campo |
| **Cuidadores** | 2 a 3 | Cuidam de alguém que toma medicamento todos os dias | Entrevista semiestruturada |
| **Médicos** | 2 | Prescrevem para pacientes idosos | Entrevista semiestruturada |
| **Enfermeiro** | 1 | Ajusta esquema terapêutico na prática | Entrevista semiestruturada |

**Por que esse tamanho.** O handbook não define amostra mínima; o critério aqui é prático: o
objetivo é **encontrar barreiras**, não medir frequência. Três a cinco sessões bastam para revelar
os pontos de parada grosseiros — e são o que cabe no esforço estimado do card (Size XL).

**Especialista do domínio antes de tudo.** O handbook alerta para o **viés de simplificação**:
"observadores inexperientes têm a tendência de simplificar demais as estratégias de solução de
problemas do usuário especialista enquanto o observam", e recomenda "adquirir conhecimento sobre
o tópico (p. ex., conversar com um especialista no assunto) antes de usar técnicas de observação"
(§3.1.2, p. 79). Então a **primeira** conversa é com um profissional que atende esse público —
não com o paciente.

---

## 4. Técnica por grupo, e por que cada uma

O handbook diferencia três técnicas de observação e pede transição consciente entre elas — "o que
deve ser evitado é passar de uma técnica para outra" sem perceber (§3.1.2, p. 79).

| Técnica | Definição no handbook | Uso aqui |
|---|---|---|
| **Investigação contextual** (§3.1.2.3, p. 86) | Sessão de 60 a 90 min; o Engenheiro de Requisitos observa **e conversa**; quatro princípios: contexto, parceria, interpretação, foco. | **Técnica principal com pacientes.** A conversa é necessária: sem ela não se descobre *por que* a pessoa travou. |
| **Observação de campo** (§3.1.2.1, p. 79) | Observação **sem interação**, usada quando a interação distorceria o processo. | Apenas no **momento do lembrete real**: ali qualquer pergunta contamina a reação. Observar, anotar, perguntar depois. |
| **Aprendizado** (§3.1.2.2, p. 83) | Mestre e aprendiz; 1 a 3 dias; o Engenheiro de Requisitos **executa** a tarefa. | **Opcional**, com um enfermeiro, para entender o ajuste de esquema terapêutico (H8). Custo alto; só se H8 ficar inconclusiva. |
| **Entrevista semiestruturada** (§3.1.1, p. 68; variantes, p. 74) | Roteiro com perguntas abertas e espaço para seguir o que aparecer. | Cuidadores e profissionais, para H7 e H8. |
| **Protótipo** (§3.2.3, p. 111) | Artefato para provocar reação concreta. | Teste de compreensão dos ícones (H3), antes de tocar no bot. |

---

## 5. Sessão com paciente — roteiro

Duração: 60 a 90 minutos, no ambiente da pessoa, no horário real de uma dose quando possível.

### Antes (preparação)

- [ ] Conversa prévia com profissional do domínio (viés de simplificação)
- [ ] Consentimento combinado e explicado **oralmente**, não por formulário escrito
- [ ] Definido quem observa e quem conduz — o handbook sugere observadores com focos distintos: produtos de trabalho, contexto físico, comunicação, processo (§3.1.2.3, p. 86)
- [ ] Celular da pessoa, com o Telegram que **ela** usa — nunca um aparelho nosso
- [ ] Lista de verificação de anotações impressa
- [ ] Combinado se haverá foto/áudio/vídeo, e com qual autorização

### Parte 1 — Contexto, sem o sistema (15 min)

Perguntas abertas, sem mencionar o bot:

- "Me conta como foi a última vez que você tomou seu remédio hoje."
- "Como você sabe que está na hora?"
- "Como você sabe qual é o remédio certo?"
- "Já aconteceu de esquecer? O que você fez?"
- "Tem alguém que te ajuda com isso?"

> **Não corrija, não ensine, não sugira.** Esta parte existe para registrar a prática real, que é
> o padrão de comparação de tudo que vem depois.

### Parte 2 — Compreensão dos ícones, no papel (10 min)

Mostre os símbolos **impressos, fora de qualquer tela**, um por vez: 💊 📷 🔊 🎤 ✅ ❌ ⏰ 🌞 ☀️ 🌙 🏠

Para cada um: *"O que você acha que isso quer dizer?"*

Registre a **palavra que a pessoa usou**, não se "acertou". Hipótese H3 cai se o significado
atribuído for diferente do previsto — e a palavra dela é candidata a entrar no
[Glossário](Glossario) e nos rótulos do bot.

### Parte 3 — Lembrete real (observação de campo, sem interação)

Quando o lembrete chegar: **só observe**. Cronômetro, anotação, silêncio.

| O que medir | Por quê |
|---|---|
| Tempo entre o aviso e a primeira ação | H2, H4 |
| Ela ouviu o áudio ou foi direto aos botões? | H4 |
| Ela olhou a foto? Comparou com a cartela? | H1 |
| Qual botão tocou primeiro, e hesitou? | H2 |
| Pediu ajuda a alguém? | H2, RF12 |
| Tocou em algo errado e o que fez depois | H2 |

Só depois da ação, volte à conversa: *"O que você entendeu dessa mensagem?"*

### Parte 4 — Cadastro de um remédio (investigação contextual, 25 min)

Peça que ela cadastre um remédio que já toma, **do jeito que preferir**. Ofereça as três entradas
na ordem que ela escolher — foto, voz, digitação — e registre a escolhida primeiro (H5).

Durante: pergunte *"o que você está tentando fazer agora?"* nos momentos de pausa. Esse é o
princípio de **interpretação** da investigação contextual: construir entendimento junto, em vez de
adivinhar depois.

Pontos de atenção:

- Na foto: ela confere o texto do OCR ou confirma no automático? (H6)
- Na voz: ela sabe gravar áudio no Telegram? (H5)
- Em qualquer campo: onde **precisou** ler ou escrever? Esses são os limites reais da RNF01.

### Parte 5 — Fechamento (10 min)

- "O que foi mais difícil?"
- "Você usaria isso amanhã? Por quê?"
- "O que falta aqui para te ajudar de verdade?"

---

## 6. O que registrar

Lista de verificação derivada do handbook (§3.1.2.1, p. 81, apoiada em [BaCC2015]):

- [ ] **Que linguagem e terminologia** a pessoa usa — as palavras dela, literais
- [ ] **Quanto do sistema** ela realmente usa
- [ ] **Barreiras e pontos de parada** que ela encontra
- [ ] **Quanto tempo** dedica a cada tarefa
- [ ] **Que perguntas** ela precisa fazer para concluir a tarefa
- [ ] **Com quais ferramentas** interage (cartela, caixinha de comprimidos, papel na parede, alarme do celular)

E, por sessão: o veredito de cada hipótese — **confirmada**, **refutada** ou **inconclusiva**.

---

## 7. Ética e dados

> **Complemento baseado em conhecimento externo aos arquivos fornecidos:** os cuidados abaixo não
> vêm dos documentos do IREB; são decisão deste projeto, coerentes com a LGPD e com o fato de o
> estudo tocar dados de saúde.

| Regra | Motivo |
|---|---|
| **Nunca interferir na medicação real.** Se a sessão atrasar ou confundir uma dose, a sessão para. | A pesquisa não pode causar dano clínico. Esta regra vem antes de qualquer dado. |
| Consentimento **oral e explicado**, com direito de parar a qualquer momento | Formulário escrito é inacessível a quem não lê — pedir assinatura seria contraditório com o projeto |
| Nome real do medicamento **não** vai para o relato | Dado de saúde; use "medicamento A" nas notas |
| Foto, áudio e vídeo só com autorização explícita, item por item | O handbook condiciona gravação à permissão (§3.1.2.3, p. 87) |
| Notas anonimizadas: "P1", "P2", "C1", "M1" | Permite citar sem identificar |
| Ambiente de teste, **nunca** a conta de produção de outra pessoa | Isolamento de dados (RN09) |

---

## 8. Processamento dos resultados

O handbook trata isso como etapa própria, e não como "depois a gente vê" (§3.1.2.1, p. 81):

1. **Análise usuário–tarefa–sistema–contexto–problema** sobre os dados brutos, aplicando leitura
   baseada em perspectiva. Produz um artefato intermediário.
2. **Diagrama de afinidade** para agrupar os achados soltos (p. 81).
3. Extrair: personas reais, processos e atritos, lista de produtos de trabalho usados, **lista de
   problemas**, e por fim metas, necessidades e requisitos.
4. **Revisão das notas por um especialista do domínio** — recomendação explícita do handbook contra
   o viés de simplificação (p. 79).

### Como o resultado entra na especificação

| Achado | Destino |
|---|---|
| Hipótese confirmada | A página do requisito troca "declarado" por evidência, citando a sessão |
| Hipótese refutada | Card de mudança, análise de impacto na [Matriz](Matriz-de-Rastreabilidade), requisito reescrito |
| Necessidade nova | Novo RF/RNF com fonte = "sessão de validação", seguindo o [checklist de revisão](Validacao-e-Verificacao#5-checklist-de-revisão-para-requisitos-novos) |
| Palavra nova do usuário | Entra no [Glossário](Glossario) e nos rótulos do bot |
| Conflito novo | Entra na tabela de [conflitos](Stakeholders-e-Fontes-de-Requisitos#4-conflitos-entre-requisitos) com a técnica de resolução |

---

## 9. Quando este estudo está concluído

- [ ] Pelo menos 3 sessões com pacientes, incluindo **uma pessoa não alfabetizada**
- [ ] Pelo menos 2 cuidadores e 2 profissionais entrevistados
- [ ] As 8 hipóteses com veredito registrado (inclusive "inconclusiva")
- [ ] Notas revisadas por um especialista do domínio
- [ ] Achados publicados nesta wiki, com os requisitos afetados atualizados
- [ ] Cards abertos para cada hipótese refutada

Só então a linha "Validação: **ausente**" em
[Validação e Verificação](Validacao-e-Verificacao#o-veredito-deste-projeto-em-uma-linha) pode mudar.

---

## 10. Riscos do próprio estudo

| Risco | Mitigação |
|---|---|
| **Viés de simplificação** do observador | Conversa prévia com especialista; revisão das notas por ele (p. 79) |
| **Efeito da observação** — a pessoa age diferente por estar sendo vista | Observação sem interação no momento do lembrete; pedir que ela "esqueça" a presença (p. 80) |
| **Pergunta que ensina a resposta** | Perguntas abertas; nunca oferecer o botão certo |
| **Recrutamento difícil** | Começar por uma unidade de saúde ou grupo de convivência, via o profissional da conversa prévia |
| **Dano clínico** | A regra do §7: a sessão para antes de atrapalhar uma dose |
| **Achado inconveniente ser ignorado** | Cada hipótese refutada vira card, com análise de impacto — não vira nota de rodapé |

---

## Próximo

- [Validação e Verificação](Validacao-e-Verificacao)
- [Stakeholders e Fontes de Requisitos](Stakeholders-e-Fontes-de-Requisitos)
- [Acessibilidade](Acessibilidade)
