# Casos de Teste — WEB (portal de profissionais)

Cenários escritos em **Gherkin**, no template padrão: **Dado** (pré-condições),
**Quando** (ações) e **Então** (pós-condições).

Aplicação sob teste: portal web de profissionais de saúde do **Hora do Remédio**
(`http://localhost:5173`), que conversa com a API em `http://localhost:8000`.

| Tela | Arquivo de automação |
| --- | --- |
| Cadastro de profissional (`/signup`) | `tests/web/cadastro-profissional.spec.js` |
| Login em duas etapas (`/login`) | `tests/web/login-portal.spec.js` |
| Cadastro de paciente (`/patients/new`) | `tests/web/cadastro-paciente.spec.js` |
| Rotas protegidas, menu e logout | `tests/web/navegacao-portal.spec.js` |

Campos do formulário de cadastro de profissional: Nome completo, E-mail, Senha, Papel,
Profissão, Número do conselho profissional e UF do conselho.

---

## Cadastro de profissional de saúde

```gherkin
Cenário: CT-WEB-C01 - Cadastro de profissional realizado com sucesso
Dado que possuo todos os dados do profissional de saúde
Quando acesso a página de cadastro do portal
E preencho o campo Nome completo
E preencho o campo E-mail com um e-mail ainda não cadastrado
E preencho o campo Senha com pelo menos 8 caracteres
E mantenho o campo Papel como "Médico(a)"
E preencho o campo Profissão
E preencho o campo Número do conselho profissional
E preencho o campo UF do conselho
E clico em "Criar conta"
Então a mensagem "Cadastro recebido! Sua conta ainda precisa ser verificada por um administrador..." será exibida
E o botão "Ir para o login" será apresentado

Cenário: CT-WEB-C02 - Cadastro recusado quando o e-mail é inválido
Dado que possuo os dados do profissional, com um e-mail sem domínio
Quando preencho o formulário de cadastro
E clico em "Criar conta"
Então a mensagem "Informe um e-mail válido" será exibida abaixo do campo E-mail
E o cadastro não será realizado

Cenário: CT-WEB-C03 - Cadastro recusado quando a senha é curta
Dado que informo uma senha com 7 caracteres
Quando clico em "Criar conta"
Então a mensagem "A senha deve ter pelo menos 8 caracteres" será exibida abaixo do campo Senha

Cenário: CT-WEB-C04 - Cadastro recusado quando os campos obrigatórios estão vazios
Dado que não preencho nenhum campo do formulário
Quando clico em "Criar conta"
Então a mensagem "Informe o nome completo" será exibida
E a mensagem "Informe um e-mail válido" será exibida
E a mensagem "A senha deve ter pelo menos 8 caracteres" será exibida
E a mensagem "Informe a profissão" será exibida

Cenário: CT-WEB-C05 - UF do conselho aceita apenas duas letras, em maiúsculas
Dado que estou na página de cadastro
Quando digito "mg" no campo UF do conselho
Então o campo exibirá "MG"
Quando limpo o campo e digito "spsp"
Então o campo exibirá apenas "SP"

Cenário: CT-WEB-C06 - Cadastro recusado quando o e-mail já está cadastrado
Dado que existe um profissional cadastrado com o e-mail informado
Quando preencho o formulário com esse mesmo e-mail
E clico em "Criar conta"
Então a mensagem "E-mail já cadastrado" será exibida no alerta do topo do formulário

Cenário: CT-WEB-C07 - Cadastro de profissional com papel de enfermeiro(a)
Dado que possuo todos os dados do profissional
Quando seleciono "Enfermeiro(a)" no campo Papel
E clico em "Criar conta"
Então a mensagem "Cadastro recebido!..." será exibida

Cenário: CT-WEB-C08 - Cadastro recusado quando o nome passa de 200 caracteres
Dado que informo um nome completo com 201 caracteres
Quando clico em "Criar conta"
Então a mensagem "Nome completo: deve ter no máximo 200 caracteres" será exibida no alerta do topo
```

---

## Login em duas etapas (senha + código do autenticador)

