# ==========================================
# CONFTEST - Fixtures compartilhadas dos testes
# ==========================================

import os
import sys
import tempfile

import pytest

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# O backend pode estar em backend/ ou na raiz do repositorio
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if not os.path.isfile(os.path.join(BACKEND_DIR, "main.py")):
    BACKEND_DIR = ROOT_DIR
sys.path.insert(0, BACKEND_DIR)

# Banco SQLite temporario, definido antes de importar a aplicacao
_db_dir = tempfile.mkdtemp(prefix="lumina-tests-")
os.environ["DATABASE_URL"] = f"sqlite:///{os.path.join(_db_dir, 'test.db')}"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

# Usuario demo criado por auth.create_demo_user
DEMO_USERNAME = "admin"
DEMO_PASSWORD = "admin1234"


@pytest.fixture(scope="session")
def client():
    """Cliente de teste; o lifespan cria o usuario demo (admin / admin1234)."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    resp = client.post("/api/auth/login", json={"username": DEMO_USERNAME, "password": DEMO_PASSWORD})
    assert resp.status_code == 200, resp.text
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture(scope="session")
def profile_id(client, auth_headers):
    resp = client.get("/api/profiles", headers=auth_headers)
    assert resp.status_code == 200, resp.text
    return resp.json()[0]["id"]
