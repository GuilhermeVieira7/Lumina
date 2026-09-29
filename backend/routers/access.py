# ==========================================
# ROUTER: Acesso de Profissionais (RF04)
# ==========================================
# O responsável convida um profissional (conta do tipo "profissional");
# o profissional aceita; o responsável pode revogar a qualquer momento.

from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from database import get_db
from models import Profile, ProfileAccess, User
from permissions import get_profile_for
from schemas import AccessInvite, AccessResponse

router = APIRouter(prefix="/api/access", tags=["Acesso de Profissionais"])


def _to_response(db: DBSession, access: ProfileAccess) -> AccessResponse:
    profile = access.profile
    owner = db.query(User).filter(User.id == profile.user_id).first()
    return AccessResponse(
        id=access.id,
        profile_id=profile.id,
        profile_name=profile.name,
        professional_id=access.professional_id,
        professional_name=access.professional.username,
        owner_name=owner.username if owner else "",
        status=access.status,
        created_at=access.created_at,
    )


@router.post("", response_model=AccessResponse)
def invite(
    data: AccessInvite,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Responsável convida um profissional pelo usuário ou email."""
    get_profile_for(db, data.profile_id, current_user, manage=True)
    ident = data.professional.strip()
    professional = db.query(User).filter(
        (User.username == ident) | (func.lower(User.email) == ident.lower())
    ).first()
    if not professional or professional.role != "therapist":
        raise HTTPException(
            status_code=404,
            detail="Profissional não encontrado. Peça que ele crie uma conta do tipo Profissional.",
        )
    if professional.id == current_user.id:
        raise HTTPException(status_code=400, detail="Você já é o responsável por este perfil")

    access = db.query(ProfileAccess).filter(
        ProfileAccess.profile_id == data.profile_id, ProfileAccess.professional_id == professional.id
    ).first()
    if access and access.status in ("pending", "active"):
        raise HTTPException(status_code=400, detail="Este profissional já foi convidado")
    if access:
        access.status = "pending"
        access.created_at = datetime.utcnow()
        access.responded_at = None
    else:
        access = ProfileAccess(profile_id=data.profile_id, professional_id=professional.id, status="pending")
        db.add(access)
    db.commit()
    db.refresh(access)
    return _to_response(db, access)


@router.get("/profile/{profile_id}", response_model=List[AccessResponse])
def list_for_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Profissionais convidados para um perfil (visão do responsável)."""
    get_profile_for(db, profile_id, current_user, manage=True)
    rows = (
        db.query(ProfileAccess)
        .filter(ProfileAccess.profile_id == profile_id)
        .order_by(desc(ProfileAccess.created_at))
        .all()
    )
    return [_to_response(db, a) for a in rows]


@router.get("/invites", response_model=List[AccessResponse])
def my_invites(
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Convites e acessos do profissional logado."""
    rows = (
        db.query(ProfileAccess)
        .filter(ProfileAccess.professional_id == current_user.id, ProfileAccess.status.in_(["pending", "active"]))
        .order_by(desc(ProfileAccess.created_at))
        .all()
    )
    return [_to_response(db, a) for a in rows]


def _own_invite(db: DBSession, access_id: int, user: User) -> ProfileAccess:
    access = db.query(ProfileAccess).filter(
        ProfileAccess.id == access_id, ProfileAccess.professional_id == user.id
    ).first()
    if not access or access.status != "pending":
        raise HTTPException(status_code=404, detail="Convite não encontrado")
    return access


@router.post("/{access_id}/accept", response_model=AccessResponse)
def accept(access_id: int, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    access = _own_invite(db, access_id, current_user)
    access.status = "active"
    access.responded_at = datetime.utcnow()
    db.commit()
    db.refresh(access)
    return _to_response(db, access)


@router.post("/{access_id}/decline")
def decline(access_id: int, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    access = _own_invite(db, access_id, current_user)
    access.status = "revoked"
    access.responded_at = datetime.utcnow()
    db.commit()
    return {"message": "Convite recusado"}


@router.delete("/{access_id}")
def revoke(access_id: int, current_user: User = Depends(get_current_user), db: DBSession = Depends(get_db)):
    """Responsável revoga o acesso; vale na próxima requisição do profissional."""
    access = db.query(ProfileAccess).filter(ProfileAccess.id == access_id).first()
    if not access:
        raise HTTPException(status_code=404, detail="Acesso não encontrado")
    get_profile_for(db, access.profile_id, current_user, manage=True)
    access.status = "revoked"
    access.responded_at = datetime.utcnow()
    db.commit()
    return {"message": "Acesso revogado"}
