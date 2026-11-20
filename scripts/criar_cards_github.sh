#!/usr/bin/env bash
# Cria os cards (issues) do projeto Hora do Remédio no GitHub.
#
# Cards do que JÁ FOI ENTREGUE são criados e fechados em seguida, para documentar a entrega
# sem poluir o backlog aberto. Cards de PENDÊNCIA ficam abertos.
#
# Requer: gh instalado e autenticado (`gh auth login`).
# Uso: bash scripts/criar_cards_github.sh

set -euo pipefail

REPO="marluceqa-source/hora-do-remedio"

if ! gh auth status >/dev/null 2>&1; then
  echo "Erro: o gh não está autenticado. Rode 'gh auth login' antes." >&2
  exit 1
fi

echo "==> Criando rótulos"
criar_rotulo() {
  gh label create "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 \
    || gh label edit "$1" --repo "$REPO" --color "$2" --description "$3" >/dev/null 2>&1 \
    || true
}

criar_rotulo "concluído"         "0E8A16" "Já entregue e validado"
criar_rotulo "pendência"         "D93F0B" "Falta implementar ou ajustar"
criar_rotulo "bot"               "1D76DB" "Bot do Telegram"
criar_rotulo "api"               "5319E7" "API REST"
criar_rotulo "portal"            "B60205" "Portal web de profissionais"
criar_rotulo "frontend"          "C2E0C6" "Interface React do portal"
criar_rotulo "regra-de-negócio"  "FBCA04" "Regra de negócio (RN)"
criar_rotulo "segurança"         "E99695" "Autenticação, sessão, privacidade"
criar_rotulo "acessibilidade"    "006B75" "Acessibilidade e idioma"
criar_rotulo "testes"            "BFD4F2" "Testes automatizados"
criar_rotulo "documentação"      "0075CA" "README, wiki, OpenAPI"
criar_rotulo "infra"             "5319E7" "Docker, deploy, operação"

# criar_card <estado: aberto|fechado> <rótulos> <título> <corpo>
criar_card() {
  local estado="$1" rotulos="$2" titulo="$3" corpo="$4"
  local url
  url=$(gh issue create --repo "$REPO" --title "$titulo" --body "$corpo" --label "$rotulos")
  echo "   $estado  $url  $titulo"
  if [ "$estado" = "fechado" ]; then
    gh issue close "$url" --repo "$REPO" --reason completed >/dev/null
  fi
}

echo "==> Cards do que já foi entregue (criados e fechados)"

criar_card fechado "concluído,bot,acessibilidade" \
  "Bot Telegram acessível com navegação 100% por botões" \
  "Interface principal do paciente no Telegram, navegável sem digitar nada: menu fixo com botões grandes, ícones e ilustrações.

Público-alvo: pessoas idosas, não alfabetizadas ou com baixa visão.

Ver [Acessibilidade](../../wiki/Acessibilidade)."

criar_card fechado "concluído,bot,api,regra-de-negócio" \
  "Cadastro de medicamentos com múltiplos horários e recorrências" \
  "Cadastro de nome, dosagem, quantidade, horários, datas e observações. Recorrências: diária, por dias da semana ou por intervalo de horas.

Regras: **RN01** (vários medicamentos por usuário), **RN02** (vários horários por medicamento), **RN16** (exclusão exige confirmação explícita)."

criar_card fechado "concluído,bot,acessibilidade,regra-de-negócio" \
  "Cadastro de medicamento por fotografia da embalagem (OCR local)" \
  "A pessoa fotografa a caixa em vez de transcrever o nome. OCR via Tesseract, rodando **localmente** — a foto não é enviada a terceiros.

Regra **RN10**: o texto reconhecido é só exibido para conferência e **nunca** sobrescreve o que a pessoa informou."

criar_card fechado "concluído,bot,acessibilidade,regra-de-negócio" \
  "Cadastro de medicamento por voz (STT local)" \
  "Cadastro do nome do medicamento falando, via faster-whisper rodando **localmente**.

