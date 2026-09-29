# ==========================================
# ROUTER: Configurações
# ==========================================

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from data.communication import REQUESTS_BY_KEY

from database import get_db
from models import User, Profile, Settings
from schemas import SettingsUpdate, SettingsResponse
from auth import get_current_user
from permissions import get_profile_for

router = APIRouter(prefix="/api/settings", tags=["Configurações"])


@router.get("/{profile_id}", response_model=SettingsResponse)
def get_settings(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Obter configurações de um perfil."""
    profile = get_profile_for(db, profile_id, current_user)

    settings = db.query(Settings).filter(Settings.profile_id == profile_id).first()
    if not settings:
        # Criar configurações padrão se não existirem
        settings = Settings(profile_id=profile_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)

    return settings


@router.put("/{profile_id}", response_model=SettingsResponse)
def update_settings(
    profile_id: int,
    settings_data: SettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Atualizar configurações de um perfil."""
    profile = get_profile_for(db, profile_id, current_user)

    settings = db.query(Settings).filter(Settings.profile_id == profile_id).first()
    if not settings:
        settings = Settings(profile_id=profile_id)
        db.add(settings)

    # Atualizar apenas campos fornecidos
    update_data = settings_data.model_dump(exclude_unset=True)
    rewards = update_data.pop("rewards", None)
    requests = update_data.pop("requests", None)
    for field, value in update_data.items():
        if value is not None:
            setattr(settings, field, value)

    if rewards is not None:
        cleaned = [{"icon": r["icon"].strip(), "label": r["label"].strip()} for r in rewards]
        if any(not r["icon"] or not r["label"] for r in cleaned):
            raise HTTPException(status_code=400, detail="Cada prêmio precisa de figura e nome")
        settings.rewards_json = json.dumps(cleaned, ensure_ascii=False)
    if requests is not None:
        unknown = [k for k in requests if k not in REQUESTS_BY_KEY]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Pedido desconhecido: {', '.join(unknown)}")
        ordered = [k for k in REQUESTS_BY_KEY if k in set(requests)]
        settings.requests_json = json.dumps(ordered)

    db.commit()
    db.refresh(settings)
    return settings
