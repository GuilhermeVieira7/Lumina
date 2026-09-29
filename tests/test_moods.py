# ==========================================
# TESTES - "Como estou me sentindo?" (registro de emoções)
# ==========================================

from datetime import date, datetime, timezone

from test_features import _headers, _new_family, _register


def test_mood_options_and_setting(client):
    headers, profile = _new_family(client)
    options = client.get("/api/moods/options", headers=headers).json()
    keys = [m["key"] for m in options]
    assert keys == ["feliz", "calmo", "triste", "bravo", "medo", "cansado"]
    assert all(m["icon"] and m["phrase"] and m["color"].startswith("#") for m in options)
    assert [m["key"] for m in options if not m["hard"]] == ["feliz", "calmo"]

    settings = client.get(f"/api/settings/{profile['id']}", headers=headers).json()
    assert settings["mood_checkin"] is True
    settings = client.put(f"/api/settings/{profile['id']}", headers=headers, json={"mood_checkin": False}).json()
    assert settings["mood_checkin"] is False


def test_moods_are_recorded_and_grouped_by_day(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    for mood, moment in [("feliz", "entrada"), ("triste", "entrada"), ("feliz", "livre")]:
        resp = client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": mood, "moment": moment})
        assert resp.status_code == 200, resp.text
    assert resp.json()["label"] == "Feliz" and resp.json()["icon"] == "😊" and resp.json()["moment"] == "livre"

    data = client.get(f"/api/moods/{pid}?days=7", headers=headers).json()
    assert data["total"] == 3
    assert data["hard"] == 1
    assert data["summary"][0]["key"] == "feliz" and data["summary"][0]["count"] == 2
    assert len(data["days"]) == 7
    assert data["days"][-1]["date"] == datetime.utcnow().date().isoformat()
    assert data["days"][-1]["counts"] == {"feliz": 2, "triste": 1}
    assert all(d["counts"] == {} for d in data["days"][:-1])
    assert data["items"][0]["mood"] == "feliz"  # mais recente primeiro

    bad = client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "radiante"})
    assert bad.status_code == 400
    bad = client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "feliz", "moment": "noite"})
    assert bad.status_code == 422

    pdf = client.get(f"/api/sessions/export/pdf?profile_id={pid}", headers=headers)
    assert pdf.status_code == 200 and pdf.content[:4] == b"%PDF"


def test_mood_day_follows_the_viewer_time_zone():
    from routers.moods import _local_date

    late_night = datetime(2026, 9, 29, 1, 30)  # 01:30 UTC = 22:30 do dia 28 em Brasília
    assert _local_date(late_night, 180) == date(2026, 9, 28)
    assert _local_date(late_night, 0) == date(2026, 9, 29)
    assert _local_date(late_night.replace(tzinfo=timezone.utc), 180) == date(2026, 9, 28)


def test_moods_are_private_and_deleted_with_the_child(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    other, _, _ = _register(client)
    stranger = _headers(other)
    assert client.get(f"/api/moods/{pid}", headers=stranger).status_code == 404
    assert client.post("/api/moods", headers=stranger, json={"profile_id": pid, "mood": "feliz"}).status_code == 404

    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "calmo"})
    assert client.delete(f"/api/profiles/{pid}", headers=headers).status_code == 200
    assert client.get(f"/api/moods/{pid}", headers=headers).status_code == 404
