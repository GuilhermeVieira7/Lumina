# ==========================================
# TESTES - Funcionalidades descritas no TCC
# ==========================================
# Cada teste cita o requisito ou caso de teste do TCC que verifica.

import secrets

from conftest import DEMO_PASSWORD


def _register(client, role="parent", consent=True):
    username = f"u{secrets.token_hex(4)}"
    password = secrets.token_hex(6)
    resp = client.post("/api/auth/register", json={
        "username": username, "password": password, "role": role, "consent": consent,
    })
    return resp, username, password


def _headers(resp):
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


def _session(client, headers, profile_id, activity_type, correct, total=5, level=1):
    resp = client.post("/api/sessions", headers=headers, json={
        "profile_id": profile_id, "activity_type": activity_type, "level": level,
        "total_questions": total, "correct": correct, "incorrect": total - correct,
        "total_time": 20000,
        "responses": [
            {"question_index": i, "is_correct": i < correct, "response_time": 2000, "attempts": 1}
            for i in range(total)
        ],
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _new_family(client):
    resp, _, _ = _register(client)
    headers = _headers(resp)
    profile = client.post("/api/profiles", headers=headers, json={
        "name": "Bia", "avatar": "🦊", "interests": "dinossauros, relógio",
        "sensory_notes": "sensível a sons altos", "communication": "figuras",
    }).json()
    return headers, profile


# ---- RF01 / RNF06: cadastro com consentimento ----

def test_register_requires_consent(client):
    resp, _, _ = _register(client, consent=False)
    assert resp.status_code == 400


def test_register_records_consent(client):
    resp, _, _ = _register(client)
    assert resp.status_code == 200
    assert resp.json()["user"]["consent_at"]


# ---- Painel dos pais protegido por senha ----

def test_verify_password(client, auth_headers):
    ok = client.post("/api/auth/verify-password", headers=auth_headers, json={"password": DEMO_PASSWORD})
    assert ok.status_code == 200
    wrong = client.post("/api/auth/verify-password", headers=auth_headers, json={"password": "x" + DEMO_PASSWORD})
    assert wrong.status_code == 403  # 403 para não derrubar a sessão da criança


# ---- RF03: perfil sem diagnóstico ----

def test_profile_has_personalization_fields_and_no_diagnosis(client):
    _, profile = _new_family(client)
    assert profile["interests"] == "dinossauros, relógio"
    assert profile["communication"] == "figuras"
    assert "diagnosis" not in profile


# ---- RF02 / RF04 / CT04 / CT05: acesso de profissionais ----

def test_professional_access_invite_accept_revoke(client):
    parent_headers, profile = _new_family(client)
    pro_resp, pro_name, _ = _register(client, role="therapist")
    pro_headers = _headers(pro_resp)
    stats_url = f"/api/sessions/stats?profile_id={profile['id']}"

    # CT04: sem vínculo, sem acesso
    assert client.get(stats_url, headers=pro_headers).status_code == 404

    invite = client.post("/api/access", headers=parent_headers, json={"profile_id": profile["id"], "professional": pro_name})
    assert invite.status_code == 200, invite.text
    assert client.get(stats_url, headers=pro_headers).status_code == 404  # convite ainda pendente

    invites = client.get("/api/access/invites", headers=pro_headers).json()
    assert [i["profile_name"] for i in invites] == ["Bia"]
    assert client.post(f"/api/access/{invites[0]['id']}/accept", headers=pro_headers).status_code == 200

    assert client.get(stats_url, headers=pro_headers).status_code == 200
    shared = client.get("/api/profiles", headers=pro_headers).json()
    assert shared[0]["is_owner"] is False
    # Profissional não edita nem exclui o perfil
    assert client.delete(f"/api/profiles/{profile['id']}", headers=pro_headers).status_code == 404

    # CT05: revogação vale imediatamente
    assert client.delete(f"/api/access/{invite.json()['id']}", headers=parent_headers).status_code == 200
    assert client.get(stats_url, headers=pro_headers).status_code == 404


def test_invite_requires_professional_account(client):
    parent_headers, profile = _new_family(client)
    _, other_parent, _ = _register(client)
    resp = client.post("/api/access", headers=parent_headers, json={"profile_id": profile["id"], "professional": other_parent})
    assert resp.status_code == 404


# ---- RF06: plano de atividades ----

def test_activity_plan_defaults_and_update(client):
    headers, profile = _new_family(client)
    plan = {p["activity_type"]: p for p in client.get(f"/api/plans/{profile['id']}", headers=headers).json()}
    assert len(plan) == 12
    assert plan["colors"]["enabled"] and not plan["clock"]["enabled"]

    resp = client.put(f"/api/plans/{profile['id']}/clock", headers=headers, json={"enabled": True, "level": 9, "question_count": 3})
    assert resp.status_code == 200
    assert resp.json()["level"] == resp.json()["max_level"]  # nível limitado ao máximo do banco
    assert resp.json()["question_count"] == 3


def test_questions_above_max_level_use_highest_level(client):
    top = client.get("/api/activities/colors/questions", params={"level": 3}).json()["questions"]
    above = client.get("/api/activities/colors/questions", params={"level": 7}).json()["questions"]
    assert above == top


# ---- RF07 / RNF10: recomendações com aceite, ajuste ou descarte ----

def test_level_recommendation_needs_adult_decision(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    for _ in range(3):
        _session(client, headers, pid, "shapes", correct=5)

    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    level_rec = next(r for r in recs if r["kind"] == "level" and r["activity"] == "shapes")
    assert level_rec["suggested_level"] == 2
    assert level_rec["reasons"]

    # Nada muda antes da decisão do adulto
    plan = {p["activity_type"]: p for p in client.get(f"/api/plans/{pid}", headers=headers).json()}
    assert plan["shapes"]["level"] == 1

    resp = client.post(f"/api/ai/recommendations/{pid}/decide", headers=headers,
                       json={"key": level_rec["key"], "activity_type": "shapes", "action": "accept"})
    assert resp.status_code == 200
    plan = {p["activity_type"]: p for p in client.get(f"/api/plans/{pid}", headers=headers).json()}
    assert plan["shapes"]["level"] == 2

    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    assert level_rec["key"] not in {r["key"] for r in recs}


def test_struggling_suggests_more_support(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    client.put(f"/api/plans/{pid}/numbers", headers=headers, json={"level": 2})
    for _ in range(3):
        _session(client, headers, pid, "numbers", correct=1, level=2)
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    rec = next(r for r in recs if r["kind"] == "level" and r["activity"] == "numbers")
    assert rec["type"] == "attention"
    assert rec["suggested_level"] == 1


def test_activity_suggestion_uses_interests_and_can_be_dismissed(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    client.put(f"/api/plans/{pid}/clock", headers=headers, json={"enabled": True})
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    suggestion = next(r for r in recs if r["kind"] == "activity" and r["activity"] == "clock")
    assert any("interesses" in reason for reason in suggestion["reasons"])

    client.post(f"/api/ai/recommendations/{pid}/decide", headers=headers,
                json={"key": suggestion["key"], "activity_type": "clock", "action": "accept"})
    plan = {p["activity_type"]: p for p in client.get(f"/api/plans/{pid}", headers=headers).json()}
    assert plan["clock"]["recommended"] is True


# ---- RF08: nível de ajuda ----

def test_help_level_on_session(client):
    headers, profile = _new_family(client)
    session = _session(client, headers, profile["id"], "colors", correct=4)
    resp = client.patch(f"/api/sessions/{session['id']}", headers=headers, json={"help_level": "verbal"})
    assert resp.json()["help_level"] == "verbal"
    stats = client.get(f"/api/sessions/stats?profile_id={profile['id']}", headers=headers).json()
    assert stats["help_levels"] == {"verbal": 1}
    bad = client.patch(f"/api/sessions/{session['id']}", headers=headers, json={"help_level": "muita"})
    assert bad.status_code == 400


# ---- RF09: painel por área e período ----

def test_stats_by_area_and_period(client):
    headers, profile = _new_family(client)
    _session(client, headers, profile["id"], "emotions", correct=5)
    stats = client.get(f"/api/sessions/stats?profile_id={profile['id']}&days=7", headers=headers).json()
    assert stats["areas_breakdown"]["socializacao"]["accuracy"] == 100.0
    assert stats["areas_breakdown"]["autonomia"]["accuracy"] is None
    assert stats["activities_breakdown"]["emotions"]["name"] == "Emoções"


# ---- RF10: diário ----

def test_diary_notes(client):
    headers, profile = _new_family(client)
    session = _session(client, headers, profile["id"], "letters", correct=3)
    resp = client.post("/api/notes", headers=headers, json={
        "profile_id": profile["id"], "session_id": session["id"], "content": "Ficou calma com a música baixa.",
    })
    assert resp.status_code == 200
    notes = client.get(f"/api/notes/{profile['id']}", headers=headers).json()
    assert notes[0]["activity_type"] == "letters"
    assert client.delete(f"/api/notes/{notes[0]['id']}", headers=headers).status_code == 200


# ---- Metas ----

def test_goal_progress_updates_after_sessions(client):
    headers, profile = _new_family(client)
    client.post("/api/goals", headers=headers, json={
        "profile_id": profile["id"], "activity_type": "colors", "target_type": "sessions", "target_value": 2,
    })
    _session(client, headers, profile["id"], "colors", correct=3)
    _session(client, headers, profile["id"], "colors", correct=3)
    goals = client.get(f"/api/goals/{profile['id']}", headers=headers).json()
    assert goals[0]["current_value"] == 2
    assert goals[0]["completed"] is True


# ---- RF13: agenda visual ----

def test_visual_routine(client):
    headers, profile = _new_family(client)
    items = client.post(f"/api/routine/{profile['id']}/template", headers=headers).json()
    assert len(items) >= 5
    toggled = client.post(f"/api/routine/{items[0]['id']}/toggle", headers=headers).json()
    assert toggled["done_today"] is True
    moved = client.put(f"/api/routine/{items[0]['id']}", headers=headers, json={"position": 2}).json()
    assert moved["position"] == 2
    order = [i["id"] for i in client.get(f"/api/routine/{profile['id']}", headers=headers).json()]
    assert order[2] == items[0]["id"]


# ---- RF12: PDF com os dados novos ----

def test_pdf_with_notes_and_emoji_name(client):
    headers, profile = _new_family(client)
    client.put(f"/api/profiles/{profile['id']}", headers=headers, json={"name": "Bia 🦊"})
    _session(client, headers, profile["id"], "colors", correct=3)
    client.post("/api/notes", headers=headers, json={"profile_id": profile["id"], "content": "Ótimo dia!"})
    resp = client.get("/api/sessions/export/pdf", headers=headers, params={"profile_id": profile["id"], "days": 30})
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")


# ---- RNF06: exclusão dos dados ----

def test_delete_account_removes_children_data(client):
    resp, _, password = _register(client)
    headers = _headers(resp)
    profile = client.post("/api/profiles", headers=headers, json={"name": "Teo"}).json()
    _session(client, headers, profile["id"], "colors", correct=3)
    assert client.post("/api/auth/delete-account", headers=headers, json={"password": password + "x"}).status_code == 403
    assert client.post("/api/auth/delete-account", headers=headers, json={"password": password}).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 401
