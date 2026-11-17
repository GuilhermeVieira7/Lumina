# ==========================================
# TESTES - Medição do progresso pela IA (nível de ajuda, emoções, Hoje, metas, assistente)
# ==========================================

from datetime import datetime, timedelta

from database import SessionLocal
from models import MoodCheck, Session
from test_features import _new_family, _session


def _help(client, headers, session_id, level):
    resp = client.patch(f"/api/sessions/{session_id}", headers=headers, json={"help_level": level})
    assert resp.status_code == 200, resp.text


def _move_to_past(model, ids, days):
    db = SessionLocal()
    try:
        for row in db.query(model).filter(model.id.in_(ids)):
            row.created_at = datetime.utcnow() - timedelta(days=days)
        db.commit()
    finally:
        db.close()


# ---- RF07 + RF08: domínio só conta sem gesto ou ajuda física ----

def test_mastery_with_physical_help_suggests_fading_not_level_up(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    for _ in range(3):
        s = _session(client, headers, pid, "shapes", correct=5)
        _help(client, headers, s["id"], "physical")

    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    assert not any(r["kind"] == "level" and r["activity"] == "shapes" for r in recs)
    fade = next(r for r in recs if r["key"] == "help:shapes:fade")
    assert "ajuda física" in fade["reasons"][0]

    # Retirada a ajuda, volta a sugerir a subida de nível
    for _ in range(3):
        s = _session(client, headers, pid, "shapes", correct=5)
        _help(client, headers, s["id"], "none")
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    assert any(r["kind"] == "level" and r["activity"] == "shapes" and r["suggested_level"] == 2 for r in recs)


def test_summary_reports_independence(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    for level in ["none", "none", "verbal", "physical"]:
        s = _session(client, headers, pid, "colors", correct=4)
        _help(client, headers, s["id"], level)
    _session(client, headers, pid, "colors", correct=4)  # sem ajuda registrada

    summary = client.get(f"/api/summary/{pid}?days=7", headers=headers).json()
    assert summary["independence"] == 50.0
    assert summary["help_counts"] == {"none": 2, "verbal": 1, "gesture": 0, "physical": 1}
    assert summary["help_unregistered"] == 1
    assert "sem ajuda 50%" in summary["headline"]
    assert sum(sum(d["help"].values()) for d in summary["daily"]) == 4


# ---- Emoções ("Como estou?") x desempenho ----

def test_hard_days_with_lower_accuracy_raise_alert(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    good = [_session(client, headers, pid, "numbers", correct=5)["id"] for _ in range(3)]
    _move_to_past(Session, good, 3)
    for _ in range(2):
        _session(client, headers, pid, "numbers", correct=1)
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "cansado"})

    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    mood = next(r for r in recs if r["key"] == "mood:hard_days")
    assert "cansado" in mood["reasons"][0] and "20%" in mood["reasons"][0]

    # Descartado, só volta depois de uma sessão nova
    client.post(f"/api/ai/recommendations/{pid}/decide", headers=headers,
                json={"key": "mood:hard_days", "activity_type": None, "action": "dismiss"})
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    assert "mood:hard_days" not in {r["key"] for r in recs}


# ---- Aba Hoje ----

def test_today_plan_alerts_and_mood(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "triste"})
    _session(client, headers, pid, "colors", correct=5)

    today = client.get(f"/api/ai/today/{pid}", headers=headers).json()
    assert today["mood"]["key"] == "triste" and today["mood"]["hard"] is True
    assert today["sessions_today"] == 1
    assert 1 <= len(today["plan"]) <= 3
    assert all(item["tip"] and item["reasons"] for item in today["plan"])
    assert "configured" in today["assistant"]

    outsider, _ = _new_family(client)
    assert client.get(f"/api/ai/today/{pid}", headers=outsider).status_code in (403, 404)


# ---- Metas com previsão ----

def test_goal_forecast(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    client.post("/api/goals", headers=headers, json={
        "profile_id": pid, "activity_type": "letters", "target_type": "sessions", "target_value": 20})
    client.post("/api/goals", headers=headers, json={
        "profile_id": pid, "activity_type": "money", "target_type": "sessions", "target_value": 5})
    for _ in range(4):
        _session(client, headers, pid, "letters", correct=3)
    old = _session(client, headers, pid, "money", correct=3)
    _move_to_past(Session, [old["id"]], 10)

    goals = {g["activity_type"]: g for g in client.get(f"/api/goals/{pid}", headers=headers).json()}
    assert goals["letters"]["status"] == "on_track"
    assert "semana" in goals["letters"]["forecast"]
    assert goals["money"]["status"] == "stalled"


# ---- Pergunte à IA ----

def test_ask_without_gemini_key_uses_rules(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    headers, profile = _new_family(client)
    resp = client.post(f"/api/ai/ask/{profile['id']}", headers=headers,
                       json={"question": "Como ajudo nas cores?"})
    assert resp.status_code == 200
    assert resp.json()["source"] == "regras"
    assert client.post(f"/api/ai/ask/{profile['id']}", headers=headers, json={"question": ""}).status_code == 422


def test_ask_context_has_no_child_name(client, monkeypatch):
    import assistant

    headers, profile = _new_family(client)
    _session(client, headers, profile["id"], "colors", correct=4)
    sent = {}

    def fake_call(context, question, history):
        sent["context"] = context
        return "Resposta de teste"

    monkeypatch.setenv("GEMINI_API_KEY", "teste")
    monkeypatch.setattr(assistant, "_call_gemini", fake_call)
    resp = client.post(f"/api/ai/ask/{profile['id']}", headers=headers,
                       json={"question": "O que fazer?", "history": [{"role": "user", "text": "oi"}]})
    assert resp.json() == {"answer": "Resposta de teste", "source": "gemini", "model": assistant.model_name()}
    assert profile["name"] not in sent["context"]
    assert "dinossauros" in sent["context"] and "Cores" in sent["context"]
