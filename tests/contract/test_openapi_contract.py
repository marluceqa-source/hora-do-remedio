from pathlib import Path

import yaml

DOCS_YAML_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "openapi.yaml"


def test_ct31_openapi_yaml_endpoint_returns_200(client):
    response = client.get("/openapi.yaml")
    assert response.status_code == 200


def test_ct32_validacao_do_content_type_yaml(client):
    response = client.get("/openapi.yaml")
    assert "yaml" in response.headers["content-type"]


def test_ct33_validacao_do_openapi_3_1(client):
    schema = yaml.safe_load(client.get("/openapi.yaml").text)
    assert schema["openapi"].startswith("3.1")


def test_ct34_swagger_ui_acessivel(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_ct34b_redoc_acessivel(client):
    response = client.get("/redoc")
    assert response.status_code == 200


def test_ct35_verificacao_de_autenticacao_da_api(client):
    response = client.get("/api/v1/medications")
    assert response.status_code == 401


def test_ct36_validacao_de_schemas_de_requisicao_e_resposta(client):
    schema = yaml.safe_load(client.get("/openapi.yaml").text)
    components = schema["components"]["schemas"]
    assert "MedicationCreate" in components
    assert "MedicationOut" in components
    assert "securitySchemes" in schema["components"]


def test_ct37_consistencia_entre_rotas_e_documentacao(client):
    live_schema = yaml.safe_load(client.get("/openapi.yaml").text)
    assert DOCS_YAML_PATH.exists(), "Rode scripts/export_openapi.py após alterar rotas/schemas"
    stored_schema = yaml.safe_load(DOCS_YAML_PATH.read_text(encoding="utf-8"))
    assert stored_schema == live_schema


def test_ct38_codigos_de_resposta_http(client):
    schema = yaml.safe_load(client.get("/openapi.yaml").text)
    medication_post = schema["paths"]["/api/v1/medications"]["post"]
    assert "201" in medication_post["responses"]
    assert "422" in medication_post["responses"]

    medication_delete = schema["paths"]["/api/v1/medications/{medication_id}"]["delete"]
    assert "204" in medication_delete["responses"]
