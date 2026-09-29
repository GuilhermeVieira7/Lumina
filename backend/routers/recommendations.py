# ==========================================
# ROUTER: Recomendações IA
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from data.activity_bank import ACTIVITY_BANK
from models import User, RecommendationDecision, Session
from routers.plans import get_or_create_plan
from schemas import AIAnalysis, ErrorPattern, Recommendation, RecommendationDecisionIn
from auth import get_current_user
from permissions import get_profile_for
from ai_engine import AIEngine

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
