import logging

import yaml
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from api.routes import (
    admin,
    auth,
    caregivers,
    dashboard,
    history,
    medications,
    patients,
    professional_auth,
    reminders,
    reports,
    schedules,
    treatment_medications,
)
from core.config import get_settings
from core.logging_config import configure_logging

settings = get_settings()
configure_logging()
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.rate_limit_per_minute}/minute"])

app = FastAPI(
    title="Hora do Remédio API",
    version="1.0.0",
    description=(
        "API REST do **Hora do Remédio**: cadastro de medicamentos, agendamentos, lembretes, "
        "histórico e relatórios de adesão declarada.\n\n"
        "O bot não prescreve nem recomenda alterações de dosagem (RN13), e a confirmação de "
        "administração representa uma informação declarada pelo usuário, não uma comprovação "
        "clínica real (RF07, RN12)."
    ),
    contact={"name": "Hora do Remédio"},
    servers=[{"url": f"http://localhost:{settings.api_port}", "description": "Desenvolvimento local"}],
    openapi_tags=[
        {"name": "Saúde", "description": "Verificação do estado do serviço."},
        {"name": "Autenticação", "description": "Emissão de tokens de acesso à API, independentes do token do bot."},
        {"name": "Medicamentos", "description": "Cadastro, consulta, atualização e exclusão de medicamentos."},
        {"name": "Agendamentos", "description": "Consulta dos horários configurados para cada medicamento."},
        {"name": "Lembretes", "description": "Lembretes do dia, confirmação de administração e adiamento."},
        {"name": "Histórico", "description": "Consulta de doses programadas, confirmadas e não confirmadas."},
        {"name": "Relatórios", "description": "Relatórios de adesão declarada, em JSON ou CSV."},
        {"name": "Cuidadores", "description": "Autorização, listagem e revogação de acesso de cuidadores."},
        {
            "name": "Portal — Autenticação",
            "description": "Cadastro, login em duas etapas (senha + MFA), sessão por cookie e recuperação de acesso para profissionais de saúde.",
        },
        {
            "name": "Portal — Pacientes",
            "description": "Cadastro de pacientes e geração de convites para vincular o paciente ao bot do Telegram.",
        },
        {
            "name": "Portal — Tratamentos",
            "description": "Edição, ativação, suspensão e histórico de versões de esquemas terapêuticos.",
        },
        {
            "name": "Portal — Dashboard",
            "description": "Painel operacional: pacientes, tratamentos e confirmações declaradas.",
        },
        {
            "name": "Portal — Administração",
            "description": "Verificação de profissionais e consulta à trilha de auditoria (admin).",
        },
    ],
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
# allow_credentials=True é obrigatório para o cookie de sessão do portal (RF01) chegar nas
# chamadas do frontend — por isso allow_origins não pode ser "*", precisa listar as origens.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({"detail": exc.errors(), "code": "validation_error"}),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro não tratado ao processar %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor", "code": "internal_error"},
    )


app.include_router(auth.router)
app.include_router(medications.router)
app.include_router(schedules.router)
app.include_router(reminders.router)
app.include_router(history.router)
app.include_router(reports.router)
app.include_router(caregivers.router)
app.include_router(professional_auth.router)
app.include_router(patients.router)
app.include_router(treatment_medications.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health", tags=["Saúde"], summary="Verifica o estado do serviço")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


@app.get(
    "/openapi.yaml",
    include_in_schema=False,
    summary="Especificação OpenAPI em YAML",
)
def openapi_yaml() -> Response:
    # Serializa o MESMO schema usado em /openapi.json, /docs e /redoc — fonte única de verdade (RF14).
    schema = app.openapi()
    return Response(
        content=yaml.safe_dump(schema, allow_unicode=True, sort_keys=False),
        media_type="application/yaml",
    )
