# ==========================================
# ROUTER: Recomendações IA
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from models import User, Profile
from schemas import AIAnalysis, ErrorPattern, Recommendation
from auth import get_current_user
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
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

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
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    patterns = AIEngine.identify_error_patterns(db, profile_id, activity_type)
    return [ErrorPattern(**p) for p in patterns]


@router.get("/recommendations/{profile_id}", response_model=List[Recommendation])
def get_recommendations(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Gerar recomendações personalizadas baseadas em IA."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    recs = AIEngine.generate_recommendations(db, profile_id)
    return [Recommendation(**r) for r in recs]
