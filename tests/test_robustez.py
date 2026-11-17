# ==========================================
# TESTES - Robustez: entradas inválidas, dados antigos, criança sem dados
# e todas as formas de o Gemini falhar (sem chamar o serviço de verdade)
# ==========================================

import io
import json
import urllib.error

import pytest

import assistant
from database import SessionLocal
from models import Session
from test_features import _new_family, _session

ACT = "colors"


def _payload(pid, **over):
    base = {"profile_id": pid, "activity_type": ACT, "level": 1, "total_questions": 5,
            "correct": 3, "incorrect": 2, "total_time": 20000, "responses": []}
    base.update(over)
    return base


# ---- Sessões: dados impossíveis não entram (eles alimentam a IA) ----

@pytest.mark.parametrize("over", [
    {"correct": 6, "incorrect": 0},          # mais acertos que questões
    {"correct": 4, "incorrect": 4},          # acertos + erros > total
    {"correct": -1, "incorrect": 0},
    {"total_questions": 0, "correct": 0, "incorrect": 0},
    {"level": 11},
    {"level": 0},
    {"activity_type": "nao_existe"},
    {"responses": [{"question_index": 0, "is_correct": True, "response_time": 10, "attempts": 0}]},
])
def test_invalid_sessions_are_rejected(client, over):
    headers, profile = _new_family(client)
    resp = client.post("/api/sessions", headers=headers, json=_payload(profile["id"], **over))
    assert resp.status_code == 422, resp.text


def test_absurd_times_are_clamped_not_rejected(client):
    headers, profile = _new_family(client)
    resp = client.post("/api/sessions", headers=headers, json=_payload(
        profile["id"], total_time=10 ** 12,
        responses=[{"question_index": 0, "is_correct": True, "response_time": -5}]))
    assert resp.status_code == 200, resp.text
    assert resp.json()["total_time"] == 6 * 60 * 60 * 1000


# ---- Metas ----

@pytest.mark.parametrize("over", [
    {"target_value": 0},
    {"target_value": -5},
    {"target_type": "accuracy", "target_value": 150},
    {"activity_type": "nao_existe"},
])
def test_invalid_goals_are_rejected(client, over):
    headers, profile = _new_family(client)
    body = {"profile_id": profile["id"], "activity_type": ACT, "target_type": "sessions", "target_value": 5}
    body.update(over)
    assert client.post("/api/goals", headers=headers, json=body).status_code == 422


# ---- Criança sem nenhum dado: nada quebra ----

