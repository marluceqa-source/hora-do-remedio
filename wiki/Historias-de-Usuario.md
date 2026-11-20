# Histórias de Usuário e Critérios de Aceitação

Os mesmos requisitos das páginas [Requisitos Funcionais](Requisitos-Funcionais) e
[Regras de Negócio](Regras-de-Negocio-Bot-e-API), reescritos na forma de histórias com critérios
de aceitação executáveis. **Não são requisitos novos**: cada história aponta o RF/RN de origem.

---

## Os conceitos

> **História de Usuário:** "Uma narrativa curta descrevendo uma necessidade da perspectiva de um
> usuário, junto com o benefício esperado quando essa necessidade é satisfeita."
> Notas: "1. Histórias de usuário são tipicamente escritas em linguagem natural usando o
> **template de história de usuário** e normalmente são acompanhadas de **critérios de
> aceitação**. 2. (…) são tipicamente consideradas itens atômicos de backlog, isto é, itens que
> não são decompostos adicionalmente no backlog."
> — Glossário, verbete *História de Usuário*, p. 16

> **Critério de aceitação:** "1. Os critérios que um produto de trabalho deve satisfazer para ser
> aceito pelos stakeholders. 2. Em desenvolvimento ágil: critérios que a implementação de um item
> de backlog deve satisfazer para ser aceita pelos stakeholders."
> — Glossário, verbete *Critério de aceitação*, p. 8

O formato Gherkin usado abaixo corresponde ao que o glossário chama de **especificação por
exemplo**: "uma técnica que especifica casos de teste e requisitos para um sistema fornecendo
exemplos de como o sistema deve se comportar" (p. 14).

> **Complemento baseado em conhecimento externo aos arquivos fornecidos:** a sintaxe
> `Dado / Quando / Então` (Gherkin) e a prática de BDD não são definidas nos documentos do IREB
> usados nesta wiki; o glossário cobre o conceito (especificação por exemplo), não a notação.

---

## Paciente

### HU01 — Cadastrar um remédio sem precisar ler
> Como **paciente com dificuldade de leitura**, quero cadastrar meu remédio navegando por
> botões e ouvindo as instruções, para conseguir usar o sistema sozinho.
>
> Origem: RF02, RF11 · Regras: RN01, RN02

```gherkin
Cenário: cadastro com dois horários pelo menu
  Dado que estou no menu principal do bot
  Quando eu escolher "➕ Adicionar Remédio"
  E informar o nome, a dosagem e a quantidade
  E informar os horários "08:00" e "20:00"
  Então o remédio é salvo com os dois horários
  E recebo uma confirmação com áudio

Cenário: nenhuma etapa obrigatória exige comando digitado
  Dado que estou em qualquer etapa do cadastro
  Então todas as opções de navegação estão disponíveis como botão
```
*Verificado em:* `tests/unit/test_bot_menu_structure.py` (CT24),
`tests/integration/test_cadastro_flow.py` (CT30)

---

### HU02 — Cadastrar fotografando a embalagem
> Como **paciente que não lê bem**, quero fotografar a caixa do remédio, para não precisar
> digitar o nome.
>
> Origem: RF03 · Regra: **RN10**

```gherkin
Cenário: texto reconhecido é apenas sugestão
  Dado que enviei a fotografia da embalagem
  Quando o OCR reconhecer um possível nome
  Então o sistema me mostra o texto reconhecido e pede confirmação
  E o nome que eu digitei antes não é sobrescrito

Cenário: reconhecimento incerto
  Dado que a fotografia não permite reconhecer nenhum nome
  Então o sistema pede o nome de outra forma, em mensagem acessível
  E a fotografia continua associada ao cadastro
```
*Verificado em:* `tests/unit/test_bot_photo_voice.py` (CT19, CT20)

---

### HU03 — Cadastrar falando
> Como **paciente que não escreve**, quero dizer o nome do remédio em uma mensagem de voz, para
> cadastrar sem teclado.
>
> Origem: RF04 · Regra: **RN11**

```gherkin
Cenário: transcrição confirmada
  Dado que enviei um áudio dizendo o nome do remédio
  Quando a transcrição for reconhecida
  Então o sistema repete o que entendeu e pede confirmação
  E só grava o nome depois da minha confirmação explícita

Cenário: transcrição vazia
  Dado que enviei um áudio que não pôde ser transcrito
  Então o sistema pede que eu tente novamente
  E nenhum valor é assumido
```
*Verificado em:* `tests/unit/test_bot_photo_voice.py` (CT21, CT26)

---

### HU04 — Ser lembrado no horário certo
> Como **paciente**, quero receber o lembrete no horário do meu fuso, com a foto do remédio e
> áudio, para tomar a dose certa na hora certa.
>
> Origem: RF05, RF06 · Regras: RN03, RN07, RN08, RN15, RN18

