# ==========================================
# ROUTER: Perfis de Crianças
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from typing import List

from database import get_db
from models import User, Profile, Settings
from schemas import ProfileCreate, ProfileUpdate, ProfileResponse
from auth import get_current_user

router = APIRouter(prefix="/api/profiles", tags=["Perfis"])


@router.get("", response_model=List[ProfileResponse])
def list_profiles(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar perfis do usuário logado."""
    profiles = db.query(Profile).filter(Profile.user_id == current_user.id).all()
    return profiles


@router.post("", response_model=ProfileResponse)
def create_profile(
    profile_data: ProfileCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Criar novo perfil de criança."""
    profile = Profile(
        user_id=current_user.id,
        name=profile_data.name,
        avatar=profile_data.avatar,
        birth_date=profile_data.birth_date,
        diagnosis=profile_data.diagnosis,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    # Criar configurações padrão para o perfil
    settings = Settings(profile_id=profile.id)
    db.add(settings)
    db.commit()

    return profile


@router.put("/{profile_id}", response_model=ProfileResponse)
def update_profile(
    profile_id: int,
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Atualizar perfil existente."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.avatar is not None:
        profile.avatar = profile_data.avatar
    if profile_data.birth_date is not None:
        profile.birth_date = profile_data.birth_date
    if profile_data.diagnosis is not None:
        profile.diagnosis = profile_data.diagnosis

    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}")
def delete_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Deletar perfil e todos os dados associados."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    # Verificar se é o último perfil
    count = db.query(Profile).filter(Profile.user_id == current_user.id).count()
    if count <= 1:
        raise HTTPException(status_code=400, detail="Você precisa ter pelo menos um perfil")

    db.delete(profile)
    db.commit()
    return {"message": "Perfil deletado com sucesso"}
