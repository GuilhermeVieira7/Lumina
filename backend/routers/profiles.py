# ==========================================
# ROUTER: Perfis de Crianças
# ==========================================

import base64
import binascii

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from models import User, Profile, Settings
from schemas import ProfileCreate, ProfileUpdate, ProfileResponse, ProfilePhoto
from auth import get_current_user
from permissions import accessible_profiles, get_profile_for, is_owner

router = APIRouter(prefix="/api/profiles", tags=["Perfis"])

EDITABLE_FIELDS = ("name", "avatar", "birth_date", "interests", "sensory_notes", "communication")


def to_response(db: DBSession, profile: Profile, user: User) -> ProfileResponse:
    owner = is_owner(profile, user)
    owner_name = None
    if not owner:
        owner_user = db.query(User).filter(User.id == profile.user_id).first()
        owner_name = owner_user.username if owner_user else None
    data = ProfileResponse.model_validate(profile, from_attributes=True).model_dump()
    data.update(is_owner=owner, owner_name=owner_name)
    return ProfileResponse(**data)


@router.get("", response_model=List[ProfileResponse])
def list_profiles(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Perfis do responsável e perfis compartilhados com o profissional logado."""
    return [to_response(db, p, current_user) for p in accessible_profiles(db, current_user)]


@router.post("", response_model=ProfileResponse)
def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Criar novo perfil de criança (sem diagnóstico: só dados para personalização)."""
    profile = Profile(user_id=current_user.id, **profile_data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)

    db.add(Settings(profile_id=profile.id))
    db.commit()
    return to_response(db, profile, current_user)


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Atualizar perfil (somente o responsável)."""
    profile = get_profile_for(db, profile_id, current_user, manage=True)
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        if field in EDITABLE_FIELDS and (value is not None or field != "name"):
            setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return to_response(db, profile, current_user)


@router.delete("/{profile_id}")
def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Excluir o perfil e todos os dados da criança (LGPD, RNF06)."""
    profile = get_profile_for(db, profile_id, current_user, manage=True)
    db.delete(profile)
    db.commit()
    return {"message": "Perfil e dados da criança excluídos"}


# Assinaturas dos formatos aceitos para a foto
PHOTO_TYPES = {
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/webp": (b"RIFF",),
}


@router.put("/{profile_id}/photo", response_model=ProfileResponse)
def set_photo(
    profile_id: int,
    data: ProfilePhoto,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Salvar a foto da criança (somente o responsável). A foto é opcional."""
    profile = get_profile_for(db, profile_id, current_user, manage=True)
    header, _, encoded = data.photo.partition(",")
    mime = header[5:].split(";")[0] if header.startswith("data:") and header.endswith(";base64") else ""
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raw = b""
    if mime not in PHOTO_TYPES or not raw or not raw.startswith(PHOTO_TYPES[mime]):
        raise HTTPException(status_code=400, detail="Envie uma imagem JPEG, PNG ou WebP")
    profile.photo = data.photo
    db.commit()
    db.refresh(profile)
    return to_response(db, profile, current_user)


@router.delete("/{profile_id}/photo", response_model=ProfileResponse)
def delete_photo(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Apagar a foto; a criança volta a ser mostrada pelo emoji."""
    profile = get_profile_for(db, profile_id, current_user, manage=True)
    profile.photo = None
    db.commit()
    db.refresh(profile)
    return to_response(db, profile, current_user)
