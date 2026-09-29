# ==========================================
# ROUTER: Conquistas (Achievements)
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func
from typing import List

from database import get_db
from models import User, Profile, Session, Achievement
from schemas import AchievementResponse, AchievementCheckResponse
from auth import get_current_user
from permissions import get_profile_for
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/achievements", tags=["Conquistas"])

# Definição dos badges
BADGES = {
    "firstSteps":        {"name": "Primeiros Passos",        "icon": "👣", "description": "Complete sua primeira atividade",       "requirement": 1,   "type": "activities"},
    "tenSessions":       {"name": "Dedicado",                "icon": "📚", "description": "Complete 10 atividades",                "requirement": 10,  "type": "activities"},
    "fiftyStars":        {"name": "Colecionador de Estrelas", "icon": "⭐", "description": "Ganhe 50 estrelas",                    "requirement": 50,  "type": "stars"},
    "perfectScore":      {"name": "Perfeição",               "icon": "💯", "description": "Acerte 100% em uma atividade",          "requirement": 100, "type": "accuracy"},
    "weekStreak":        {"name": "Consistente",             "icon": "🔥", "description": "Estude 7 dias seguidos",                "requirement": 7,   "type": "streak"},
    "masterAll":         {"name": "Mestre",                  "icon": "🏆", "description": "Complete todas as 12 atividades",       "requirement": 12,  "type": "allActivities"},
    "speedDemon":        {"name": "Relâmpago",               "icon": "⚡", "description": "Complete uma atividade em menos de 2min","requirement": 120000, "type": "speed"},
    "hundredActivities": {"name": "Campeão",                 "icon": "🎖️", "description": "Complete 100 atividades",               "requirement": 100, "type": "activities"},
}


def _get_streak(db: DBSession, profile_id: int) -> int:
    """Calcular streak de dias consecutivos de estudo."""
    sessions = (
        db.query(Session.created_at)
        .filter(Session.profile_id == profile_id, Session.is_practice == False)
        .order_by(Session.created_at.desc())
        .all()
    )
    if not sessions:
        return 0

    dates = list(set(s.created_at.date() for s in sessions))
    dates.sort(reverse=True)

    streak = 1
    for i in range(1, len(dates)):
        diff = (dates[i - 1] - dates[i]).days
        if diff == 1:
            streak += 1
        else:
            break
    return streak


@router.get("/{profile_id}", response_model=List[AchievementResponse])
def get_achievements(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar todas as conquistas (desbloqueadas e bloqueadas)."""
    profile = get_profile_for(db, profile_id, current_user)

    unlocked = db.query(Achievement).filter(Achievement.profile_id == profile_id).all()
    unlocked_ids = {a.badge_id: a.unlocked_at for a in unlocked}

    result = []
    for badge_id, badge in BADGES.items():
        result.append(AchievementResponse(
            badge_id=badge_id,
            name=badge["name"],
            icon=badge["icon"],
            description=badge["description"],
            unlocked=badge_id in unlocked_ids,
            unlocked_at=unlocked_ids.get(badge_id),
        ))
    return result


@router.post("/check/{profile_id}", response_model=AchievementCheckResponse)
def check_achievements(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Verificar e desbloquear novas conquistas."""
    profile = get_profile_for(db, profile_id, current_user)

    unlocked = db.query(Achievement).filter(Achievement.profile_id == profile_id).all()
    unlocked_ids = set(a.badge_id for a in unlocked)

    # Calcular métricas necessárias
    total_activities = db.query(func.count(Session.id)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total_stars = db.query(func.sum(Session.stars)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    has_perfect = db.query(Session).filter(
        Session.profile_id == profile_id, Session.accuracy >= 100, Session.is_practice == False
    ).first() is not None

    streak = _get_streak(db, profile_id)

    distinct_activities = db.query(func.count(func.distinct(Session.activity_type))).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    has_fast = db.query(Session).filter(
        Session.profile_id == profile_id, Session.total_time < 120000, Session.is_practice == False
    ).first() is not None

    newly_unlocked = []

    for badge_id, badge in BADGES.items():
        if badge_id in unlocked_ids:
            continue

        achieved = False
        if badge["type"] == "activities":
            achieved = total_activities >= badge["requirement"]
        elif badge["type"] == "stars":
            achieved = (total_stars or 0) >= badge["requirement"]
        elif badge["type"] == "accuracy":
            achieved = has_perfect
        elif badge["type"] == "streak":
            achieved = streak >= badge["requirement"]
        elif badge["type"] == "allActivities":
            achieved = distinct_activities >= badge["requirement"]
        elif badge["type"] == "speed":
            achieved = has_fast

        if achieved:
            new_achievement = Achievement(profile_id=profile_id, badge_id=badge_id)
            db.add(new_achievement)
            newly_unlocked.append(AchievementResponse(
                badge_id=badge_id,
                name=badge["name"],
                icon=badge["icon"],
                description=badge["description"],
                unlocked=True,
                unlocked_at=datetime.utcnow(),
            ))

    db.commit()

    # Retornar todas as conquistas atualizadas
    all_achievements = []
    current_unlocked = set(unlocked_ids) | set(a.badge_id for a in newly_unlocked if hasattr(a, 'badge_id'))
    for badge_id, badge in BADGES.items():
        all_achievements.append(AchievementResponse(
            badge_id=badge_id,
            name=badge["name"],
            icon=badge["icon"],
            description=badge["description"],
            unlocked=badge_id in current_unlocked,
        ))

    return AchievementCheckResponse(newly_unlocked=newly_unlocked, all_achievements=all_achievements)
