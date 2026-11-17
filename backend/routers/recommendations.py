# ==========================================
# ROUTER: Recomendações IA
# ==========================================

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

import assistant
from database import get_db
from data.activity_bank import ACTIVITY_BANK, activity_name
from data.communication import MOODS_BY_KEY
from models import ActivityPlan, MoodCheck, User, RecommendationDecision, Session
from routers.goals import goals_with_forecast
from routers.moods import _local_date
from routers.plans import get_or_create_plan
from schemas import AIAnalysis, AskIn, ErrorPattern, Recommendation, RecommendationDecisionIn
from auth import get_current_user
from permissions import get_profile_for
from ai_engine import HELP_LABELS, AIEngine

router = APIRouter(prefix="/api/ai", tags=["Inteligência Artificial"])


@router.get("/analyze/{profile_id}/{activity_type}", response_model=AIAnalysis)
def analyze_performance(
    profile_id: int,
    activity_type: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Análise de desempenho IA para uma atividade específica."""
    get_profile_for(db, profile_id, current_user)

    result = AIEngine.analyze_performance(db, profile_id, activity_type)
    return AIAnalysis(**result)


@router.get("/patterns/{profile_id}/{activity_type}", response_model=List[ErrorPattern])
def get_error_patterns(
    profile_id: int,
    activity_type: str,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Identificar padrões de erro em uma atividade."""
    get_profile_for(db, profile_id, current_user)

    patterns = AIEngine.identify_error_patterns(db, profile_id, activity_type)
    return [ErrorPattern(**p) for p in patterns]


@router.get("/recommendations/{profile_id}", response_model=List[Recommendation])
def get_recommendations(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Recomendações pendentes, cada uma com os motivos que a produziram."""
    get_profile_for(db, profile_id, current_user)
    recs = AIEngine.generate_recommendations(db, profile_id)
    return [Recommendation(**r) for r in recs]


@router.post("/recommendations/{profile_id}/decide")
def decide_recommendation(
    profile_id: int,
    decision: RecommendationDecisionIn,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Aceitar, ajustar ou descartar uma recomendação (supervisão humana, RNF10).

    - nível: aceitar aplica o nível sugerido; ajustar aplica o nível escolhido pelo adulto
    - próxima atividade: aceitar ou ajustar destaca a atividade no menu da criança
    - padrões: aceitar só registra que o adulto está ciente
    """
    get_profile_for(db, profile_id, current_user)
    if decision.action not in ("accept", "adjust", "dismiss"):
        raise HTTPException(status_code=400, detail="Ação inválida")

    kind = decision.key.split(":", 1)[0]
    activity = decision.activity_type
    if kind in ("level", "activity") and activity not in ACTIVITY_BANK:
        raise HTTPException(status_code=400, detail="Atividade inválida")

    applied_level = None
    if decision.action != "dismiss" and kind in ("level", "activity"):
        plan = get_or_create_plan(db, profile_id, activity)
        if kind == "level":
            suggested = int(decision.key.split(":")[2])
            applied_level = decision.level if decision.action == "adjust" and decision.level else suggested
            plan.level = applied_level
        else:
            plan.recommended = True
            plan.enabled = True
            if decision.action == "adjust" and decision.level:
                plan.level = decision.level
                applied_level = decision.level

    last_session_id = db.query(func.max(Session.id)).filter(Session.profile_id == profile_id).scalar() or 0
    db.add(RecommendationDecision(
        profile_id=profile_id,
        rec_key=decision.key,
        activity_type=activity,
        action=decision.action,
        level=applied_level,
        decided_by=current_user.id,
        last_session_id=last_session_id,
    ))
    db.commit()
    return {"ok": True, "action": decision.action, "level": applied_level}


# ---------- Hoje: o que fazer agora, num lugar só ----------

def _support_tip(analysis: dict, last_help: str, tried: bool) -> str:
    if not tried:
        return "Primeira vez: faça junto, mostrando como responder, e elogie cada tentativa."
    if analysis["recommendation"] == "attention":
        return "Está difícil: ofereça dica verbal ou gesto antes do erro e use o Modo Baixo Estímulo."
    if analysis["recommendation"] == "fade_help":
        return f"Da última vez precisou de {HELP_LABELS.get(last_help, 'ajuda')}: tente um nível de ajuda a menos."
    if analysis["recommendation"] == "level_up":
        return "Está dominando: veja a sugestão de subir de nível na aba Sugestões."
    return "Deixe tentar sem ajuda primeiro; ajude só se travar."


@router.get("/today/{profile_id}")
def today(
    profile_id: int,
    tz: int = Query(0, ge=-840, le=840),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Plano do dia montado pelo motor de regras, alertas e metas (aba "Hoje")."""
    profile = get_profile_for(db, profile_id, current_user)
    today_date = _local_date(datetime.utcnow(), tz)

    mood = None
    last_mood = (db.query(MoodCheck).filter(MoodCheck.profile_id == profile_id)
                 .order_by(desc(MoodCheck.created_at), desc(MoodCheck.id)).first())
    if last_mood and _local_date(last_mood.created_at, tz) == today_date and last_mood.mood in MOODS_BY_KEY:
        option = MOODS_BY_KEY[last_mood.mood]
        mood = {"key": last_mood.mood, "label": option["label"], "icon": option["icon"], "hard": option["hard"]}

    done_today = [
        s for s in db.query(Session).filter(Session.profile_id == profile_id, Session.is_practice == False)  # noqa: E712
        .order_by(desc(Session.created_at)).limit(50)
        if _local_date(s.created_at, tz) == today_date
    ]

    plans = {p.activity_type: p for p in db.query(ActivityPlan).filter(ActivityPlan.profile_id == profile_id)}
    scored = AIEngine.score_activities(db, profile)
    # Num dia difícil, priorizar o que a criança já faz bem (sucesso e previsibilidade)
    if mood and mood["hard"]:
        def known_first(item):
            a = AIEngine.analyze_performance(db, profile_id, item["activity"])
            return (a["avg_accuracy"] or 0) >= 70
        scored.sort(key=lambda i: (not known_first(i), -i["score"]))

    plan = []
    for item in scored[:3]:
        activity = item["activity"]
        analysis = AIEngine.analyze_performance(db, profile_id, activity)
        last = (db.query(Session).filter(Session.profile_id == profile_id, Session.activity_type == activity,
                                         Session.is_practice == False)  # noqa: E712
                .order_by(desc(Session.created_at), desc(Session.id)).first())
        reasons = item["reasons"] or ["Mantém a variedade das atividades"]
        if mood and mood["hard"] and (analysis["avg_accuracy"] or 0) >= 70:
            reasons = ["Já conhece bem: boa escolha para um dia difícil"] + reasons
        plan.append({
            "activity": activity,
            "name": activity_name(activity),
            "level": plans[activity].level if activity in plans else 1,
            "reasons": reasons,
            "tip": _support_tip(analysis, last.help_level if last else None, last is not None),
            "done_today": any(s.activity_type == activity for s in done_today),
        })

    recs = AIEngine.generate_recommendations(db, profile_id)
    alerts = [r for r in recs if r["kind"] != "activity"][:3]
    goals = [g for g in goals_with_forecast(db, profile_id) if not g["completed"]]

    return {
        "mood": mood,
        "sessions_today": len(done_today),
        "plan": plan,
        "alerts": alerts,
        "pending": len(recs),
        "goals": goals[:4],
        "assistant": {"configured": assistant.is_configured(), "model": assistant.model_name()},
    }


@router.post("/ask/{profile_id}")
def ask(
    profile_id: int,
    payload: AskIn,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Pergunte à IA: orientação ao adulto com o Gemini, usando os dados da criança como contexto."""
    profile = get_profile_for(db, profile_id, current_user)
    return assistant.ask(db, profile, current_user.id, payload.question,
                         [t.model_dump() for t in payload.history])
