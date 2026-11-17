# ==========================================
# ASSISTENTE - "Pergunte à IA" do Painel dos Adultos (Google Gemini)
# ==========================================
# O adulto pergunta o que fazer para ajudar a criança. A resposta vem do Gemini,
# com os dados do Lumina como contexto. Cuidados (LGPD e RNF10):
#   - não envia o nome, a foto nem o diário da criança; só números agregados,
#     interesses, preferências sensoriais e forma de comunicação
#   - o modelo é instruído a não diagnosticar e a remeter à equipe que acompanha
#   - sem GEMINI_API_KEY (ou se o serviço falhar), responde com as regras do Lumina
#
# Configuração (.env): GEMINI_API_KEY e, opcionalmente, GEMINI_MODEL.

import http.client
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timedelta
from threading import Lock
from typing import List, Optional, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from ai_engine import HELP_LABELS, AIEngine, accuracy_of, independence_of, to_utc
from data.activity_bank import activity_name
from data.communication import MOODS_BY_KEY
from models import MoodCheck, Profile, Session

DEFAULT_MODEL = "gemini-3.5-flash"
# Se o modelo principal estiver sobrecarregado (503/429) ou lento, tenta este, mais leve
FALLBACK_MODEL = "gemini-3.1-flash-lite"
RETRY_CODES = {404, 429, 500, 502, 503, 504}  # 404: modelo aposentado
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 30
WINDOW_DAYS = 30

# Limite de perguntas por usuário (protege a cota da chave)
MAX_QUESTIONS = 20
LIMIT_WINDOW = 10 * 60
_asked = defaultdict(deque)
_lock = Lock()

SYSTEM_PROMPT = """Você é o assistente do Lumina, uma plataforma de apoio à educação de crianças autistas (TEA).
Quem pergunta é um responsável (pai, mãe, cuidador) ou um profissional (professor, terapeuta) da criança.

Como responder:
- Português do Brasil, linguagem simples e acolhedora, sem jargão (explique os termos técnicos quando usar).
- Seja prático: até 4 passos concretos em lista, que dê para fazer hoje em casa ou na escola. No máximo 220 palavras.
- Baseie as dicas em práticas com evidência para TEA: ensino estruturado (TEACCH), apoios visuais e rotina,
  Análise do Comportamento Aplicada (reforço, dicas e retirada gradual da ajuda) e Comunicação Aumentativa e Alternativa.
- Use os dados do Lumina abaixo quando ajudarem e cite os números. Se os dados forem poucos, diga isso.
- Respeite os interesses e as preferências sensoriais da criança.

Limites (obrigatórios):
- Você não faz diagnóstico, não interpreta laudos e não indica remédios nem terapias específicas.
- Se a pergunta envolver saúde, autoagressão, agressividade intensa, regressão ou sofrimento persistente,
  oriente procurar a equipe que acompanha a criança (pediatra, neurologista, terapeutas).
- As dicas complementam, e não substituem, a orientação dos profissionais da criança.
- Se a pergunta não tiver relação com a criança ou com o Lumina, diga gentilmente que só pode ajudar com isso."""


def model_name() -> str:
    return (os.getenv("GEMINI_MODEL") or "").strip() or DEFAULT_MODEL


def is_configured() -> bool:
    return bool(_api_key())


def _check_limit(user_id: int) -> None:
    now = time.monotonic()
    with _lock:
        asked = _asked[user_id]
        while asked and now - asked[0] > LIMIT_WINDOW:
            asked.popleft()
        if len(asked) >= MAX_QUESTIONS:
            raise HTTPException(status_code=429, detail="Muitas perguntas seguidas. Tente de novo em alguns minutos.")
        asked.append(now)


def _age(birth: Optional[date]) -> Optional[int]:
    if not birth:
        return None
    today = date.today()
    return today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))


