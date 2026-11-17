# ==========================================
# ROUTER: Metas Personalizadas
# ==========================================

import math
from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import User, Goal, Session
from schemas import GoalCreate, GoalResponse
from ai_engine import to_utc
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


STALLED_DAYS = 7      # sem praticar a atividade da meta há mais que isso: meta parada
ON_TRACK_WEEKS = 6    # previsão até 6 semanas: no ritmo; acima disso: devagar


def _weeks_text(weeks: float) -> str:
    if weeks < 1:
        return "em poucos dias"
    n = math.ceil(weeks)
    return f"em cerca de {n} {'semana' if n == 1 else 'semanas'}"


def goal_forecast(db: DBSession, goal: Goal) -> dict:
    """Previsão simples, explicável: no ritmo das últimas 4 semanas, quando a meta será atingida.

    - acerto: inclinação (reta de mínimos quadrados) do acerto nas últimas sessões
    - sessões e estrelas: média por semana nas últimas 4 semanas
    """
    if goal.completed:
        done = goal.completed_at.strftime("%d/%m") if goal.completed_at else ""
        return {"status": "done", "forecast": f"Meta atingida{' em ' + done if done else ''}."}

    sessions = (
        db.query(Session)
        .filter(Session.profile_id == goal.profile_id, Session.activity_type == goal.activity_type,
                Session.is_practice == False)  # noqa: E712
        .order_by(Session.created_at, Session.id).all()
    )
    if not sessions:
        return {"status": "waiting", "forecast": "Ainda não há sessões nesta atividade."}

    now = datetime.utcnow()
    idle = (now - to_utc(sessions[-1].created_at)).days
    if idle > STALLED_DAYS:
        return {"status": "stalled", "forecast": f"Parada: a atividade não é praticada há {idle} dias."}

    month = [s for s in sessions if to_utc(s.created_at) >= now - timedelta(days=28)]
    span_weeks = max(1.0, (now - to_utc(month[0].created_at)).days / 7) if month else 1.0
    per_week = len(month) / span_weeks
    remaining = goal.target_value - goal.current_value

    if goal.target_type == "accuracy":
        recent = [s.accuracy for s in sessions[-6:]]
        if len(recent) < 3:
            return {"status": "waiting", "forecast": "Precisa de pelo menos 3 sessões para prever."}
        n = len(recent)
        mean_x, mean_y = (n - 1) / 2, sum(recent) / n
        slope = sum((i - mean_x) * (y - mean_y) for i, y in enumerate(recent)) / sum((i - mean_x) ** 2 for i in range(n))
        if slope <= 0.5:
            return {"status": "slow", "forecast": (
                f"O acerto está estável em torno de {mean_y:.0f}%. No ritmo atual não dá para prever; "
                "considere mais apoio, menos etapas ou um nível abaixo.")}
        weeks = (remaining / slope) / max(per_week, 0.5)
    else:
        if goal.target_type == "stars":
            rate = sum(s.stars or 0 for s in month) / span_weeks
        else:
            rate = per_week
        if rate <= 0:
            return {"status": "slow", "forecast": "Sem avanço nas últimas semanas."}
        weeks = remaining / rate

    status = "on_track" if weeks <= ON_TRACK_WEEKS else "slow"
    return {"status": status, "forecast": f"No ritmo atual, deve atingir a meta {_weeks_text(weeks)}."}


def goals_with_forecast(db: DBSession, profile_id: int) -> List[dict]:
    refresh_goals(db, profile_id)
    goals = db.query(Goal).filter(Goal.profile_id == profile_id).order_by(Goal.completed, Goal.created_at).all()
    return [{**GoalResponse.model_validate(g).model_dump(), **goal_forecast(db, g)} for g in goals]


@router.get("/{profile_id}", response_model=List[GoalResponse])
def list_goals(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar metas de um perfil, com o progresso atualizado e a previsão de quando serão atingidas."""
    get_profile_for(db, profile_id, current_user)
    return goals_with_forecast(db, profile_id)


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
