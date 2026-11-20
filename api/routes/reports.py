import csv
import io

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.report import ReportOut
from database.models import User
from services.report_service import compute_report

router = APIRouter(prefix="/api/v1/reports", tags=["Relatórios"])


@router.get(
    "",
    summary="Consulta relatórios de adesão declarada (RF10)",
    description=(
        "Retorna um resumo em JSON por padrão. Use ?format=csv para obter o relatório como arquivo CSV. "
        "Os números refletem confirmações declaradas pelo usuário, não comprovação clínica real (RN12)."
    ),
    responses={200: {"content": {"application/json": {}, "text/csv": {}}}},
)
def get_report(
    format: str = "json",
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    data = compute_report(db, user)

    if format == "csv":
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(data.keys())
        writer.writerow(data.values())
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=relatorio_hora_do_remedio.csv"},
        )

    return ReportOut(**data)