def build_context(db: DBSession, profile: Profile) -> str:
    """Dados da criança para o modelo: agregados, sem nome, foto ou diário."""
    since = datetime.utcnow() - timedelta(days=WINDOW_DAYS)
    sessions = [
        s for s in db.query(Session).filter(Session.profile_id == profile.id, Session.is_practice == False)  # noqa: E712
        if s.created_at and to_utc(s.created_at) >= since
    ]
    lines = ["Dados da criança no Lumina (a criança é chamada apenas de \"a criança\"):"]
    age = _age(profile.birth_date)
    lines.append(f"- Idade: {f'{age} anos' if age is not None else 'não informada'}")
    lines.append(f"- Interesses: {profile.interests or 'não informados'}")
    lines.append(f"- Preferências sensoriais: {profile.sensory_notes or 'não informadas'}")
    lines.append(f"- Forma de comunicação: {profile.communication or 'não informada'}")

    lines.append(f"\nÚltimos {WINDOW_DAYS} dias: {len(sessions)} atividades.")
    if sessions:
        acc = accuracy_of(sessions)
        ind = independence_of(sessions)
        lines.append(f"- Acerto de primeira geral: {acc:.0f}%" if acc is not None else "- Acerto: sem dados")
        if ind is not None:
            lines.append(f"- Feitas sem ajuda (entre as sessões com ajuda registrada): {ind:.0f}%")
        by_activity = defaultdict(list)
        for s in sessions:
            by_activity[s.activity_type].append(s)
        lines.append("- Por atividade (sessões; acerto; nível atual; ajuda registrada):")
        for activity, rows in sorted(by_activity.items(), key=lambda kv: -len(kv[1])):
            rows.sort(key=lambda s: (to_utc(s.created_at), s.id))
            helps = Counter(HELP_LABELS[s.help_level] for s in rows if s.help_level in HELP_LABELS)
            help_text = ", ".join(f"{k} {v}x" for k, v in helps.most_common()) or "não registrada"
            lines.append(f"  - {activity_name(activity)}: {len(rows)}; {accuracy_of(rows):.0f}%; "
                         f"nível {rows[-1].level}; {help_text}")

    moods = [m for m in db.query(MoodCheck).filter(MoodCheck.profile_id == profile.id).all()
             if m.created_at and to_utc(m.created_at) >= since]
    if moods:
        counts = Counter(MOODS_BY_KEY[m.mood]["label"] for m in moods if m.mood in MOODS_BY_KEY)
        lines.append("- Como disse que estava (\"Como estou?\"): " + ", ".join(f"{k} {v}x" for k, v in counts.most_common()))
    mood = AIEngine.mood_performance(db, profile.id)
    if mood:
        lines.append(f"- Acerto nos dias difíceis: {mood['hard_accuracy']:.0f}%; nos outros dias: {mood['other_accuracy']:.0f}%")

    from routers.goals import goals_with_forecast  # evita import circular
    goals = [g for g in goals_with_forecast(db, profile.id) if not g["completed"]]
    if goals:
        lines.append("- Metas abertas:")
        for g in goals[:5]:
            lines.append(f"  - {activity_name(g['activity_type'])} ({g['target_type']}): {g['current_value']} de "
                         f"{g['target_value']}. {g['forecast'] or ''}")

    recs = AIEngine.generate_recommendations(db, profile.id)
    if recs:
        lines.append("- Sugestões pendentes do motor de regras do Lumina:")
        for r in recs[:5]:
            lines.append(f"  - {r['title']}: {' '.join(r['reasons'])[:300]}")
    return "\n".join(lines)


class Blocked(Exception):
    """O Gemini se recusou a responder (filtro de segurança do próprio serviço)."""


def _api_key() -> str:
    # Tolera aspas e espaços colados por engano no .env ou no painel da hospedagem
    return (os.getenv("GEMINI_API_KEY") or "").strip().strip('"').strip("'")


def _call_gemini(context: str, question: str, history: List[dict]) -> Tuple[str, str]:
    """Pergunta ao modelo configurado; se ele falhar por instabilidade, ao modelo reserva.

    Devolve (resposta, modelo que respondeu). Erros de chave (400, 401, 403) não mudam com
    outro modelo e sobem direto; um modelo aposentado (404) ou sobrecarregado tenta o reserva.
    """
    models = [model_name()] + ([FALLBACK_MODEL] if FALLBACK_MODEL != model_name() else [])
    for i, model in enumerate(models):
        last = i == len(models) - 1
        try:
            return _call_model(model, context, question, history), model
        except urllib.error.HTTPError as err:
            if err.code not in RETRY_CODES or last:
                raise
            print(f"[ASSISTENTE] {model} respondeu {err.code}; tentando {models[i + 1]}")
        except (TimeoutError, urllib.error.URLError, ConnectionError, http.client.HTTPException) as err:
            if last:
                raise
            print(f"[ASSISTENTE] {model} falhou ({type(err).__name__}); tentando {models[i + 1]}")
    raise RuntimeError("nenhum modelo disponível")  # inalcançável: o último erro sobe acima


