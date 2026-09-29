# ==========================================
# ROUTER: Agenda Visual de Rotina (RF13)
# ==========================================
# Sequência de pictogramas que a criança acompanha ao longo do dia
# (agenda visual do ensino estruturado, TEACCH).

from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from database import get_db
from models import RoutineItem, User
from permissions import get_profile_for
from schemas import RoutineItemCreate, RoutineItemResponse, RoutineItemUpdate

router = APIRouter(prefix="/api/routine", tags=["Rotina Visual"])

ROUTINE_TEMPLATE = [
    ("🌅", "Acordar", "07:00"),
    ("🪥", "Escovar os dentes", "07:10"),
    ("🥣", "Café da manhã", "07:30"),
    ("🏫", "Escola", "08:00"),
    ("🍽️", "Almoço", "12:00"),
    ("⭐", "Atividades no Lumina", "15:00"),
    ("🧸", "Brincar", "16:00"),
    ("🛁", "Banho", "18:30"),
    ("🌙", "Dormir", "20:30"),
]


def _to_response(item: RoutineItem) -> RoutineItemResponse:
    return RoutineItemResponse(
        id=item.id,
        profile_id=item.profile_id,
        position=item.position,
        icon=item.icon,
        label=item.label,
        time=item.time,
        done_today=item.done_on == date.today(),
    )


def _get_item(db: DBSession, item_id: int, user: User) -> RoutineItem:
    item = db.query(RoutineItem).filter(RoutineItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    get_profile_for(db, item.profile_id, user)
    return item


@router.get("/{profile_id}", response_model=List[RoutineItemResponse])
def list_routine(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    get_profile_for(db, profile_id, current_user)
    items = (
        db.query(RoutineItem)
        .filter(RoutineItem.profile_id == profile_id)
        .order_by(RoutineItem.position, RoutineItem.id)
        .all()
    )
    return [_to_response(i) for i in items]


@router.post("", response_model=RoutineItemResponse)
def create_item(
    data: RoutineItemCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    get_profile_for(db, data.profile_id, current_user)
    count = db.query(RoutineItem).filter(RoutineItem.profile_id == data.profile_id).count()
    item = RoutineItem(
        profile_id=data.profile_id, position=count,
        icon=data.icon or "⭐", label=data.label.strip(), time=data.time or None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.post("/{profile_id}/template", response_model=List[RoutineItemResponse])
def create_from_template(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Criar uma rotina de exemplo para o adulto adaptar."""
    get_profile_for(db, profile_id, current_user)
    if db.query(RoutineItem).filter(RoutineItem.profile_id == profile_id).count():
        raise HTTPException(status_code=400, detail="A rotina já tem itens")
    for position, (icon, label, time) in enumerate(ROUTINE_TEMPLATE):
        db.add(RoutineItem(profile_id=profile_id, position=position, icon=icon, label=label, time=time))
    db.commit()
    return list_routine(profile_id, current_user, db)


@router.put("/{item_id}", response_model=RoutineItemResponse)
def update_item(
    item_id: int,
    data: RoutineItemUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = _get_item(db, item_id, current_user)
    if data.icon is not None:
        item.icon = data.icon
    if data.label is not None:
        item.label = data.label.strip()
    if data.time is not None:
        item.time = data.time or None
    if data.position is not None:
        siblings = (
            db.query(RoutineItem)
            .filter(RoutineItem.profile_id == item.profile_id, RoutineItem.id != item.id)
            .order_by(RoutineItem.position, RoutineItem.id)
            .all()
        )
        new_pos = max(0, min(data.position, len(siblings)))
        siblings.insert(new_pos, item)
        for position, sibling in enumerate(siblings):
            sibling.position = position
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.post("/{item_id}/toggle", response_model=RoutineItemResponse)
def toggle_done(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Marcar ou desmarcar a etapa como feita hoje."""
    item = _get_item(db, item_id, current_user)
    item.done_on = None if item.done_on == date.today() else date.today()
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.delete("/{item_id}")
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    item = _get_item(db, item_id, current_user)
    db.delete(item)
    db.commit()
    return {"message": "Item removido"}
