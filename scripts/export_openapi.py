"""Gera docs/openapi.yaml a partir do schema OpenAPI efetivamente servido pela API.

Execute após qualquer alteração de rotas ou schemas Pydantic para manter a
documentação sincronizada com a implementação (RF14 — única fonte de verdade):

    python scripts/export_openapi.py
"""

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.main import app  # noqa: E402


def main() -> None:
    schema = app.openapi()
    output_path = Path(__file__).resolve().parent.parent / "docs" / "openapi.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(yaml.safe_dump(schema, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"OpenAPI YAML exportado para {output_path}")


if __name__ == "__main__":
    main()
