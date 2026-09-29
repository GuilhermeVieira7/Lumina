# ==========================================
# ROUTER: Metas Personalizadas
# ==========================================

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import User, Goal, Session
from schemas import GoalCreate, GoalResponse
from auth import get_current_user
from permissions import get_profile_for

router = APIRouter(prefix="/api/goals", tags=["Metas"])

TARGET_TYPES = {"accuracy", "stars", "sessions"}


def refresh_goals(db: DBSession, profile_id: int) -> None:
    """Recalcular o progresso das metas a partir das sessões registradas.

    - accuracy: média de acerto das 3 últimas sessões da atividade
    - stars:    estrelas somadas na atividade
    - sessions: quantidade de sessões na atividade
    """
    goals = db.query(Goal).filter(Goal.profile_id == profile_id).all()
    for goal in goals:
        base = db.query(Session).filter(
            Session.profile_id == profile_id,
            Session.activity_type == goal.activity_type,
            Session.is_practice == False,  # noqa: E712
        )
        if goal.target_type == "accuracy":
            recent = base.order_by(desc(Session.created_at)).limit(3).all()
            value = sum(s.accuracy for s in recent) / len(recent) if recent else 0
        elif goal.target_type == "stars":
            value = base.with_entities(func.sum(Session.stars)).scalar() or 0
        else:
            value = base.count()
        goal.current_value = round(float(value), 1)
        if not goal.completed and goal.current_value >= goal.target_value:
            goal.completed = True
            goal.completed_at = datetime.utcnow()
    db.commit()


@router.get("/{profile_id}", response_model=List[GoalResponse])
def list_goals(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar metas de um perfil, com o progresso atualizado."""
    get_profile_for(db, profile_id, current_user)
    refresh_goals(db, profile_id)
    return db.query(Goal).filter(Goal.profile_id == profile_id).order_by(Goal.completed, Goal.created_at).all()


@router.post("", response_model=GoalResponse)
def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Criar nova meta (responsável ou profissional autorizado)."""
    get_profile_for(db, goal_data.profile_id, current_user)
    if goal_data.target_type not in TARGET_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de meta inválido")

    goal = Goal(
        profile_id=goal_data.profile_id,
        activity_type=goal_data.activity_type,
        target_type=goal_data.target_type,
        target_value=goal_data.target_value,
        description=goal_data.description,
    )
    db.add(goal)
    db.commit()
    refresh_goals(db, goal_data.profile_id)
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Deletar meta."""
    goal = db.query(Goal).filter(Goal.id == goal_id).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")
    get_profile_for(db, goal.profile_id, current_user)
    db.delete(goal)
    db.commit()
    return {"message": "Meta deletada com sucesso"}
