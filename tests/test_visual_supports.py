# ==========================================
# TESTES - Apoios visuais: timer, quadro de fichas e prancha de pedidos
# ==========================================

import json
from pathlib import Path

from test_features import _headers, _new_family, _register

ROOT = Path(__file__).resolve().parent.parent


# ---- Timer visual (RF06: tempo; RF13: rotina) ----

def test_routine_item_duration(client):
    headers, profile = _new_family(client)
    item = client.post("/api/routine", headers=headers, json={
        "profile_id": profile["id"], "icon": "🪥", "label": "Escovar os dentes", "duration": 2,
    }).json()
    assert item["duration"] == 2

    item = client.put(f"/api/routine/{item['id']}", headers=headers, json={"duration": 5}).json()
    assert item["duration"] == 5
    item = client.put(f"/api/routine/{item['id']}", headers=headers, json={"duration": 0}).json()
    assert item["duration"] is None

    bad = client.post("/api/routine", headers=headers, json={
        "profile_id": profile["id"], "label": "Longo demais", "duration": 500,
    })
    assert bad.status_code == 422


def test_routine_template_has_timers(client):
    headers, profile = _new_family(client)
    items = client.post(f"/api/routine/{profile['id']}/template", headers=headers).json()
    brushing = next(i for i in items if i["label"] == "Escovar os dentes")
    assert brushing["duration"] == 2
    assert any(i["duration"] is None for i in items)


def test_activity_time_limit(client):
    headers, profile = _new_family(client)
    plan = client.get(f"/api/plans/{profile['id']}", headers=headers).json()
    assert all(p["time_limit"] == 0 for p in plan)

    updated = client.put(f"/api/plans/{profile['id']}/colors", headers=headers, json={"time_limit": 5}).json()
    assert updated["time_limit"] == 5
    assert client.put(f"/api/plans/{profile['id']}/colors", headers=headers, json={"time_limit": 99}).status_code == 422


def test_session_timed_out_keeps_answered_steps(client):
    headers, profile = _new_family(client)
    resp = client.post("/api/sessions", headers=headers, json={
        "profile_id": profile["id"], "activity_type": "colors", "level": 1,
        "total_questions": 2, "correct": 2, "incorrect": 0, "total_time": 60000,
        "timed_out": True,
        "responses": [{"question_index": i, "is_correct": True, "response_time": 1000, "attempts": 1} for i in range(2)],
    })
    assert resp.status_code == 200
    assert resp.json()["timed_out"] is True
    assert resp.json()["accuracy"] == 100


# ---- Quadro de fichas ----

def test_token_board_defaults_and_custom_rewards(client):
    headers, profile = _new_family(client)
    settings = client.get(f"/api/settings/{profile['id']}", headers=headers).json()
    assert settings["token_board"] is True
    assert len(settings["rewards"]) >= 3
    assert all(r["icon"] and r["label"] for r in settings["rewards"])

    rewards = [{"icon": "🦖", "label": "Ver o dinossauro"}, {"icon": "🧸", "label": "Brinquedo"}]
    settings = client.put(f"/api/settings/{profile['id']}", headers=headers, json={"rewards": rewards}).json()
    assert settings["rewards"] == rewards

    settings = client.put(f"/api/settings/{profile['id']}", headers=headers, json={"token_board": False}).json()
    assert settings["token_board"] is False
    assert settings["rewards"] == rewards  # desligar o quadro não apaga os prêmios

    assert client.put(f"/api/settings/{profile['id']}", headers=headers, json={"rewards": []}).status_code == 422
    blank = client.put(f"/api/settings/{profile['id']}", headers=headers, json={"rewards": [{"icon": " ", "label": "x"}]})
    assert blank.status_code == 400


def test_session_records_chosen_reward(client):
    headers, profile = _new_family(client)
    resp = client.post("/api/sessions", headers=headers, json={
        "profile_id": profile["id"], "activity_type": "shapes", "level": 1,
        "total_questions": 3, "correct": 3, "incorrect": 0, "total_time": 9000,
        "reward": "🧸 Brinquedo",
        "responses": [{"question_index": i, "is_correct": True, "response_time": 1000, "attempts": 1} for i in range(3)],
    })
    assert resp.json()["reward"] == "🧸 Brinquedo"
    listed = client.get(f"/api/sessions?profile_id={profile['id']}", headers=headers).json()
    assert listed[0]["reward"] == "🧸 Brinquedo"


# ---- Prancha de pedidos ----

def test_request_board_options(client):
    headers, profile = _new_family(client)
    options = client.get("/api/requests/options", headers=headers).json()
    keys = [o["key"] for o in options["requests"]]
    assert {"pausa", "ajuda", "agua", "banheiro", "sim", "nao"} <= set(keys)
    assert all(o["phrase"] and o["icon"] for o in options["requests"])
    assert options["rewards"]

    settings = client.get(f"/api/settings/{profile['id']}", headers=headers).json()
    assert settings["request_board"] is True
    assert settings["requests"] == keys


def test_choose_which_requests_appear(client):
    headers, profile = _new_family(client)
    settings = client.put(f"/api/settings/{profile['id']}", headers=headers,
                          json={"requests": ["nao", "agua", "pausa"]}).json()
    assert settings["requests"] == ["pausa", "agua", "nao"]  # ordem da prancha
    bad = client.put(f"/api/settings/{profile['id']}", headers=headers, json={"requests": ["voar"]})
    assert bad.status_code == 400


def test_child_requests_are_recorded_for_adults(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    for key, context in [("agua", None), ("pausa", "Cores"), ("agua", None)]:
        resp = client.post("/api/requests", headers=headers, json={"profile_id": pid, "key": key, "context": context})
        assert resp.status_code == 200
    assert resp.json()["label"] == "Água" and resp.json()["icon"] == "🥤"

    data = client.get(f"/api/requests/{pid}?days=7", headers=headers).json()
    assert data["total"] == 3
    assert data["summary"][0] == {"key": "agua", "icon": "🥤", "label": "Água", "count": 2}
    assert any(r["context"] == "Cores" for r in data["items"])

    assert client.post("/api/requests", headers=headers, json={"profile_id": pid, "key": "voar"}).status_code == 400

    pdf = client.get(f"/api/sessions/export/pdf?profile_id={pid}", headers=headers)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


def test_requests_are_private_to_authorized_adults(client):
    headers, profile = _new_family(client)
    other, _, _ = _register(client)
    stranger = _headers(other)
    assert client.get(f"/api/requests/{profile['id']}", headers=stranger).status_code == 404
    resp = client.post("/api/requests", headers=stranger, json={"profile_id": profile["id"], "key": "agua"})
    assert resp.status_code == 404


def test_deleting_child_removes_requests(client):
    headers, profile = _new_family(client)
    client.post("/api/requests", headers=headers, json={"profile_id": profile["id"], "key": "abraco"})
    assert client.delete(f"/api/profiles/{profile['id']}", headers=headers).status_code == 200
    assert client.get(f"/api/requests/{profile['id']}", headers=headers).status_code == 404


# ---- Pictogramas ----

def test_pictogram_index_is_valid_and_files_exist():
    index = json.loads((ROOT / "frontend/img/pictos/index.json").read_text(encoding="utf-8"))
    assert "ARASAAC" in index["attribution"]
    for emoji, info in index["pictos"].items():
        assert (ROOT / "frontend/img/pictos" / info["file"]).is_file(), emoji
