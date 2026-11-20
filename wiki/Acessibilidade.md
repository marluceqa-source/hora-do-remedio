# Acessibilidade

O público-alvo do bot são **pessoas idosas, não alfabetizadas ou com dificuldade de leitura e
visão**. Isso não é um detalhe de interface: condiciona decisões de arquitetura.

---

## Princípio

> Se a pessoa precisa **ler** ou **digitar** para usar o sistema, o sistema falhou com parte
> do seu público.

---

## No bot (paciente)

| Decisão | Por quê |
|---|---|
| **Navegação 100% por botões** no menu fixo do Telegram. | Não exigir digitação em nenhum fluxo principal. |
| **Mensagens de voz (TTS local)** no `/start`, na ajuda e, opcionalmente, em toda confirmação de ação. | Quem não lê consegue operar ouvindo. Ligado/desligado em ⚙️ Configurações. |
| Cadastro do nome do medicamento **por voz** (STT local). | Alternativa a digitar. Sempre com confirmação ([RN11](Regras-de-Negocio-Bot-e-API)). |
| Cadastro **por fotografia** da embalagem, com OCR local. | A pessoa fotografa a caixa em vez de transcrever o nome. Sempre com confirmação ([RN10](Regras-de-Negocio-Bot-e-API)). |
| Lembrete com **botões grandes e ícones**: ✅ Tomei · ⏰ Mais tarde · ❌ Não tomei. | Alvo de toque grande, significado reforçado por ícone e cor, não só por texto. |
| **Ilustrações** nos fluxos principais (`assets/illustrations/`). | Reconhecimento visual independente de leitura. |
| Áudio opcional por medicamento (campo `audio_text`). | O lembrete pode **falar** a orientação daquele remédio específico. |
| Vínculo ao bot por **deep link / QR Code**, não por código digitado. | [RN23](Regras-de-Negocio-Portal) — o paciente só toca no link ou aponta a câmera. |

### Detalhe de implementação que importa

O áudio gerado pelo TTS (`pyttsx3`) sai em `.aiff`, formato que o Telegram **não reproduz**.
O `services/text_to_speech_service.py` converte para `.m4a` antes de enviar. Sem essa
conversão, a mensagem de voz chega como arquivo mudo — o recurso de acessibilidade mais
importante do bot ficaria silenciosamente quebrado.

---

## No portal (profissional)

O portal tem outro público, mas também tem metas de acessibilidade:

| Decisão | Por quê |
|---|---|
| Tema MUI com paleta orientada a **contraste WCAG AA** e contorno visível de `focus-visible`. | Navegação por teclado e legibilidade. |
| `<html lang="pt-BR">`. | Leitores de tela pronunciam o conteúdo corretamente. |
| Alertas de erro com `role="alert"`. | O leitor de tela anuncia o erro quando ele aparece. |
| Erro de validação **no próprio campo** (`helperText`), não só num alerta no topo. | O erro é anunciado junto do campo que o causou. |
| `noValidate` nos formulários + validação própria em português. | A validação nativa do navegador aparece **no idioma do sistema operacional**, que pode não ser português, e não é controlada por `lang="pt-BR"`. |
| Botão desabilitado **sempre acompanhado de texto** explicando o motivo. | Ex.: na ativação de tratamento, o portal explica [RN20](Regras-de-Negocio-Portal) em texto — a pessoa entende por que não pode, em vez de achar que é um bug. |
| Navegação responsiva (AppBar + Drawer). | Uso em tela pequena. |

---

## Tudo em português

Nenhuma mensagem crua de framework chega ao usuário:

- **Validação de formulário** — todos os formulários do portal (login, MFA, cadastro de
  profissional, cadastro de paciente, cadastro de medicamento, recuperação de senha) validam
  em português **antes** de chamar a API.
- **Erros do backend** — `frontend/src/api/client.ts` traduz as mensagens do Pydantic e
  acrescenta o **rótulo do campo** (ex.: *"Senha: deve ter pelo menos 8 caracteres"* em vez de
  *"String should have at least 8 characters"*).
- **Erros de rede** — as mensagens do Axios (`"Network Error"`, timeouts) são substituídas por
  texto em português.

---

## O que ainda não foi verificado

A acessibilidade do portal foi construída com essas decisões, mas **ainda não foi auditada
automaticamente** — os testes com axe-core e Playwright não foram implementados. Ver
[Limitações Conhecidas](Limitacoes-Conhecidas).

---

## Próximo

- [Visão Geral do Sistema](Visao-Geral)
- [Limitações Conhecidas](Limitacoes-Conhecidas)
