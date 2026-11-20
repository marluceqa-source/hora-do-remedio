# Stakeholders e Fontes de Requisitos

De onde vieram os requisitos do Hora do Remédio, quem são as pessoas afetadas por eles e quais
técnicas foram — e **não** foram — aplicadas.

---

## 1. As três classes de fonte

> **Fonte de requisitos:** "A fonte da qual um requisito foi derivado. Nota: fontes típicas são
> **stakeholders, documentos, sistemas existentes** e observações."
> — Glossário, verbete *Fonte de requisitos*, p. 14

O Handbook de Elicitação organiza o capítulo 2 exatamente nessas três classes: stakeholders
(§2.2, p. 48), documentos (§2.3, p. 57) e sistemas (§2.4, p. 61). É a estrutura usada aqui.

| Classe | Peso neste projeto |
|---|---|
| **Documentos** | **Alto.** O prompt master é a especificação de origem de quase todo o produto. |
| **Sistemas** | **Alto.** A Telegram Bot API e os motores locais de OCR/STT/TTS impuseram restrições reais. |
| **Stakeholders** | **Baixo.** Nenhuma pessoa do público-alvo foi consultada diretamente. Ver §4. |

---

## 2. Stakeholders

O Handbook de Elicitação define o conteúdo mínimo da documentação de cada stakeholder
(§2.2.3, p. 55): nome, função, dados de contato, disponibilidade, relevância, área e tempo de
experiência, metas e interesses em relação ao projeto.

> **Lacuna declarada.** Deste esquema, este projeto documenta **função, relevância, metas e
> interesses**. Nome, contato, disponibilidade e experiência **não existem** para nenhum
> stakeholder, porque nenhuma pessoa concreta foi envolvida. A tabela abaixo descreve
> **papéis**, não pessoas — e o handbook é explícito ao pedir pessoas identificáveis.

| Papel | Relevância | Metas e interesses | Afetado por |
|---|---|---|---|
| **Paciente** (usuário direto) | **Crítica** — é quem recebe o lembrete e confirma a dose. | Não esquecer a dose; conseguir usar o sistema sem ler nem escrever; não ser repreendido pelo sistema. | RF01–RF11, RN01–RN18 |
| **Paciente com baixa alfabetização / baixa visão / idoso** | **Crítica** — é o perfil que define o projeto. | Navegar por botões e áudio; reconhecer o remédio pela foto; errar sem consequência. | RF03, RF04, RF11, [Acessibilidade](Acessibilidade) |
| **Cuidador familiar** | Alta — opera em nome do paciente quando este não consegue. | Acompanhar as doses; ser avisado de doses sem confirmação; não precisar de senha nova. | RF12, RN14 |
| **Profissional de saúde (médico)** | Alta — é quem prescreve e **ativa** o tratamento. | Prescrever com segurança; saber se o paciente confirmou; alterar a dose sem perder o histórico. | RF01–RF08 do portal, RN20, RN25–RN28 |
| **Profissional de saúde (enfermeiro / outro)** | Média — cadastra e acompanha, mas não ativa. | Preparar o tratamento; acompanhar pacientes vinculados. | RN20, [Papéis e Permissões](Papeis-e-Permissoes) |
| **Administrador do portal** | Média — governança, não clínica. | Verificar quem é profissional de verdade; auditar operações sensíveis. | RN32, trilha de auditoria |
| **Equipe de desenvolvimento / QA** | Alta — consome a especificação e a API. | Especificação sem ambiguidade; contrato estável; testes executáveis. | RF14, CT31–CT38 |
| **Titular de dados sob a LGPD** (o próprio paciente, nessa condição) | Alta — define restrições legais. | Que dados de saúde não vazem nem sejam compartilhados sem autorização. | RNF08–RNF12, RN09, RN14, RN17 |

### O usuário como grupo especial

O handbook separa **usuários internos** (dentro da empresa, conhecidos e envolvidos
individualmente) de **usuários externos** (compradores de produtos de consumo, em geral não
conhecidos individualmente nem envolvidos diretamente) — §2.2.4, p. 56.

Os pacientes do Hora do Remédio são usuários **externos** no sentido do handbook: não há uma
lista de usuários a entrevistar. Isso explica — mas não resolve — a ausência de elicitação
direta, e é a razão pela qual as decisões de acessibilidade precisam ser tratadas como
hipóteses até serem testadas com pessoas reais.

---

## 3. Técnicas de elicitação aplicadas

O Handbook de Elicitação agrupa as técnicas de coleta em questionamento, observação,
colaboração e **baseadas em artefatos** (§3.1, p. 68). O que este projeto usou pertence
inteiramente ao último grupo.

