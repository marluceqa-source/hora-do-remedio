# Ciclo de Vida do Tratamento

Como uma prescrição feita no portal se transforma em lembrete no Telegram do paciente — e o
que acontece quando ela muda.

---

## A decisão de arquitetura central

O portal **não reimplementou o agendador**. Existem duas camadas distintas:

| Camada | Tabelas | Quem usa |
|---|---|---|
| **Clínica / prescritiva** | `TreatmentPlan`, `TreatmentMedication`, `TreatmentMedicationSchedule` | Portal. É versionada e guarda a intenção do profissional. |
| **Operacional / executora** | `Medication`, `Schedule`, `ReminderEvent` | Bot e agendador, exatamente como já existiam antes do portal. |

Ativar um tratamento **materializa** a camada operacional a partir da clínica
([RN26](Regras-de-Negocio-Portal)). O campo `TreatmentMedication.linked_medication_id`
(com restrição `UNIQUE`) é o elo entre as duas.

Consequência prática: o agendador, o bot, os lembretes e o histórico continuaram funcionando
sem alteração, e **nenhuma regra de agendamento existe em dois lugares**.

---

## Os estados

```
                   ┌──────────────────────────┐
                   │          draft           │  ← nasce aqui (RN25: não gera lembrete)
                   └────────────┬─────────────┘
                                │  ativar  (só médico — RN20)
                                │  exige paciente vinculado ao Telegram
                                ▼
                   ┌──────────────────────────┐
         ┌────────▶│          active          │  ← materializa Medication + Schedule (RN26)
         │         └────────────┬─────────────┘
         │                      │
   ativar│             suspender│  (RN28: Medication.active = False)
    nova │                      ▼
  versão │         ┌──────────────────────────┐
         │         │        suspended         │
         │         └──────────────────────────┘
         │
         │  editar um tratamento ATIVO (RN27)
         │  ┌──────────────────────────┐
         └──│   nova versão em draft   │   a versão anterior vira `closed`
            └──────────────────────────┘
```

Status possíveis: `draft` · `pending_validation` · `active` · `suspended` · `closed`

---

## Passo a passo

### 1. Rascunho
O profissional cadastra o medicamento, a dose, a quantidade por administração, as orientações,
as datas e os horários. O registro nasce como `draft`.

**Nada é agendado.** [RN25](Regras-de-Negocio-Portal) — o paciente não recebe nada, e a tela
do portal diz isso: *"Fica como rascunho — só gera lembretes depois de revisado e ativado."*

### 2. Ativação
Só um profissional com `role = medico` pode ativar ([RN20](Regras-de-Negocio-Portal)), e só se
o paciente já estiver **vinculado ao Telegram** — sem vínculo não há destino para o lembrete.

Ao ativar:
1. São criados (ou atualizados) o `Medication` e os `Schedule` reais.
2. O agendador passa a disparar os lembretes nos horários e no fuso configurados
   ([RN07](Regras-de-Negocio-Bot-e-API)).
3. O paciente recebe uma **notificação de que um novo medicamento foi cadastrado para ele**,
   enviada **após** a resposta HTTP — a notificação não trava nem derruba a requisição do
   profissional.

### 3. Edição de um tratamento ativo → nova versão
Editar um tratamento **ativo** nunca sobrescreve a versão anterior
([RN27](Regras-de-Negocio-Portal)):

- Uma **nova versão** é criada em `draft`, encadeada pelo campo `previous_version_id`.
- A versão ativa anterior continua valendo até que a nova seja ativada.
- Ao ativar a nova versão, a anterior passa a `closed` e **libera** seu
  `linked_medication_id` (a restrição `UNIQUE` não permitiria duas versões apontando para a
  mesma linha de `Medication`).
- A **mesma linha** de `Medication` é atualizada — por isso o histórico de `ReminderEvent` já
  emitido **não se perde**.

O portal mostra as versões anteriores na tela de detalhe do medicamento.

> Isso é deliberado: o histórico de doses de um paciente precisa sobreviver a uma mudança de
> dosagem. Apagar e recriar o medicamento jogaria fora o passado clínico.

### 4. Suspensão
Suspender marca o `Medication` como `active = False`. O agendador já ignora medicamentos
inativos ([RN15](Regras-de-Negocio-Bot-e-API)), então **nenhum lembrete novo é gerado** —
sem precisar de código novo no portal ([RN28](Regras-de-Negocio-Portal)).

O histórico anterior permanece consultável.

### 5. Encerramento natural
Se o tratamento tem data de término, o agendador para de disparar quando essa data passa
([RN03](Regras-de-Negocio-Bot-e-API)), comparando no **fuso do agendamento**, não no do
servidor.

---

## O que o paciente vê

| Momento | No Telegram |
|---|---|
| Tratamento ativado | Notificação de novo medicamento cadastrado, com opção de **ouvir em áudio** e de ver os detalhes. |
| No horário | Lembrete com botões grandes: **✅ Tomei**, **⏰ Mais tarde**, **❌ Não tomei**. |
| Adiamento | Novo lembrete em 5, 10, 15 ou 30 min — **sem alterar o horário original** ([RN06](Regras-de-Negocio-Bot-e-API)). |

O paciente **não vê jargão de status** (`draft`, `active`, `suspended`). Esses nomes existem
para o profissional e para o banco.

---

## Próximo

- [Regras de Negócio — Portal](Regras-de-Negocio-Portal)
- [Regras de Negócio — Bot e API](Regras-de-Negocio-Bot-e-API)