def _call_model(model: str, context: str, question: str, history: List[dict]) -> str:
    contents = []
    for turn in history[-6:]:
        text = (turn.get("text") or "")[:1500]
        if text:
            contents.append({"role": "model" if turn.get("role") == "assistant" else "user", "parts": [{"text": text}]})
    contents.append({"role": "user", "parts": [{"text": question}]})
    body = {
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT + "\n\n" + context}]},
        "contents": contents,
        # Os modelos Gemini 3 "pensam" antes de responder e isso consome o limite de tokens:
        # raciocínio baixo basta para dicas práticas e deixa folga para a resposta.
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096, "thinkingConfig": {"thinkingLevel": "low"}},
    }
    request = urllib.request.Request(
        API_URL.format(model=urllib.parse.quote(model, safe="-._")),
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": _api_key()},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return _parse(data)


def _parse(data) -> str:
    """Extrai o texto da resposta, ignorando o raciocínio interno do modelo."""
    if not isinstance(data, dict):
        raise ValueError("formato inesperado")
    if (data.get("promptFeedback") or {}).get("blockReason"):
        raise Blocked(data["promptFeedback"]["blockReason"])
    candidates = data.get("candidates") or []
    candidate = candidates[0] if candidates and isinstance(candidates[0], dict) else {}
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict) and not p.get("thought")).strip()
    if not text:
        if candidate.get("finishReason") in ("SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"):
            raise Blocked(candidate["finishReason"])
        raise ValueError("resposta vazia")
    if candidate.get("finishReason") == "MAX_TOKENS":
        text += "\n\n_(A resposta foi resumida. Pergunte de novo, de forma mais específica, para ver o restante.)_"
    return text


def rules_answer(db: DBSession, profile: Profile, reason: str) -> str:
    """Sem o Gemini: o que as regras do Lumina sugerem agora."""
    try:
        recs = AIEngine.generate_recommendations(db, profile.id)
    except Exception as err:  # noqa: BLE001 - a resposta reserva nunca pode falhar
        print(f"[ASSISTENTE] regras indisponíveis: {type(err).__name__}")
        recs = []
    tips = [f"- **{r['title']}**: {r['reasons'][0]}" for r in recs[:3] if r.get("reasons")]
    if not tips:
        tips = ["- Ainda há poucos dados. Faça algumas atividades com a criança e registre a ajuda que ela precisou."]
    return (f"{reason} Enquanto isso, veja o que as regras do Lumina sugerem agora:\n\n"
            + "\n".join(tips)
            + "\n\nPara dúvidas sobre saúde ou comportamento, converse com a equipe que acompanha a criança.")


def _explain(err: Exception) -> str:
    """Motivo no log do servidor (sem a chave), para quem administra saber o que corrigir."""
    code = getattr(err, "code", None)
    if code in (400, 401, 403):
        return f"chave inválida, sem permissão ou sem cota (HTTP {code}). Confira a GEMINI_API_KEY."
    if code == 404:
        return f"modelo não encontrado (HTTP 404). Confira a GEMINI_MODEL ({model_name()})."
    if code == 429:
        return "limite de uso da chave atingido (HTTP 429)."
    if code:
        return f"erro do serviço (HTTP {code})."
    return f"{type(err).__name__}: {str(err)[:200]}"


def ask(db: DBSession, profile: Profile, user_id: int, question: str, history: List[dict]) -> dict:
    """Responde sempre: pelo Gemini quando possível; nas falhas, pelas regras do Lumina."""
    question = (question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Escreva uma pergunta.")
    _check_limit(user_id)
    if not is_configured():
        return {"answer": rules_answer(db, profile, "O assistente com Gemini não está configurado neste servidor."),
                "source": "regras"}
    try:
        answer, model = _call_gemini(build_context(db, profile), question, history)
        return {"answer": answer, "source": "gemini", "model": model}
    except Blocked as err:
        print(f"[ASSISTENTE] Gemini recusou a pergunta: {err}")
        return {"answer": rules_answer(db, profile, "O Gemini não pôde responder a essa pergunta."), "source": "regras"}
    except Exception as err:  # noqa: BLE001 - qualquer falha externa vira a resposta pelas regras
        db.rollback()  # se a falha veio do banco, a sessão volta a um estado usável
        print(f"[ASSISTENTE] Gemini indisponível: {_explain(err)}")
        return {"answer": rules_answer(db, profile, "O Gemini não respondeu agora."), "source": "regras"}