| Técnica (nomenclatura do handbook) | Onde foi aplicada | Resultado |
|---|---|---|
| **Arqueologia de sistemas** (§3.1.4, p. 98) | Leitura do código de `services/`, `api/routes/`, `bot/handlers/` e `database/models.py`. | Confirmação de quais RN estão garantidas e onde; descoberta de que RN01, RN08, RN14 e RN17 não têm marcação no código. |
| **Leitura baseada em perspectiva** (§3.1.4, p. 98) | Releitura do prompt master pelas perspectivas do paciente, do profissional, do QA e da LGPD. | Extração dos RNF, que estavam diluídos nas seções 8, 11, 12 e 13 do prompt. |
| **Reutilização de requisitos** (§3.1.4, p. 98) | Reaproveitamento das RN do bot pelo portal (RN15 e RN28; RN07 e RN03). | O portal não reimplementou agendamento — ver [Ciclo de Vida do Tratamento](Ciclo-de-Vida-do-Tratamento). |
| **Documentos como fonte** (§2.3, p. 57) | Prompt master, `docs/openapi.yaml`, `core/config.py`, suíte de testes. | RF, RN, CT, parâmetros operacionais e limites configuráveis. |
| **Sistemas como fonte** (§2.4, p. 61) | Telegram Bot API; Tesseract; faster-whisper; pyttsx3; APScheduler. | Restrições RES01–RES05. O handbook prevê exatamente isso: plataformas geram requisitos "principalmente restrições" (§2.4.1, p. 62). |

### Técnicas não aplicadas, e o que isso custa

| Técnica não aplicada | Para que serviria aqui | Risco de não ter |
|---|---|---|
| **Entrevista** (§3.1.1, p. 68) | Entender como um paciente idoso descreve seu próprio remédio. | Os rótulos e a ordem das perguntas do bot são suposição da equipe. |
| **Observação de campo / investigação contextual** (§3.1.2, p. 79) | Ver uma pessoa não alfabetizada usando o bot na hora da dose. | **O risco mais alto do projeto.** Acessibilidade não verificada com quem ela deveria atender. |
| **Workshop de requisitos** (§3.1.3, p. 90) | Alinhar médico, enfermeiro e paciente sobre quem pode ativar um tratamento. | RN20 foi decidida sem contraditório clínico. |
| **Protótipos** (§3.2.3, p. 111) | Testar a compreensão dos ícones e dos áudios antes de implementar. | Os símbolos (💊 📷 🔊 🎤 ✅ ❌ ⏰) vieram do prompt master, sem teste de compreensão. |

Essas lacunas estão registradas no card [#40](https://github.com/marluceqa-source/hora-do-remedio/issues/40),
e o plano para fechá-las está em [Roteiro de Validação com Usuários](Roteiro-de-Validacao-com-Usuarios).

---

## 4. Conflitos entre requisitos

O capítulo 4 do Handbook de Elicitação trata identificação, análise e resolução de conflitos,
e classifica os tipos segundo Moore, estendidos pelo IREB: conflito de temas, de dados, de
interesses, de valor, estrutural e de relacionamento (§4.2.2, p. 147). As técnicas de resolução
apresentadas são acordo, compromisso, votação, análise de alternativas e imposição
(§4.3, p. 152–158), e o handbook pede que a resolução seja **documentada** (§4.4, p. 164).

> **Ressalva honesta.** Os conflitos abaixo são **tensões entre requisitos** identificadas na
> especificação e no código, não disputas registradas entre pessoas — não houve partes em
> conflito a mediar. A classificação por tipo é feita **por analogia** com os tipos de Moore,
> para deixar explícito o que foi trocado por quê.

| ID | Tensão | Tipo (por analogia) | Como foi resolvido | Evidência |
|---|---|---|---|---|
| **CF01** | RF11 pede uso sem ler nem escrever; RF02 exige nome, dosagem, quantidade e datas. | Temas | **Análise de alternativas**: entrada por voz (RF04) e por foto (RF03), sempre com confirmação explícita (RN10, RN11). Os campos que ainda exigem digitação estão nomeados no teste de fluxo acessível. | `tests/integration/test_cadastro_flow.py` (CT30) |
| **CF02** | O cuidador quer saber se a dose foi tomada; RN12 proíbe tratar silêncio como "não tomou". | Valor | **Compromisso**: o sistema relata **adesão declarada**, com os status `pending`/`delivered` distintos de `not_taken`, e diz isso no próprio relatório. | `services/report_service.py`, `api/schemas/report.py` |
| **CF03** | Todo profissional quer poder ativar o tratamento; a responsabilidade clínica recai sobre o médico. | Interesses | **Imposição** (regra normativa), mitigada por transparência: a API responde 403 com motivo e o portal desabilita o botão explicando. | RN20 · `api/routes/treatment_medications.py` |
| **CF04** | OCR e STT em nuvem reconhecem melhor; dados de saúde não devem sair do ambiente. | Valor | **Análise de alternativas**: Tesseract e faster-whisper **locais**, aceitando qualidade menor. | RES03 · `services/ocr_service.py`, `services/speech_to_text_service.py` |
| **CF05** | Mudar a dose de um tratamento ativo; preservar o histórico de doses já emitidas. | Dados | **Análise de alternativas**: versionamento (RN27) com atualização da mesma linha de `Medication`, em vez de apagar e recriar. | `services/treatment_service.py` |

---

## 5. Resumo

- As fontes reais deste projeto foram **documentos e sistemas**; stakeholders entraram apenas
  como papéis inferidos.
- As técnicas aplicadas foram **baseadas em artefatos** — adequadas para reconstruir
  requisitos, insuficientes para descobrir necessidades novas.
- Cinco tensões entre requisitos estão documentadas com a decisão que as resolveu, e todas têm
  evidência no código.
- A lacuna mais relevante é a **ausência de observação de campo** com o público-alvo.

---

## Próximo

- [Requisitos Funcionais](Requisitos-Funcionais)
- [Requisitos Não Funcionais](Requisitos-Nao-Funcionais)
- [Priorização e Backlog](Priorizacao-e-Backlog)
