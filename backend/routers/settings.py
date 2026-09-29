# ==========================================
# ROUTER: Configurações
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import User, Profile, Settings
from schemas import SettingsUpdate, SettingsResponse
from auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["Configurações"])


@router.get("/{profile_id}", response_model=SettingsResponse)
def get_settings(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Obter configurações de um perfil."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

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
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    settings = db.query(Settings).filter(Settings.profile_id == profile_id).first()
    if not settings:
        settings = Settings(profile_id=profile_id)
        db.add(settings)

    # Atualizar apenas campos fornecidos
    update_data = settings_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(settings, field, value)

    db.commit()
    db.refresh(settings)
    return settings