def test_child_without_data_everything_loads(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    headers, profile = _new_family(client)
    pid = profile["id"]
    for url in [f"/api/ai/today/{pid}", f"/api/summary/{pid}?days=7", f"/api/summary/{pid}?all_time=true",
                f"/api/ai/recommendations/{pid}", f"/api/goals/{pid}", f"/api/sessions/stats?profile_id={pid}",
                f"/api/sessions/export/pdf?profile_id={pid}"]:
        assert client.get(url, headers=headers).status_code == 200, url
    summary = client.get(f"/api/summary/{pid}?days=7", headers=headers).json()
    assert summary["independence"] is None and summary["accuracy"] is None
    ask = client.post(f"/api/ai/ask/{pid}", headers=headers, json={"question": "Por onde começo?"}).json()
    assert ask["source"] == "regras" and "não está configurado" in ask["answer"]


# ---- Dados antigos: atividade que saiu do banco de atividades ----

def test_legacy_activity_in_database_does_not_break_panel(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    _session(client, headers, pid, ACT, correct=4)
    db = SessionLocal()
    try:
        for _ in range(3):
            db.add(Session(profile_id=pid, activity_type="atividade_antiga", level=1, total_questions=4,
                           correct=4, incorrect=0, accuracy=100.0, total_time=1000, help_level="none"))
        db.commit()
    finally:
        db.close()
    for url in [f"/api/ai/today/{pid}", f"/api/summary/{pid}?days=7", f"/api/ai/recommendations/{pid}",
                f"/api/sessions/stats?profile_id={pid}", f"/api/sessions/export/pdf?profile_id={pid}"]:
        assert client.get(url, headers=headers).status_code == 200, url
    recs = client.get(f"/api/ai/recommendations/{pid}", headers=headers).json()
    assert not any(r.get("activity") == "atividade_antiga" for r in recs)


# ---- Acesso: profissional sem vínculo não usa a IA ----

def test_ai_endpoints_require_access(client):
    owner, profile = _new_family(client)
    stranger, _ = _new_family(client)
    pid = profile["id"]
    assert client.get(f"/api/ai/today/{pid}", headers=stranger).status_code in (403, 404)
    assert client.post(f"/api/ai/ask/{pid}", headers=stranger, json={"question": "oi"}).status_code in (403, 404)
    assert client.post(f"/api/ai/ask/{pid}", json={"question": "oi"}).status_code == 401


# ---- Pergunte à IA: validação e limite ----

def test_ask_validation(client):
    headers, profile = _new_family(client)
    url = f"/api/ai/ask/{profile['id']}"
    assert client.post(url, headers=headers, json={"question": "x" * 1001}).status_code == 422
    assert client.post(url, headers=headers, json={"question": "oi", "history": [{"role": "system", "text": "x"}]}).status_code == 422
    assert client.post(url, headers=headers, json={"question": "oi", "history": [{"role": "user", "text": "x"}] * 9}).status_code == 422
    assert client.post(url, headers=headers, json={"question": "   "}).status_code == 400


def test_ask_rate_limit(client, monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(assistant, "MAX_QUESTIONS", 3)
    headers, profile = _new_family(client)
    url = f"/api/ai/ask/{profile['id']}"
    codes = [client.post(url, headers=headers, json={"question": "oi"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]


# ---- Gemini: cada tipo de falha cai nas regras, nunca em erro 500 ----

class _Resp(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _ok(text="Dica 1", finish="STOP", thought=None):
    parts = ([{"text": thought, "thought": True}] if thought else []) + [{"text": text}]
    return _Resp(json.dumps({"candidates": [{"content": {"parts": parts}, "finishReason": finish}]}).encode())


def _http(code):
    return urllib.error.HTTPError("https://exemplo", code, "erro", {}, None)


@pytest.fixture
def gemini(monkeypatch, client):
    """Simula o serviço do Google: cada item da lista é a resposta (ou erro) de uma chamada."""
    monkeypatch.setenv("GEMINI_API_KEY", ' "chave-de-teste" ')
    monkeypatch.setenv("GEMINI_MODEL", "modelo-principal")
    calls = []

    def install(*outcomes):
        queue = list(outcomes)

        def fake_urlopen(request, timeout=None):
            calls.append({"url": request.full_url, "key": request.get_header("X-goog-api-key"),
                          "body": json.loads(request.data)})
            outcome = queue.pop(0)
            if isinstance(outcome, BaseException):
                raise outcome
            return outcome
        monkeypatch.setattr(assistant.urllib.request, "urlopen", fake_urlopen)
        headers, profile = _new_family(client)
        _session(client, headers, profile["id"], ACT, correct=4)
        return client.post(f"/api/ai/ask/{profile['id']}", headers=headers,
                           json={"question": "Como ajudo?", "history": [{"role": "assistant", "text": "Olá"}]})
    return install, calls


def test_gemini_success_ignores_thoughts_and_strips_key(gemini):
    install, calls = gemini
    resp = install(_ok("Resposta final", thought="raciocínio interno"))
    assert resp.status_code == 200
    assert resp.json() == {"answer": "Resposta final", "source": "gemini", "model": "modelo-principal"}
    assert calls[0]["key"] == "chave-de-teste"
    assert "modelo-principal:generateContent" in calls[0]["url"]
    roles = [c["role"] for c in calls[0]["body"]["contents"]]
    assert roles == ["model", "user"]


def test_gemini_truncated_answer_is_flagged(gemini):
    install, _ = gemini
    assert "resumida" in install(_ok("Começo", finish="MAX_TOKENS")).json()["answer"]


@pytest.mark.parametrize("first", [_http(503), _http(429), _http(404), TimeoutError(), ConnectionResetError()])
def test_gemini_falls_back_to_reserve_model(gemini, first):
    install, calls = gemini
    resp = install(first, _ok("Do reserva"))
    assert resp.json() == {"answer": "Do reserva", "source": "gemini", "model": assistant.FALLBACK_MODEL}
    assert len(calls) == 2


@pytest.mark.parametrize("code", [400, 401, 403])
def test_gemini_key_problem_goes_to_rules_without_retry(gemini, code):
    install, calls = gemini
    resp = install(_http(code))
    assert resp.status_code == 200 and resp.json()["source"] == "regras"
    assert len(calls) == 1


@pytest.mark.parametrize("outcomes", [
    (_http(503), _http(503)),
    (TimeoutError(), TimeoutError()),
    (urllib.error.URLError("sem DNS"), urllib.error.URLError("sem DNS")),
    (_Resp(b"isto nao e json"),),
    (_Resp(b"[]"),),
    (_Resp(b'{"candidates": []}'),),
    (_Resp(b'{"candidates": [null]}'),),
])
def test_gemini_failures_answer_with_rules(gemini, outcomes):
    install, _ = gemini
    resp = install(*outcomes)
    assert resp.status_code == 200
    assert resp.json()["source"] == "regras"
    assert "não respondeu agora" in resp.json()["answer"]


def test_gemini_blocked_question(gemini):
    install, _ = gemini
    blocked = _Resp(json.dumps({"promptFeedback": {"blockReason": "SAFETY"}}).encode())
    resp = install(blocked)
    assert resp.json()["source"] == "regras"
    assert "não pôde responder" in resp.json()["answer"]


# ---- Conquistas (medalhas) depois das sessões ----

def test_achievements_unlock_after_sessions(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    _session(client, headers, pid, ACT, correct=5)
    first = client.post(f"/api/achievements/check/{pid}", headers=headers)
    assert first.status_code == 200
    assert first.json()["newly_unlocked"]
    again = client.post(f"/api/achievements/check/{pid}", headers=headers).json()
    assert again["newly_unlocked"] == []
    listed = client.get(f"/api/achievements/{pid}", headers=headers)
    assert listed.status_code == 200


# ---- Previsão das metas: todos os caminhos ----

def _goal(client, headers, pid, activity, target_type, value):
    resp = client.post("/api/goals", headers=headers, json={
        "profile_id": pid, "activity_type": activity, "target_type": target_type, "target_value": value})
    assert resp.status_code == 200, resp.text


def test_goal_forecast_paths(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    _goal(client, headers, pid, "numbers", "accuracy", 100)   # acerto subindo -> previsão
    _goal(client, headers, pid, "shapes", "accuracy", 100)    # acerto parado -> devagar
    _goal(client, headers, pid, "letters", "accuracy", 100)   # menos de 3 sessões -> aguardando
    _goal(client, headers, pid, "colors", "stars", 50)        # estrelas por semana
    _goal(client, headers, pid, "clock", "sessions", 3)       # sem sessões -> aguardando
    _goal(client, headers, pid, "money", "sessions", 1)       # atingida -> concluída
    for correct in (1, 2, 3, 4):
        _session(client, headers, pid, "numbers", correct=correct)
    for _ in range(4):
        _session(client, headers, pid, "shapes", correct=3)
    _session(client, headers, pid, "letters", correct=3)
    for _ in range(2):
        _session(client, headers, pid, "colors", correct=5)
    _session(client, headers, pid, "money", correct=3)

    goals = {g["activity_type"]: g for g in client.get(f"/api/goals/{pid}", headers=headers).json()}
    assert goals["numbers"]["status"] in ("on_track", "slow") and "No ritmo atual" in goals["numbers"]["forecast"]
    assert goals["shapes"]["status"] == "slow" and "estável" in goals["shapes"]["forecast"]
    assert goals["letters"]["status"] == "waiting"
    assert goals["colors"]["status"] in ("on_track", "slow") and "meta" in goals["colors"]["forecast"]
    assert goals["clock"]["status"] == "waiting"
    assert goals["money"]["status"] == "done" and goals["money"]["completed"] is True
