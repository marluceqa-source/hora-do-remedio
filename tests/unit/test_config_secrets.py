"""Recusa de segredos fracos fora de desenvolvimento (card #30).

Os segredos usados aqui são gerados na hora, nunca literais no arquivo: um literal longo
num teste é indistinguível de credencial vazada para quem (ou o que) varre o repositório.
"""

import secrets

import pytest
from pydantic import ValidationError

from core.config import MIN_SECRET_LENGTH, Settings, is_weak_secret


def forte() -> str:
    return secrets.token_urlsafe(48)


def montar(**extra) -> Settings:
    """Settings com os dois segredos explícitos.

    Passar por argumento é essencial: sem isso o `.env` da máquina entraria no teste, e o
    resultado passaria a depender de quem está rodando.
    """
    base = {"api_secret_key": forte(), "professional_session_secret_key": forte()}
    return Settings(**{**base, **extra})


# --- O reconhecedor de segredo fraco ---------------------------------------------------


@pytest.mark.parametrize(
    "valor",
    [
        "",
        "change-me",
        "change-me-professional-session",
        "troque_por_uma_chave_aleatoria_forte",
        "troque_por_outra_chave_aleatoria_forte",
        "dev-only-professional-session-secret-troque-em-producao",
        "a" * (MIN_SECRET_LENGTH - 1),
    ],
)
def test_reconhece_segredo_fraco(valor):
    assert is_weak_secret(valor) is True


def test_reconhece_segredo_forte():
    assert is_weak_secret(forte()) is False


def test_tamanho_minimo_e_a_fronteira():
    assert is_weak_secret("a" * (MIN_SECRET_LENGTH - 1)) is True
    assert is_weak_secret("a" * MIN_SECRET_LENGTH) is False


# --- Ambientes de desenvolvimento toleram exemplo --------------------------------------


@pytest.mark.parametrize("ambiente", ["development", "dev", "local", "test", "testing"])
def test_desenvolvimento_tolera_segredo_de_exemplo(ambiente):
    s = Settings(
        app_env=ambiente,
        api_secret_key="change-me",
        professional_session_secret_key="change-me-professional-session",
    )
    assert s.app_env == ambiente


def test_desenvolvimento_e_insensivel_a_caixa():
    assert Settings(app_env="Development", api_secret_key="change-me").app_env == "Development"


# --- Fora de desenvolvimento, segredo real é obrigatório -------------------------------


@pytest.mark.parametrize("ambiente", ["production", "staging", "homologacao", "prod"])
def test_fora_de_desenvolvimento_rejeita_segredo_padrao(ambiente):
    """Não é só "production": qualquer ambiente não reconhecido como dev exige segredo real."""
    with pytest.raises(ValidationError) as exc:
        montar(app_env=ambiente, api_secret_key="change-me")
    assert "API_SECRET_KEY" in str(exc.value)


def test_rejeita_placeholder_do_env_example():
    """Copiar .env.example e esquecer de editar é o descuido que motivou o card."""
    with pytest.raises(ValidationError) as exc:
        montar(
            app_env="production",
            professional_session_secret_key="troque_por_outra_chave_aleatoria_forte",
        )
    assert "PROFESSIONAL_SESSION_SECRET_KEY" in str(exc.value)


def test_rejeita_segredo_curto():
    with pytest.raises(ValidationError) as exc:
        montar(app_env="production", api_secret_key="a" * (MIN_SECRET_LENGTH - 1))
    assert str(MIN_SECRET_LENGTH) in str(exc.value)


def test_aponta_os_dois_segredos_de_uma_vez():
    """Quem está configurando deve ver tudo que falta, não um erro por vez."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            app_env="production",
            api_secret_key="change-me",
            professional_session_secret_key="change-me-professional-session",
        )
    mensagem = str(exc.value)
    assert "API_SECRET_KEY" in mensagem
    assert "PROFESSIONAL_SESSION_SECRET_KEY" in mensagem


def test_mensagem_ensina_a_gerar_o_segredo():
    with pytest.raises(ValidationError) as exc:
        montar(app_env="production", api_secret_key="change-me")
    assert "secrets.token_urlsafe" in str(exc.value)


# --- RN19: os dois segredos têm de ser diferentes --------------------------------------


def test_rejeita_segredos_iguais_mesmo_sendo_fortes():
    """RN19: reaproveitar o segredo anula a separação entre as duas autenticações."""
    mesmo = forte()
    with pytest.raises(ValidationError) as exc:
        Settings(
            app_env="production",
            api_secret_key=mesmo,
            professional_session_secret_key=mesmo,
        )
    assert "RN19" in str(exc.value)


def test_aceita_segredos_fortes_e_distintos():
    s = montar(app_env="production")
    assert is_weak_secret(s.api_secret_key) is False
    assert is_weak_secret(s.professional_session_secret_key) is False
    assert s.api_secret_key != s.professional_session_secret_key