```gherkin
Cenário: disparo no fuso do agendamento
  Dado um remédio agendado para 08:00 no fuso "America/Sao_Paulo"
  Quando chegar 08:00 nesse fuso
  Então recebo o lembrete com a foto, o nome, a dosagem e os botões
  E o horário do servidor não altera esse cálculo

Cenário: tratamento encerrado
  Dado um remédio com data de término ontem
  Quando chegar o horário agendado hoje
  Então nenhum lembrete é enviado

Cenário: reinício do serviço
  Dado que existem agendamentos salvos
  Quando o processo do bot for reiniciado
  Então os agendamentos voltam a valer sem recadastro

Cenário: falha no envio
  Dado que o Telegram está indisponível no horário do lembrete
  Então a falha é registrada em log
  E o evento não é marcado como entregue
  E nenhum lembrete duplicado é criado para o mesmo horário
```
*Verificado em:* `tests/unit/test_scheduler_firing.py` (CT05, CT11, CT14, CT15, CT18, CT42),
`tests/unit/test_notification_service.py` (CT13, CT22, CT27)

---

### HU05 — Confirmar que tomei
> Como **paciente**, quero confirmar com um toque que tomei a dose, para que meu histórico
> fique correto.
>
> Origem: RF07 · Regras: **RN04**, **RN05**, RN12

```gherkin
Cenário: confirmação registrada
  Dado que recebi o lembrete das 08:00
  Quando eu tocar em "✅ Tomei"
  Então a dose é registrada como confirmada com data e hora
  E recebo uma confirmação sonora

Cenário: confirmação duplicada
  Dado que já confirmei a dose das 08:00
  Quando eu tocar em "✅ Tomei" novamente
  Então o sistema informa que a dose já estava confirmada
  E nenhum segundo registro é criado
```
*Verificado em:* `tests/unit/test_reminder_service.py`, `tests/api/test_reminders.py`,
`tests/unit/test_bot_reminders_handler.py` (CT23, CT25)

---

### HU06 — Adiar sem desarrumar a rotina
> Como **paciente**, quero adiar o lembrete alguns minutos, para ser avisado de novo sem perder
> o horário original do tratamento.
>
> Origem: RF08 · Regra: **RN06**

```gherkin
Cenário: adiamento de 15 minutos
  Dado que recebi o lembrete das 08:00
  Quando eu escolher adiar por 15 minutos
  Então recebo um novo lembrete 15 minutos depois
  E o horário programado de 08:00 continua inalterado
  E a contagem de adiamentos é incrementada
```
*Verificado em:* `tests/api/test_reminders.py`, `services/reminder_service.py`

---

### HU07 — Consultar meu histórico
> Como **paciente**, quero ver o que tomei por dia, semana ou mês, para acompanhar meu
> tratamento.
>
> Origem: RF09

```gherkin
Cenário: filtro por período
  Dado que tenho doses confirmadas, não tomadas e sem resposta
  Quando eu consultar o histórico da semana
  Então vejo cada dose com seu status e, quando houver, a hora da confirmação
```
*Verificado em:* `tests/api/test_history_reports.py`

---

### HU08 — Ter um relatório que não me acuse
> Como **paciente**, quero que o relatório diga apenas o que eu declarei, para não ser registrado
> como "não tomei" por não ter respondido.
>
> Origem: RF10 · Regra: **RN12**

```gherkin
Cenário: silêncio não é "não tomou"
  Dado um lembrete entregue e nunca respondido
  Quando eu gerar o relatório do período
  Então essa dose aparece como sem confirmação
  E não é contada como "não tomada"
  E o relatório declara que mede adesão declarada
```
*Verificado em:* `tests/unit/test_report_service.py`, `tests/api/test_history_reports.py`

---

### HU09 — Autorizar e revogar um cuidador
> Como **paciente**, quero autorizar alguém de confiança a acompanhar meu tratamento e poder
> revogar esse acesso quando eu quiser.
>
> Origem: RF12 · Regra: **RN14**

```gherkin
Cenário: autorização por código
  Dado que gerei um código de convite
  Quando o cuidador informar esse código no bot
  Então ele passa a consultar meus medicamentos e meu histórico

Cenário: revogação
  Dado um cuidador com acesso ativo
  Quando eu revogar o acesso
  Então qualquer nova consulta dele é recusada
```
*Verificado em:* `tests/unit/test_caregiver_service.py` (CT28), `tests/api/test_caregivers.py`

---

## Cuidador

### HU10 — Acompanhar quem eu cuido
> Como **cuidador autorizado**, quero consultar os remédios e o histórico do paciente, para
> ajudar sem precisar de uma conta nova.
>
> Origem: RF12 · Regras: RN14, RN09

```gherkin
Cenário: acesso somente leitura e somente do paciente que autorizou
  Dado que sou cuidador autorizado do paciente A
  Quando eu consultar dados do paciente B
  Então o acesso é recusado
```
*Verificado em:* `tests/api/test_caregivers.py`, `tests/api/test_isolation.py` (CT41)

---

## Profissional de saúde