Regra **RN11**: a transcrição só é aceita após confirmação explícita; transcrição vazia ou ambígua pede nova tentativa, nunca assume valor."

criar_card fechado "concluído,bot,regra-de-negócio" \
  "Agendador de lembretes com fuso horário correto e persistência" \
  "APScheduler no processo do bot, reconstruindo os jobs a partir do banco a cada início.

Regras: **RN03** (não envia após o fim do tratamento), **RN07** (usa o fuso do agendamento, nunca o do servidor), **RN08** (sobrevive a reinicialização), **RN15** (medicamento inativo não gera lembrete), **RN18** (falha de envio não gera duplicidade)."

criar_card fechado "concluído,bot,api,regra-de-negócio" \
  "Confirmação, adiamento e registro de dose não tomada" \
  "Botões ✅ Tomei · ⏰ Mais tarde · ❌ Não tomei, e os endpoints equivalentes na API.

Regras: **RN04** (só registra com confirmação explícita), **RN05** (impede confirmação duplicada), **RN06** (o adiamento não altera o horário original). Adiamento em 5, 10, 15 ou 30 min."

criar_card fechado "concluído,api,regra-de-negócio" \
  "Histórico e relatórios de adesão declarada" \
  "Histórico filtrável por dia, semana ou mês, e relatórios em JSON ou CSV.

