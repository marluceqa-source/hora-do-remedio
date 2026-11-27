# Heurísticas aplicadas no desenho dos testes

Este projeto não inventou critérios próprios: cada teste nasceu de uma heurística de
teste. Esta página registra qual heurística gerou qual caso — é o que permite revisar a
cobertura depois e explicar as escolhas.

## VADER — heurística para APIs REST (Stuart Ashman)

Mnemônico de cinco pilares: **V**erbs, **A**uthorization, **D**ata, **E**rrors,
**R**esponsiveness. É a espinha dorsal dos testes de API — cada pilar virou um arquivo de
especificação.

| Pilar | Perguntas que guiaram os casos | Casos |
| --- | --- | --- |
| Verbs | Cada verbo faz o que promete? PATCH altera só o que foi enviado? O que acontece com um verbo que o recurso não suporta? | CT-API-V01 a V10 |
| Authorization | Dá para entrar sem credencial? Com credencial adulterada? Um usuário alcança o dado de outro? Cada papel faz só o que deveria? Uma credencial de um público vale no outro? | CT-API-A01 a A12 |
| Data | A estrutura e os tipos do retorno são os do contrato? Quais são os limites de tamanho? O que acontece nas bordas? Caracteres especiais sobrevivem? | CT-API-D01 a D12 |
| Errors | O status é o certo para cada causa? A mensagem diz o problema sem vazar detalhe interno? Entrada inválida vira 422 ou 500? | CT-API-E01 a E15 |
| Responsiveness | Quanto tempo leva? Aguenta chamadas simultâneas sem perder registro? E a maior carga permitida pelo contrato? E acima do limite por minuto? | CT-API-R01 a R08 |

## Heurísticas de ataque a tipos de dados e strings

Baseadas no material da **Test Obsessed — Test Heuristics Cheat Sheet**, com ideias de
Elisabeth Hendrickson, James Lyndsay e Dale Emery. As cargas estão centralizadas em
`support/dados.js`, no objeto `HEURISTICAS_STRING`.

| Heurística | Onde foi aplicada | Caso |
| --- | --- | --- |
| Nome longo (acima de 255/limite do campo) | nome do medicamento (200/201), nome do profissional e do paciente (201) | CT-API-D03, CT-WEB-C08, CT-WEB-P05 |
| Strings longas em campo de texto | orientações do medicamento (500/501) | CT-API-D06 |
| Caracteres acentuados | nome do medicamento com acentuação completa em pt-BR | CT-API-D04 |
| Caracteres asiáticos | nome do medicamento em japonês | CT-API-D04 |
| Caracteres especiais e delimitadores | aspas, apóstrofo, `<tag>`, `&`, ponto-e-vírgula | CT-API-D04 |
| Injeção de SQL | nome do medicamento com `'); DROP TABLE ... --` | CT-API-D05 |
| Em branco | nome vazio e nome só com espaços | CT-API-D08 |
| Espaços no início ou fim | observado no cadastro (risco R3 do relatório de sessão) | CT-API-D08 (nota) |
| Nome já existente | e-mail de profissional e identificador interno de paciente duplicados | CT-API-E10, CT-API-E11, CT-WEB-C06, CT-WEB-P03 |
| Nome inexistente | medicamento e paciente por id inexistente | CT-API-E09, CT-API-A11 |
| Nome/domínio reservado | e-mail com TLD `.test` | CT-API-E08 |
| Dias e formatos de data inválidos | data de término anterior ao início | CT-API-E03 |
| Valores fora da faixa | intervalo entre doses (0, 1, 24, 25 horas) | CT-API-D07 |

## Heurísticas de interface (UI)

| Heurística | Onde foi aplicada | Caso |
| --- | --- | --- |
| Manipular URL | acesso direto a rotas protegidas e a `/admin` sem o papel necessário | CT-WEB-N01, CT-WEB-N04 |
| Atualizar página / voltar | sessão lida do cookie a cada carga da página (o portal consulta `/professionals/me` no boot) | CT-WEB-N01, CT-WEB-N05 |
| Campo com limite de tamanho na própria tela | UF do conselho (2 letras, maiúsculas) e código MFA (6 dígitos) | CT-WEB-C05, CT-WEB-L04 |
| Mensagem de erro do servidor chegando na tela | limite de 200 caracteres validado só no backend | CT-WEB-C08, CT-WEB-P05 |

## O que ficou de fora, e por quê

- **Bot do Telegram (RF04, RF07)**: exige token do BotFather e conversa real no Telegram;
  não é alcançável por Playwright.
- **OCR, fala e voz (RF11 a RF13)**: dependem de Tesseract, faster-whisper e pyttsx3
  instalados e de arquivos de mídia; são testes de outra natureza.
- **Carga e performance**: o pilar Responsiveness aqui pega degradação grosseira, em
  segundos. Medir performance de verdade pede ferramenta própria.