### HU11 — Cadastrar o paciente e vinculá-lo sem digitação
> Como **profissional de saúde**, quero cadastrar o paciente e entregar um convite que ele
> ativa com um toque, para que ele receba os lembretes sem configurar nada.
>
> Origem: RF03 e RF04 do portal · Regras: **RN22**, **RN23**, **RN24**

```gherkin
Cenário: convite de uso único
  Dado um paciente cadastrado por mim
  Quando eu gerar o convite de vínculo
  Então recebo um link do Telegram e o QR Code correspondente
  E o convite expira no prazo configurado

Cenário: convite já usado
  Dado um convite já consumido
  Quando alguém tentar usá-lo novamente
  Então o vínculo é recusado
```
*Verificado em:* `tests/unit/test_patient_service.py`, `tests/api/test_patients.py`

---

### HU12 — Ativar só o que foi validado
> Como **médico**, quero ativar o tratamento depois de revisá-lo, para que o paciente só receba
> lembretes de uma prescrição conferida.
>
> Origem: RF05 e RF06 do portal · Regras: **RN20**, **RN25**, **RN26**

```gherkin
Cenário: rascunho não gera lembrete
  Dado um tratamento em rascunho
  Então nenhum lembrete é agendado para o paciente

Cenário: ativação pelo médico
  Dado um tratamento em rascunho de um paciente já vinculado ao Telegram
  Quando eu, como médico, ativá-lo
  Então o medicamento e os horários reais são criados
  E o paciente é notificado no Telegram

Cenário: ativação por outro papel
  Dado um tratamento em rascunho
  Quando um enfermeiro tentar ativá-lo
  Então a operação é recusada com a resposta 403 e o motivo explicado
```
*Verificado em:* `tests/unit/test_treatment_service.py`, `tests/unit/test_professional_rbac.py`,
`tests/api/test_treatment_medications.py`

---

### HU13 — Mudar a dose sem apagar o passado
> Como **médico**, quero alterar um tratamento ativo criando uma nova versão, para que o
> histórico de doses do paciente continue válido.
>
> Origem: RF07 do portal · Regra: **RN27**

```gherkin
Cenário: edição de tratamento ativo
  Dado um tratamento ativo com doses já registradas
  Quando eu editá-lo
  Então uma nova versão é criada em rascunho, ligada à versão anterior
  E a versão ativa continua valendo até eu ativar a nova
  E o histórico de doses já emitidas permanece consultável
```
*Verificado em:* `tests/unit/test_treatment_service.py`

---

### HU14 — Suspender um tratamento
> Como **profissional de saúde**, quero suspender um tratamento, para que o paciente pare de
> receber lembretes imediatamente.
>
> Origem: RF07 do portal · Regras: **RN28**, RN15

```gherkin
Cenário: suspensão interrompe os lembretes
  Dado um tratamento ativo
  Quando eu suspendê-lo
  Então nenhum lembrete novo é gerado
  E o histórico anterior continua consultável
```
*Verificado em:* `tests/unit/test_treatment_service.py`

---

### HU15 — Ver o painel dos meus pacientes
> Como **profissional de saúde**, quero ver pacientes, tratamentos e confirmações em um painel,
> para priorizar quem precisa de atenção.
>
> Origem: RF02 do portal · Regras: RN12, **RN22**

```gherkin
Cenário: painel restrito ao vínculo ativo
  Dado que tenho vínculo ativo com o paciente A
  Quando eu abrir o painel
  Então vejo o paciente A
  E não vejo pacientes sem vínculo ativo comigo
  E as confirmações são apresentadas como adesão declarada
```
*Verificado em:* `tests/unit/test_dashboard_service.py`, `tests/api/test_dashboard_and_admin.py`

---

## Administrador

### HU16 — Verificar quem é profissional e auditar
> Como **administrador**, quero verificar as solicitações de cadastro e consultar a trilha de
> auditoria, para que só profissionais confirmados atuem no portal.
>
> Origem: RF01 do portal · Regra: **RN32**

```gherkin
Cenário: cadastro não concede acesso clínico
  Dado um profissional recém-cadastrado
  Então seu status é "pendente" até que eu o verifique

Cenário: auditoria sem dado clínico
  Quando eu consultar a trilha de auditoria
  Então vejo ator, papel, ação e momento
  E não vejo dados clínicos de pacientes
```
*Verificado em:* `tests/api/test_dashboard_and_admin.py`,
`tests/unit/test_professional_auth_service.py`

---

## Resumo

- 16 histórias cobrem os quatro papéis do sistema: paciente, cuidador, profissional e
  administrador.
- Nenhuma história introduz comportamento novo: todas apontam o RF/RN de origem e o teste que
  as sustenta.
- Os critérios de aceitação em Gherkin são a ponte entre a especificação e a suíte de testes —
  ver [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade).

---

## Próximo

- [Matriz de Rastreabilidade](Matriz-de-Rastreabilidade)
- [Priorização e Backlog](Priorizacao-e-Backlog)
- [Validação e Verificação](Validacao-e-Verificacao)