Regra **RN12** — a mais importante do ponto de vista clínico: **ausência de resposta não significa que o medicamento não foi tomado**. Os status \`pending\`/\`delivered\` são distintos de \`not_taken\` em todo o modelo e nos relatórios. Todo relatório é de adesão **declarada**, não real."

criar_card fechado "concluído,bot,api,segurança" \
  "Cuidadores: autorização por convite e revogação pelo paciente" \
  "O paciente autoriza um cuidador por código de convite e pode revogar a qualquer momento, sem depender de ninguém. O cuidador tem acesso **somente de leitura**.

Regra **RN14**: o acesso exige registro de autorização não revogado."

criar_card fechado "concluído,bot,acessibilidade" \
  "Mensagens de voz (TTS) com conversão para formato reproduzível no Telegram" \
  "Áudio no /start, na ajuda e, opcionalmente, em toda confirmação de ação. Também é possível definir um texto falado por medicamento.

Detalhe que importa: o pyttsx3 gera \`.aiff\`, que o Telegram **não reproduz**. O serviço converte para \`.m4a\` antes de enviar — sem isso, o recurso de acessibilidade mais importante do bot ficaria silenciosamente quebrado."

criar_card fechado "concluído,api,documentação" \
  "API REST FastAPI com OpenAPI como fonte única de verdade" \
  "Regra **RF14**: \`docs/openapi.yaml\` é exportado do mesmo schema que alimenta \`/openapi.json\`, \`/docs\` e \`/redoc\` (via \`scripts/export_openapi.py\`). Não existe uma segunda descrição da API para sair de sincronia."

criar_card fechado "concluído,api,segurança,regra-de-negócio" \
  "Isolamento de dados por usuário na API" \
  "Regra **RN09**: toda rota filtra pelo usuário autenticado (\`Medication.user_id == user.id\`, ou equivalente via \`ReminderEvent\` → \`Medication\`). Nenhum usuário alcança dado de outro."

criar_card fechado "concluído,portal,segurança" \
  "Autenticação de profissionais com MFA TOTP obrigatório" \
  "Login em duas etapas (**RF01**): a senha devolve apenas um \`pre_auth_token\` de 5 min carimbado com a finalidade; a sessão só é emitida depois do código TOTP. QR Code exibido no primeiro acesso.

Regras **RN19** (autenticação totalmente separada da do paciente, com segredo próprio) e **RN30** (token de sessão opaco, persistido só como hash, revogável no servidor; bloqueio após 5 tentativas por 15 min).

Ver [Segurança e Privacidade](../../wiki/Seguranca-e-Privacidade)."

criar_card fechado "concluído,portal,segurança,regra-de-negócio" \
  "RBAC por papel e verificação de profissional pelo administrador" \
  "O papel enforçado é \`role\` (\`medico\`, \`enfermeiro\`, \`outro_profissional\`, \`admin\`); \`profession\` é texto livre e não concede permissão.

Regra **RN20**: **só \`medico\` pode ativar um tratamento** — a API responde 403 e o portal desabilita o botão **explicando o motivo em texto**.

O autocadastro é uma solicitação, não uma liberação: nasce com \`verification_status = pending\`.

Ver [Papéis e Permissões](../../wiki/Papeis-e-Permissoes)."

criar_card fechado "concluído,portal,acessibilidade,regra-de-negócio" \
  "Cadastro de pacientes e vínculo ao Telegram por convite único" \
  "**RF03**/**RF04**. Regras **RN21**/**RN22** (acesso por vínculo explícito e ativo) e **RN23**/**RN24** (convite de uso único, expira em 30 min, persistido só como hash).

Decisão de acessibilidade: o convite é entregue como **deep link nativo do Telegram** e como **QR Code** — o paciente toca no link ou aponta a câmera, sem digitar código nenhum.

O paciente é identificado por identificador interno, **nunca** por CPF ou documento."

criar_card fechado "concluído,portal,regra-de-negócio" \
  "Ciclo de vida do tratamento: rascunho → ativo → suspenso, com versionamento" \
  "**RF05**/**RF06**/**RF07**. Regras:
- **RN25** — rascunho não gera lembrete nenhum.
- **RN26** — a ativação **materializa** as entidades \`Medication\`/\`Schedule\` que o agendador já consumia; o portal **não** reimplementou o agendador.
- **RN27** — editar um tratamento ativo cria **nova versão** em vez de sobrescrever; a mesma linha de \`Medication\` é atualizada, então o histórico de \`ReminderEvent\` **não se perde**.
- **RN28** — suspender marca \`Medication.active = False\`, e o agendador já respeita isso via RN15.

A notificação ao paciente roda **após** a resposta HTTP, para não travar a requisição do profissional.

Ver [Ciclo de Vida do Tratamento](../../wiki/Ciclo-de-Vida-do-Tratamento)."

criar_card fechado "concluído,portal" \
  "Painel operacional do profissional" \
  "**RF02** do portal: pacientes, tratamentos e confirmações declaradas.

Coerente com **RN12** — o painel mostra adesão **declarada**, nunca interpreta silêncio como dose não tomada."

criar_card fechado "concluído,portal,segurança,regra-de-negócio" \
  "Trilha de auditoria restrita a administradores" \
  "Regra **RN32**: \`AuditLog\` registra ator, papel do ator, ação e momento das operações sensíveis do portal.

A consulta é exclusiva de \`admin\`. A rota expõe auditoria — **nunca** dados clínicos de pacientes."

criar_card fechado "concluído,portal,frontend" \
  "Portal web React + TypeScript + MUI com todas as telas" \
  "Login/MFA, autocadastro, recuperação de acesso, painel, pacientes (lista/cadastro/detalhe com QR Code), cadastro de tratamento, detalhe do tratamento com ativação/suspensão e versões anteriores, perfil e área administrativa.

Tema com paleta orientada a contraste WCAG AA e contorno visível de \`focus-visible\`."

criar_card fechado "concluído,portal,segurança" \
  "CORS com credenciais para o cookie de sessão httpOnly" \
  "O cookie \`httpOnly\` precisa atravessar origens diferentes (frontend em :5173, API em :8000). O \`CORSMiddleware\` usa \`allow_credentials=True\` com **lista explícita de origens** — nunca \`*\`, que é incompatível com credenciais."

criar_card fechado "concluído,portal,frontend,acessibilidade" \
  "Validação e mensagens de erro integralmente em português" \
  "Nenhuma mensagem crua de framework chega ao usuário:

- Todos os formulários validam em português **antes** de chamar a API, com \`noValidate\` (a validação nativa do navegador aparece no idioma do sistema operacional, que \`lang=\"pt-BR\"\` não controla).
- Erros do Pydantic são traduzidos **com o rótulo do campo** — ex.: *\"Senha: deve ter pelo menos 8 caracteres\"* em vez de *\"String should have at least 8 characters\"*.
- Erros do Axios (\`\"Network Error\"\`, timeouts) são substituídos por texto em português.
- Erro exibido **no próprio campo** (\`helperText\`), e alertas com \`role=\"alert\"\`."

criar_card fechado "concluído,testes" \
  "Suíte de 160 testes automatizados de backend" \
  "Cobre serviços, rotas, agendador, OCR/STT, cuidadores, autenticação do portal, pacientes, tratamentos e auditoria.

Os casos de teste são referenciados por ID (CT04, CT06, CT11, CT14, CT15, CT18…) nas tabelas de regras de negócio da wiki, para que cada regra tenha lastro verificável."

echo "==> Cards de pendência (ficam abertos)"

criar_card aberto "pendência,regra-de-negócio,api" \
  "RN17: implementar o expurgo automático da política de retenção" \
  "\`DATA_RETENTION_DAYS\` existe na configuração (padrão 365 dias), mas **nenhum job de expurgo foi implementado** — a aplicação não apaga registros antigos sozinha.

A regra está documentada e configurável, mas **não está em vigor**.

**O que falta:** um job periódico que remova registros além da janela de retenção, com teste cobrindo a borda."

criar_card aberto "pendência,regra-de-negócio,documentação" \
  "RN29 e RN31: conferir na especificação e documentar ou descartar" \
  "A numeração das regras do portal salta: **RN29 e RN31 não têm marcação em nenhum arquivo do repositório**.

Podem existir na especificação original do portal sem terem sido anotadas na implementação, ou podem não existir.

**O que falta:** conferir a especificação do portal e então (a) documentar a regra e apontar onde está implementada, ou (b) registrar que o número não é usado. A wiki deliberadamente **não inventou** o conteúdo delas."

criar_card aberto "pendência,testes,portal" \
  "Testes E2E do portal com Playwright" \
  "Não existe nenhum teste em \`frontend/\`. Playwright não foi configurado.

**Fluxos que precisam de cobertura E2E:**
- Autocadastro → login → configuração de MFA com TOTP → sessão.
- Cadastro de paciente → geração de convite → vínculo ao Telegram.
- Cadastro de tratamento (rascunho) → tentativa de ativação por não-médico (403, RN20) → ativação por médico.
- Edição de tratamento ativo gerando nova versão (RN27).
- Suspensão (RN28)."

criar_card aberto "pendência,testes,acessibilidade" \
  "Testes automatizados de acessibilidade com axe-core" \
  "As decisões de acessibilidade do portal (contraste WCAG AA, \`focus-visible\`, \`role=\"alert\"\`, erro no próprio campo, \`lang=\"pt-BR\"\`) foram tomadas na implementação, mas **não foram auditadas automaticamente**.

**O que falta:** axe-core rodando sobre as telas do portal, idealmente no mesmo pipeline do Playwright."

criar_card aberto "pendência,infra,portal" \
  "Docker: empacotar e servir o portal web" \
  "\`Dockerfile\` e \`docker-compose.yml\` **não têm nenhuma referência a Node, npm ou \`frontend/\`**. O portal web não é empacotado nem servido pela infraestrutura Docker atual.

**O que falta:** estágio de build do frontend (\`npm ci && npm run build\`), serviço que sirva os estáticos, e \`VITE_API_BASE_URL\`/\`CORS_ORIGINS\` coerentes entre os serviços do compose."

criar_card aberto "pendência,documentação" \
  "README: documentar o portal de profissionais" \
  "O \`README.md\` tem **zero ocorrências** de \"portal\" ou \"profissional\". A documentação principal descreve apenas o bot e a API.

Consequência: quem clona o repositório **não descobre que o portal existe**, nem como subi-lo.

**O que falta:** seção do portal no README — o que é, para quem, como rodar (API + frontend), variáveis de ambiente novas, e o fluxo de primeiro acesso com MFA."

criar_card aberto "pendência,documentação" \
  "Publicar a wiki no GitHub" \
  "As páginas da wiki estão versionadas em \`wiki/\` no repositório, mas a wiki do GitHub **ainda não foi inicializada** — \`hora-do-remedio.wiki.git\` não existe, então não é possível publicá-la por git.

**O que falta:** habilitar a wiki em *Settings → Features → Wikies* e criar a primeira página pela interface web. Depois disso o conteúdo de \`wiki/\` pode ser enviado por git de uma vez.

Páginas prontas: Home, Visão Geral, Requisitos Funcionais, Regras de Negócio (Bot/API e Portal), Ciclo de Vida do Tratamento, Papéis e Permissões, Segurança e Privacidade, Acessibilidade, Limitações Conhecidas."

criar_card aberto "pendência,portal,infra" \
  "Envio real de e-mail na recuperação de acesso do profissional" \
  "A recuperação **gera** o token corretamente (opaco, 30 min, encerra as sessões anteriores ao ser consumido), mas o ambiente **não envia e-mails reais** — a própria tela avisa que o token deve ser obtido com o administrador.

**O que falta:** integração de envio de e-mail. Manter a garantia atual de **não revelar se o e-mail existe** (a resposta é a mesma para e-mail cadastrado ou não)."

criar_card aberto "pendência,segurança,infra" \
  "Trocar os segredos padrão antes de qualquer uso real" \
  "\`PROFESSIONAL_SESSION_SECRET_KEY\` está com o valor padrão \`change-me-professional-session\`.

**O que falta:** gerar segredos reais por ambiente e, de preferência, falhar a inicialização se um segredo padrão for detectado fora de desenvolvimento."

criar_card aberto "pendência,testes" \
  "Reexecutar a suíte de backend após os ajustes finais" \
  "Os 160 testes de backend **não foram reexecutados** depois dos últimos ajustes de validação em português.

As alterações foram só no frontend (\`frontend/src/api/client.ts\` e as páginas de formulário), então não deveriam afetar o backend — mas a verificação não foi feita.

**O que falta:** rodar \`pytest\` e confirmar os 160 testes."

criar_card aberto "pendência,testes,frontend" \
  "Validar ao vivo os formulários de paciente e de medicamento" \
  "A validação em português foi verificada ao vivo no navegador no login, no MFA, no autocadastro e na recuperação de senha.

O **cadastro de paciente** e o **cadastro de medicamento** usam o mesmo padrão (\`noValidate\` + validação própria + \`error\`/\`helperText\`) e passam no \`tsc -b\`, mas **não foram testados ao vivo** porque exigem login com MFA.

**O que falta:** autenticar no portal e submeter os dois formulários vazios, conferindo as mensagens em português campo a campo."

criar_card aberto "pendência,infra,bot" \
  "Agendador: evitar lembretes duplicados com múltiplas instâncias" \
  "O APScheduler roda no processo do bot (é ele que tem a conexão com o Telegram). Rodar **mais de uma instância** do bot produziria lembretes duplicados — não há coordenação entre instâncias.

Hoje isso é contornado por operar em instância única, o que limita a escala e não sobrevive a um deploy sem downtime.

**O que falta:** lock distribuído ou eleição de líder antes de escalar horizontalmente."

criar_card aberto "pendência,regra-de-negócio" \
  "RN13: avaliar validação ativa de conteúdo em campos livres" \
  "A regra \"o bot não prescreve nem recomenda alterações de dosagem\" é garantida por **ausência de funcionalidade**: não existe código que sugira dosagem.

**Não** há filtro ativo — nada impede que o próprio usuário digite esse tipo de informação no campo livre de observações.

**A decidir:** se isso é aceitável (o texto é do próprio paciente, para ele mesmo) ou se merece um aviso na interface. Vale registrar a decisão em vez de deixar a lacuna implícita."

echo ""
echo "==> Concluído. Cards criados em https://github.com/$REPO/issues"
