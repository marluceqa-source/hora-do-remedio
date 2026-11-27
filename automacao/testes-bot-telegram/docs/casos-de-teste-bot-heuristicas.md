# Casos de Teste — Bot do Telegram (heurísticas de Elisabeth Hendrickson)

Os casos deste projeto saíram do material **Test Heuristics Cheat Sheet** (Test Obsessed),
com ideias de **Elisabeth Hendrickson**, James Lyndsay e Dale Emery — o mesmo documento de
[Heurísticas de Teste](../../Heurísticas%20de%20Teste.docx) da pasta `Automacao`.

Cada grupo de heurística virou um arquivo de teste, e cada caso cita no próprio código a
heurística que o originou.

| Grupo da heurística | Arquivo | Casos | Testes |
| --- | --- | --- | --- |
| Ataques de Tipos de Dados | `testes/test_ataques_tipos_de_dados.py` | CT-BOT-D01 a D11 | 37 |
| Testes de Strings | `testes/test_ataques_de_strings.py` | CT-BOT-S01 a S10 | 14 |
| Heurísticas Gerais — CRUD e Siga os Dados | `testes/test_crud_e_siga_os_dados.py` | CT-BOT-C01 a C08 | 8 |
| Heurísticas Gerais — Interrupções | `testes/test_interrupcoes.py` | CT-BOT-I01 a I07 | 7 |
| Sabedoria em Testes — Adote abordagem contrária | `testes/test_abordagem_contraria.py` | CT-BOT-X01 a X07 | 7 |
| Guarda do condutor de conversa | `testes/test_mapa_da_conversa.py` | — | 3 |

A diferença entre "casos" e "testes" é a parametrização: CT-BOT-D02, por exemplo, é um caso
que roda quatro vezes, uma para cada data inválida.

---

## Ataques de Tipos de Dados

| ID | Heurística | Caso de teste | Resultado esperado |
| --- | --- | --- | --- |
| CT-BOT-D01 | Nome já existente | Cadastrar duas vezes o mesmo medicamento | **Comportamento atual:** os dois são aceitos, sem aviso de duplicidade (risco R6) |
| CT-BOT-D02 | Dias inválidos | Início em 30/02, 31/09, 32/01 e 00/01 | "Data inválida" e o bot continua pedindo a data |
| CT-BOT-D03 | Formatos de data | "5 de junho de 2001", "2026-11-26", "06-05-01", "6/5/26" | "Data inválida" — só DD/MM/AAAA e "hoje" são aceitos |
| CT-BOT-D04 | Formatos de data (o lado que deve passar) | "hoje", "HOJE", "today", "26/11/2026" | Aceitos; a conversa avança para a data de término |
| CT-BOT-D05 | Dias inválidos entre dois campos | Término anterior ao início | Explica o motivo e não grava nada |
| CT-BOT-D06 | Faixa de valores | Horários "24:00", "07:60", "-1:00", "8h30", "manhã", "08:30:00", vazio, "::" | "Horário inválido" e permanece pedindo o horário |
| CT-BOT-D07 | Bordas da faixa | Horários "00:00", "23:59", "8:30" | Aceitos; "8:30" é normalizado para 08:30 |
| CT-BOT-D08 | Faixa de valores | Intervalos "0", "25", "-3", "1.5", "três", vazio | "Intervalo inválido. Digite um número entre 1 e 24" |
| CT-BOT-D09 | Bordas da faixa | Intervalos "1", "24", " 3 " | Aceitos, inclusive com espaços em volta |
| CT-BOT-D10 | Diferença de horários entre máquinas | Cadastro completo | O fuso do usuário (America/Sao_Paulo) é gravado junto do horário |
| CT-BOT-D11 | Tempo limite | `/start` com convite vencido | Avisa que o convite não vale e não vincula o paciente |

## Testes de Strings

| ID | Heurística | Caso de teste | Resultado esperado |
| --- | --- | --- | --- |
| CT-BOT-S01 | Em branco | Nome vazio e nome só com espaços | "O nome não pode ficar em branco" |
| CT-BOT-S02 | Espaços no início ou fim | Nome `"  Losartana  "` | Gravado como `"Losartana"` — o bot faz `strip()` (ver R3) |
| CT-BOT-S03 | Acentuados / asiáticos / delimitadores | Nome com acentos, japonês e aspas, `<tag>`, `&`, `;` | Gravado e devolvido exatamente igual |
| CT-BOT-S04 | Injeção de SQL | Nome com `'); DROP TABLE medications; --` | Vira texto literal; a base segue íntegra no cadastro seguinte |
| CT-BOT-S05 | Strings longas | Nome com 200 caracteres | Aceito |
| CT-BOT-S06 | Strings longas | Nome com 201 caracteres | Explica o motivo, não grava — e **descarta o rascunho inteiro** (risco R7) |
| CT-BOT-S07 | Strings longas | Observação com 500 e com 501 caracteres | 500 aceito; 501 recusado com o motivo |
| CT-BOT-S08 | Em branco | Dosagem e quantidade só com espaços | Cada campo tem sua própria mensagem |
| CT-BOT-S09 | Palavra reservada | Observação "pular" | Grava sem observação |
| CT-BOT-S10 | Abordagem contrária na palavra reservada | Observação "Não pular a dose da noite" | Gravada inteira — "pular" no meio da frase não é comando |

