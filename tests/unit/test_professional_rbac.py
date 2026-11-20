"""RBAC (seção 3): core.professional_security.require_roles."""

import pytest
from fastapi import HTTPException

from core.professional_security import require_roles
from database.models import Professional


def test_require_roles_allows_matching_role():
    check = require_roles("medico", "admin")
    professional = Professional(id=1, role="medico")
    assert check(professional=professional) is professional


def test_require_roles_blocks_other_role():
    check = require_roles("admin")
    professional = Professional(id=1, role="medico")
    with pytest.raises(HTTPException) as exc_info:
        check(professional=professional)
    assert exc_info.value.status_code == 403
