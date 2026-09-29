# ==========================================
# TESTES DE FUMACA - API FastAPI
# ==========================================

import secrets

from ai_engine import AIEngine
from conftest import DEMO_USERNAME


def test_app_starts(client):
    resp = client.get("/api/docs")
    assert resp.status_code == 200
    assert client.get("/openapi.json").json()["info"]["title"] == "Sistema TEA - Apoio Educacional"


def test_login_returns_jwt(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == DEMO_USERNAME


def test_login_rejects_wrong_password(client):
    wrong = {"username": DEMO_USERNAME, "password": secrets.token_hex(8)}
    resp = client.post("/api/auth/login", json=wrong)
    assert resp.status_code == 401


def test_protected_route_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


def test_list_activities(client):
    resp = client.get("/api/activities")
    assert resp.status_code == 200
    types = {a["type"] for a in resp.json()}
    assert "colors" in types


def test_activity_questions(client):
    resp = client.get("/api/activities/colors/questions", params={"level": 1})
    assert resp.status_code == 200
    body = resp.json()
    assert body["activity_type"] == "colors"
    assert len(body["questions"]) > 0


def _save_session(client, headers, profile_id, activity_type, correct, total=10, response_time=1500):
    resp = client.post("/api/sessions", headers=headers, json={
        "profile_id": profile_id,
        "activity_type": activity_type,
        "level": 2,
        "total_questions": total,
        "correct": correct,
        "incorrect": total - correct,
        "total_time": response_time * total,
        "responses": [
            {"question_index": i, "is_correct": i < correct, "response_time": response_time, "attempts": 1}
            for i in range(total)
        ],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_ai_engine_needs_data_before_predicting(client, profile_id):
    from database import SessionLocal

    db = SessionLocal()
    try:
        result = AIEngine.analyze_performance(db, profile_id, "never_played")
    finally:
        db.close()
    assert result["recommendation"] == "continue"
    assert result["suggested_level"] == 1


def test_ai_engine_levels_up_on_high_accuracy(client, auth_headers, profile_id):
    from database import SessionLocal

    for _ in range(3):
        _save_session(client, auth_headers, profile_id, "shapes", correct=10)

    db = SessionLocal()
    try:
        result = AIEngine.analyze_performance(db, profile_id, "shapes")
    finally:
        db.close()
    assert result["recommendation"] == "level_up"
    assert result["suggested_level"] == 3
    assert result["avg_accuracy"] == 100.0


def test_ai_engine_steps_down_on_low_accuracy(client, auth_headers, profile_id):
    from database import SessionLocal

    for _ in range(3):
        _save_session(client, auth_headers, profile_id, "numbers", correct=2, response_time=15000)

    db = SessionLocal()
    try:
        result = AIEngine.analyze_performance(db, profile_id, "numbers")
    finally:
        db.close()
    assert result["recommendation"] == "attention"
    assert result["suggested_level"] == 1


def test_export_pdf_report(client, auth_headers, profile_id):
    _save_session(client, auth_headers, profile_id, "colors", correct=8)
    resp = client.get("/api/sessions/export/pdf", headers=auth_headers, params={"profile_id": profile_id})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")
