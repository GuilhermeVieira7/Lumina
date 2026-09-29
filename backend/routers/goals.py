# ==========================================
# ROUTER: Metas Personalizadas
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from models import User, Profile, Goal
from schemas import GoalCreate, GoalResponse
from auth import get_current_user

router = APIRouter(prefix="/api/goals", tags=["Metas"])


@router.get("/{profile_id}", response_model=List[GoalResponse])
def list_goals(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar metas de um perfil."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    goals = db.query(Goal).filter(Goal.profile_id == profile_id).all()
    return goals


@router.post("", response_model=GoalResponse)
def create_goal(
    goal_data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Criar nova meta."""
    profile = db.query(Profile).filter(
        Profile.id == goal_data.profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    goal = Goal(
        profile_id=goal_data.profile_id,
        activity_type=goal_data.activity_type,
        target_type=goal_data.target_type,
        target_value=goal_data.target_value,
        description=goal_data.description,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


@router.delete("/{goal_id}")
def delete_goal(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Deletar meta."""
    goal = db.query(Goal).join(Profile).filter(
        Goal.id == goal_id, Profile.user_id == current_user.id
    ).first()
    if not goal:
        raise HTTPException(status_code=404, detail="Meta não encontrada")

    db.delete(goal)
    db.commit()
    return {"message": "Meta deletada com sucesso"}
