# ==========================================
# ROUTER: Plano de Atividades (personalização pelos adultos)
# ==========================================
# O adulto escolhe quais atividades aparecem para a criança, em que nível,
# com quantas etapas e qual fica destacada como recomendada (RF06, RNF10).

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from data.activity_bank import ACTIVITY_AREA, ACTIVITY_BANK, DEFAULT_ENABLED, max_level
from database import get_db
from models import ActivityPlan, User
from permissions import get_profile_for
from schemas import PlanResponse, PlanUpdate

router = APIRouter(prefix="/api/plans", tags=["Plano de Atividades"])


def get_or_create_plan(db: DBSession, profile_id: int, activity_type: str) -> ActivityPlan:
    plan = db.query(ActivityPlan).filter(
        ActivityPlan.profile_id == profile_id, ActivityPlan.activity_type == activity_type
    ).first()
    if not plan:
        plan = ActivityPlan(
            profile_id=profile_id,
            activity_type=activity_type,
            level=1,
            enabled=activity_type in DEFAULT_ENABLED,
            recommended=False,
            question_count=5,
        )
        db.add(plan)
        db.flush()
    return plan


def _to_response(activity_type: str, plan: ActivityPlan = None) -> PlanResponse:
    activity = ACTIVITY_BANK[activity_type]
    return PlanResponse(
        activity_type=activity_type,
        name=activity["name"],
        icon=activity["icon"],
        area=ACTIVITY_AREA.get(activity_type, "cognicao"),
        max_level=max_level(activity_type),
        level=min(plan.level, max_level(activity_type)) if plan else 1,
        enabled=plan.enabled if plan else activity_type in DEFAULT_ENABLED,
        recommended=plan.recommended if plan else False,
        question_count=plan.question_count if plan else 5,
    )


@router.get("/{profile_id}", response_model=List[PlanResponse])
def list_plan(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Plano de todas as atividades do perfil (valores padrão quando ainda não definido)."""
    get_profile_for(db, profile_id, current_user)
    plans = {p.activity_type: p for p in db.query(ActivityPlan).filter(ActivityPlan.profile_id == profile_id)}
    return [_to_response(a, plans.get(a)) for a in ACTIVITY_BANK]


@router.put("/{profile_id}/{activity_type}", response_model=PlanResponse)
def update_plan(
    profile_id: int,
    activity_type: str,
    data: PlanUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Ajustar nível, visibilidade, etapas ou destaque de uma atividade."""
    get_profile_for(db, profile_id, current_user)
    if activity_type not in ACTIVITY_BANK:
        raise HTTPException(status_code=404, detail="Atividade não encontrada")

    plan = get_or_create_plan(db, profile_id, activity_type)
    if data.level is not None:
        plan.level = min(data.level, max_level(activity_type))
    if data.enabled is not None:
        plan.enabled = data.enabled
        if not data.enabled:
            plan.recommended = False
    if data.recommended is not None:
        plan.recommended = data.recommended
        if data.recommended:
            plan.enabled = True
    if data.question_count is not None:
        plan.question_count = data.question_count
    db.commit()
    db.refresh(plan)
    return _to_response(activity_type, plan)