## Heurísticas Gerais — CRUD e Siga os Dados

| ID | Heurística | Caso de teste | Resultado esperado |
| --- | --- | --- | --- |
| CT-BOT-C01 | CRUD (criar e ler) | Cadastrar e abrir "Meus Remédios" | O medicamento aparece com dose e quantidade |
| CT-BOT-C02 | CRUD (ler vazio) | Abrir "Meus Remédios" sem nada cadastrado | Orienta a usar "Adicionar Remédio", sem erro seco |
| CT-BOT-C03 | Siga os Dados | Cadastro completo | usuário → medicamento → horário, tudo amarrado pelos ids |
| CT-BOT-C04 | CRUD (integridade) | Cadastrar com dois horários | Um medicamento só, com dois horários |
| CT-BOT-C05 | Siga os Dados | Cadastro completo com agendador ligado | O horário criado também entra no agendador |
| CT-BOT-C06 | CRUD (atualizar) | Confirmar um lembrete | Status vira `confirmed` e aparece no histórico como "tomado" |
| CT-BOT-C07 | Siga os Dados | Abrir "Remédios de Hoje" | A lista reflete o estado real de cada dose |
| CT-BOT-C08 | Siga os Dados | Outro usuário abre "Meus Remédios" | Não enxerga o medicamento alheio |

## Heurísticas Gerais — Interrupções

| ID | Heurística | Caso de teste | Resultado esperado |
| --- | --- | --- | --- |
| CT-BOT-I01 | Interrupções | `/cancelar` no meio do cadastro | Rascunho descartado, nada gravado |
| CT-BOT-I02 | Interrupções | Cancelar pelo botão, já no resumo | Nada gravado |
| CT-BOT-I03 | Interrupções | Recomeçar o cadastro sem cancelar | O rascunho anterior é zerado |
| CT-BOT-I04 | Reinício | Contrato da conversa | `persistent=False`: um reinício do bot perde o cadastro em andamento |
| CT-BOT-I05 | Tempo limite | Tocar em um lembrete já encerrado | "Esse lembrete é antigo... Nada foi registrado" e o status não muda |
| CT-BOT-I06 | Interrupções | Confirmar a mesma dose duas vezes | "Essa dose já havia sido confirmada" |
| CT-BOT-I07 | Interrupções | Adiar uma dose já confirmada | Recusado; o contador de adiamentos não mexe |

## Sabedoria em Testes — Adote abordagem contrária

| ID | Caso de teste | Resultado esperado |
| --- | --- | --- |
| CT-BOT-X01 | Confirmar o lembrete de outra pessoa | "Lembrete não encontrado"; o lembrete alheio não muda |
| CT-BOT-X02 | Marcar "não tomei" no lembrete de outra pessoa | Mesma proteção |
| CT-BOT-X03 | Adiar o lembrete de outra pessoa | Mesma proteção |
| CT-BOT-X04 | Confirmar um lembrete que nunca existiu | Avisa sem quebrar o bot |
| CT-BOT-X05 | `/start` com convite inventado | Avisa e segue para a boas-vindas |
| CT-BOT-X06 | Usar o mesmo convite duas vezes | O segundo uso é recusado; o vínculo do primeiro permanece |
| CT-BOT-X07 | Recusar o convite ("não sou eu") | Ninguém é vinculado |

---

## O que ficou de fora

- **Áudio e foto** (RF03, RF04, RF11): os caminhos de voz e de OCR dependem de
  `faster-whisper`, Tesseract e de arquivos de mídia de verdade. Dão um projeto de teste
  próprio, com massa de áudio e imagem.
- **Entrega do lembrete pelo Telegram**: o envio em si é do `notification_service` e do
  agendador; aqui o lembrete é montado direto no banco e o teste investiga a resposta
  da pessoa ao botão.
- **Conversa de verdade no Telegram**: exigiria token do BotFather e uma conta de teste.
  Os handlers são exercitados como funções, que é onde mora o comportamento investigado
  pelas heurísticas.
