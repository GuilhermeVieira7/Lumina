# ==========================================
# PERMISSIONS - Quem pode ver cada perfil
# ==========================================
# O responsável (dono do perfil) tem acesso total.
# Um profissional só acessa depois que o responsável convida e ele aceita,
# e perde o acesso no momento em que o responsável revoga (RF02, RF04).

from typing import List

from fastapi import HTTPException
from sqlalchemy.orm import Session as DBSession

from models import Profile, ProfileAccess, User


def is_owner(profile: Profile, user: User) -> bool:
    return profile.user_id == user.id


def get_profile_for(db: DBSession, profile_id: int, user: User, manage: bool = False) -> Profile:
    """Retorna o perfil se o usuário puder acessá-lo; senão 404.

    manage=True restringe ao responsável (editar perfil, convidar, revogar, excluir).
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if profile and is_owner(profile, user):
        return profile
    if profile and not manage:
        access = db.query(ProfileAccess).filter(
            ProfileAccess.profile_id == profile_id,
            ProfileAccess.professional_id == user.id,
            ProfileAccess.status == "active",
        ).first()
        if access:
            return profile
    raise HTTPException(status_code=404, detail="Perfil não encontrado")


def accessible_profiles(db: DBSession, user: User) -> List[Profile]:
    """Perfis do responsável e perfis compartilhados com o profissional."""
    own = db.query(Profile).filter(Profile.user_id == user.id).all()
    shared = (
        db.query(Profile)
        .join(ProfileAccess, ProfileAccess.profile_id == Profile.id)
        .filter(ProfileAccess.professional_id == user.id, ProfileAccess.status == "active")
        .all()
    )
    return own + [p for p in shared if p.user_id != user.id]