```gherkin
Cenário: CT-WEB-L01 - Login recusado com campos vazios
Dado que estou na página de login do portal
Quando clico em "Entrar" sem informar e-mail e senha
Então a mensagem "Preencha o e-mail e a senha." será exibida

Cenário: CT-WEB-L02 - Login recusado com senha inválida
Dado que existe um profissional cadastrado
Quando informo o e-mail correto e uma senha errada
E clico em "Entrar"
Então a mensagem "E-mail ou senha inválidos" será exibida
E continuarei na etapa de credenciais

Cenário: CT-WEB-L03 - Primeiro acesso apresenta a configuração do MFA
Dado que existe um profissional que nunca acessou o portal
Quando informo e-mail e senha corretos
E clico em "Entrar"
Então a mensagem "Primeiro acesso: configure a autenticação em duas etapas..." será exibida
E o QR Code será apresentado
E o código otpauth:// para digitação manual será apresentado
E o campo "Código de 6 dígitos" será apresentado

Cenário: CT-WEB-L04 - Código fora do formato é barrado na própria tela
Dado que estou na etapa de configuração do MFA
Quando informo "123" no campo Código de 6 dígitos
E clico em "Confirmar e entrar"
Então a mensagem "Informe o código de 6 dígitos do aplicativo autenticador." será exibida

Cenário: CT-WEB-L05 - Código de seis dígitos incorreto é recusado pelo servidor
Dado que estou na etapa de configuração do MFA
Quando informo "000000" no campo Código de 6 dígitos
E clico em "Confirmar e entrar"
Então a mensagem "Código de verificação inválido" será exibida
E permanecerei na página de login

Cenário: CT-WEB-L06 - Primeiro acesso concluído com código válido
Dado que estou na etapa de configuração do MFA
E que calculo o código TOTP a partir do segredo apresentado na tela
Quando informo esse código
E clico em "Confirmar e entrar"
Então serei levada ao painel, com o título "Dashboard"
E meu nome será apresentado no topo do portal

Cenário: CT-WEB-L07 - Segundo acesso pede apenas o código do autenticador
Dado que já concluí o primeiro acesso e configurei o MFA
Quando volto à página de login e informo e-mail e senha corretos
Então a mensagem "Digite o código do seu aplicativo autenticador." será exibida
E a tela de configuração do primeiro acesso não será apresentada
Quando informo o código válido e clico em "Entrar"
Então serei levada ao painel, com o título "Dashboard"

Cenário: CT-WEB-L08 - A tela de login dá acesso ao cadastro e à recuperação de senha
Dado que estou na página de login
Quando clico em "Criar conta"
Então serei levada à página de cadastro de profissional
Quando volto ao login e clico em "Esqueci minha senha"
Então serei levada à página de recuperação de acesso
```

---

## Cadastro de paciente (profissional autenticado)

```gherkin
Cenário: CT-WEB-P01 - Cadastro de paciente realizado com sucesso
Dado que estou autenticada no portal como profissional clínica
E que possuo os dados do paciente
Quando acesso "Cadastrar paciente"
E preencho o campo Nome completo
E preencho o campo Identificador interno com um valor ainda não usado
E preencho o campo Data de nascimento
E clico em "Cadastrar"
Então serei levada à ficha do paciente
E o nome do paciente será o título da página
E o texto "Identificador: <identificador>" será exibido
E as abas "Vínculo Telegram", "Medicamentos" e "Histórico" serão apresentadas

Cenário: CT-WEB-P02 - Cadastro de paciente recusado com campos obrigatórios vazios
Dado que estou na página de cadastro de paciente
Quando clico em "Cadastrar" sem preencher nada
Então a mensagem "Informe o nome completo" será exibida
E a mensagem "Informe o identificador interno" será exibida
E permanecerei na página de cadastro

Cenário: CT-WEB-P03 - Cadastro recusado quando o identificador interno já existe
Dado que existe um paciente cadastrado com um identificador interno
Quando cadastro outro paciente com o mesmo identificador
Então a mensagem "Já existe um paciente com este identificador interno" será exibida

Cenário: CT-WEB-P04 - Paciente cadastrado aparece na lista como não vinculado
Dado que cadastrei um paciente pela interface
Quando acesso a lista de pacientes
Então o paciente será apresentado na lista
E o identificador interno será apresentado junto ao nome
E o status "Não vinculado" será apresentado

Cenário: CT-WEB-P05 - Nome de paciente com mais de 200 caracteres é recusado
Dado que informo um nome com 201 caracteres e um identificador válido
Quando clico em "Cadastrar"
Então a mensagem "Nome completo: deve ter no máximo 200 caracteres" será exibida
E permanecerei na página de cadastro
```

---

## Rotas protegidas, navegação e encerramento de sessão

```gherkin
Cenário: CT-WEB-N01 - Rotas protegidas exigem login
Dado que não possuo sessão ativa no portal
Quando acesso "/", "/patients", "/patients/new", "/profile" ou "/admin"
Então serei redirecionada para a página de login
E o botão "Entrar" será apresentado

Cenário: CT-WEB-N02 - Dashboard apresenta os indicadores operacionais
Dado que estou autenticada no portal
Quando acesso o painel
Então os indicadores "Pacientes vinculados", "Tratamentos ativos", "Terminando em breve",
  "Lembretes enviados", "Doses confirmadas", "Doses não tomadas" e "Sem confirmação" serão apresentados
E o aviso "Não significa que não foi tomado (RN12)" será apresentado

Cenário: CT-WEB-N03 - Menu principal navega entre as áreas do portal
Dado que estou autenticada no portal
Quando clico em "Pacientes" no menu principal
Então serei levada à lista de pacientes
Quando clico em "Meu perfil"
Então serei levada à página do meu perfil
Quando clico em "Dashboard"
Então serei levada ao painel

Cenário: CT-WEB-N04 - Profissional sem papel de administrador não acessa a administração
Dado que estou autenticada com o papel "medico"
Então o item "Administração" não será apresentado no menu
Quando acesso "/admin" digitando a rota
Então serei redirecionada para o painel

Cenário: CT-WEB-N05 - Ao sair, a sessão é encerrada
Dado que estou autenticada no portal
Quando clico em "Sair" no menu principal
Então serei levada à página de login
E ao acessar "/" novamente serei redirecionada para a página de login
```
