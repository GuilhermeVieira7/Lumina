# ==========================================
# TESTES - Resumo do período (topo do Painel dos Adultos)
# ==========================================

from datetime import datetime, timedelta

from test_features import _headers, _new_family, _register, _session


def _age_sessions(profile_id, days_ago):
    """Move as sessões já gravadas desta criança para alguns dias atrás."""
    from database import SessionLocal
    from models import Session

    db = SessionLocal()
    try:
        for s in db.query(Session).filter(Session.profile_id == profile_id).all():
            s.created_at = datetime.utcnow() - timedelta(days=days_ago)
        db.commit()
    finally:
        db.close()


def test_empty_summary_suggests_starting(client):
    headers, profile = _new_family(client)
    data = client.get(f"/api/summary/{profile['id']}?days=7", headers=headers).json()
    assert data["activities"] == 0 and data["accuracy"] is None
    assert len(data["daily"]) == 7 and all(d["accuracy"] is None for d in data["daily"])
    assert "ainda não fez atividades" in data["headline"]


def test_summary_headline_compares_with_previous_period(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    # Período anterior (8 a 14 dias atrás): 40% de acerto
    _session(client, headers, pid, "numbers", correct=2)
    _session(client, headers, pid, "numbers", correct=2)
    _age_sessions(pid, 10)
    # Últimos 7 dias: Formas vai bem, Números precisa de apoio
    for _ in range(2):
        _session(client, headers, pid, "shapes", correct=5)
        _session(client, headers, pid, "numbers", correct=2)
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "triste"})
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "bravo"})
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "feliz"})

    data = client.get(f"/api/summary/{pid}?days=7", headers=headers).json()
    assert data["activities"] == 4
    assert data["accuracy"] == 70.0 and data["previous_accuracy"] == 40.0 and data["accuracy_change"] == 30.0
    assert data["minutes"] == 1 and data["stars"] > 0 and data["active_days"] == 1
    assert data["best"]["activity"] == "shapes" and data["support"]["activity"] == "numbers"
    assert data["moods"] == 3 and data["hard_days"] == 1
    assert len(data["daily"]) == 7 and data["daily"][-1]["sessions"] == 4
    headline = data["headline"]
    assert headline.startswith("Nos últimos 7 dias, Bia fez 4 atividades e acertou 70% de primeira, 30 pontos a mais")
    assert f"Foi bem em {data['best']['name']}; {data['support']['name']} precisa de mais apoio." in headline
    assert "Teve 1 dia difícil" in headline

    everything = client.get(f"/api/summary/{pid}?all_time=true", headers=headers).json()
    assert everything["activities"] == 6 and everything["accuracy_change"] is None
    assert everything["headline"].startswith("Desde o início, Bia fez 6 atividades")
    assert len(everything["daily"]) == 11  # do primeiro dia com atividade até hoje
    assert everything["daily"][0]["sessions"] == 2


def test_summary_is_private(client):
    _, profile = _new_family(client)
    other, _, _ = _register(client)
    resp = client.get(f"/api/summary/{profile['id']}", headers=_headers(other))
    assert resp.status_code == 404
