# ==========================================
# TESTES - Segurança do login e das senhas
# ==========================================

import secrets

from rate_limit import MAX_FAILURES
from test_features import _headers, _register

# Senha errada gerada na hora (um texto fixo aqui vira alerta falso em scanners de segredos)
WRONG = secrets.token_hex(6)


def test_too_many_wrong_passwords_are_blocked(client):
    resp, username, password = _register(client)
    for _ in range(MAX_FAILURES):
        wrong = client.post("/api/auth/login", json={"username": username, "password": WRONG})
        assert wrong.status_code == 401
    blocked = client.post("/api/auth/login", json={"username": username, "password": password})
    assert blocked.status_code == 429 and "Muitas tentativas" in blocked.json()["detail"]

    # A senha do Painel dos Adultos também tem limite
    headers = _headers(resp)
    for _ in range(MAX_FAILURES):
        assert client.post("/api/auth/verify-password", headers=headers, json={"password": WRONG}).status_code == 403
    assert client.post("/api/auth/verify-password", headers=headers, json={"password": password}).status_code == 429


def test_right_password_resets_the_count(client):
    _, username, password = _register(client)
    for _ in range(MAX_FAILURES - 1):
        client.post("/api/auth/login", json={"username": username, "password": WRONG})
    assert client.post("/api/auth/login", json={"username": username, "password": password}).status_code == 200
    for _ in range(MAX_FAILURES - 1):
        client.post("/api/auth/login", json={"username": username, "password": WRONG})
    assert client.post("/api/auth/login", json={"username": username, "password": password}).status_code == 200


def test_long_passwords_do_not_break_the_server(client):
    resp = client.post("/api/auth/register", json={"username": "senhalonga", "password": "ç" * 60, "consent": True})
    assert resp.status_code == 200
    assert client.post("/api/auth/login", json={"username": "senhalonga", "password": "ç" * 60}).status_code == 200
    assert client.post("/api/auth/login", json={"username": "admin", "password": "a" * 100}).status_code == 401
    too_long = client.post("/api/auth/register", json={"username": "senhaenorme", "password": "a" * 500, "consent": True})
    assert too_long.status_code == 422


def test_security_headers(client):
    resp = client.get("/")
    assert resp.headers["x-content-type-options"] == "nosniff"
    assert resp.headers["x-frame-options"] == "DENY"
    assert "access-control-allow-origin" not in client.get("/api/activities", headers={"Origin": "https://evil.example"}).headers
