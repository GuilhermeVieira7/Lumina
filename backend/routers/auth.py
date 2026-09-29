# ==========================================
# ROUTER: Autenticação
# ==========================================

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession

import rate_limit
from database import get_db
from models import Note, ProfileAccess, RecommendationDecision, User
from schemas import PasswordCheck, UserCreate, UserLogin, UserResponse, TokenResponse
from auth import DUMMY_HASH, hash_password, verify_password, needs_rehash, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse)
def register(user_data: UserCreate, db: DBSession = Depends(get_db)):
    """Registrar responsável ou profissional, com registro do consentimento (LGPD)."""
    if not user_data.consent:
        raise HTTPException(status_code=400, detail="É preciso aceitar o termo de consentimento")
    if user_data.role not in ("parent", "therapist"):
        raise HTTPException(status_code=400, detail="Tipo de conta inválido")

    query = db.query(User).filter(User.username == user_data.username)
    if user_data.email:
        query = db.query(User).filter((User.username == user_data.username) | (User.email == user_data.email))
    if query.first():
        raise HTTPException(status_code=400, detail="Usuário ou email já cadastrado")

    user = User(
        username=user_data.username,
        email=user_data.email or None,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        consent_at=datetime.utcnow(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: DBSession = Depends(get_db)):
    """Login de usuário existente."""
    key = f"login:{credentials.username.lower()}"
    rate_limit.check(key)
    user = db.query(User).filter(User.username == credentials.username).first()
    valid = verify_password(credentials.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        rate_limit.failed(key)
        raise HTTPException(status_code=401, detail="Usuário ou senha incorretos")
    rate_limit.succeeded(key)
    _upgrade_hash(db, user, credentials.password)

    token = create_access_token(data={"sub": str(user.id)})
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Obter dados do usuário autenticado."""
    return UserResponse.model_validate(current_user)


def _upgrade_hash(db: DBSession, user: User, password: str) -> None:
    """Senha certa de conta antiga (bcrypt): regrava em Argon2id sem o usuário perceber."""
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()


def _check_password(password: str, user: User) -> None:
    """Senha do adulto já logado (painel, excluir conta), com limite de tentativas."""
    key = f"user:{user.id}"
    rate_limit.check(key)
    if not verify_password(password, user.password_hash):
        rate_limit.failed(key)
        raise HTTPException(status_code=403, detail="Senha incorreta")
    rate_limit.succeeded(key)


@router.post("/verify-password")
def verify_current_password(data: PasswordCheck, current_user: User = Depends(get_current_user)):
    """Confirmar a senha do adulto antes de abrir o Painel dos Pais.

    Responde 403 (e não 401) para não encerrar a sessão da criança por engano.
    """
    _check_password(data.password, current_user)
    return {"ok": True}


@router.post("/delete-account")
def delete_account(
    data: PasswordCheck,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Excluir a conta e todos os dados das crianças cadastradas (LGPD, RNF06)."""
    _check_password(data.password, current_user)

    db.query(ProfileAccess).filter(ProfileAccess.professional_id == current_user.id).delete()
    db.query(Note).filter(Note.author_id == current_user.id).update({Note.author_id: None})
    db.query(RecommendationDecision).filter(RecommendationDecision.decided_by == current_user.id).update(
        {RecommendationDecision.decided_by: None}
    )
    db.delete(current_user)  # perfis, sessões, notas e rotinas saem em cascata
    db.commit()
    return {"message": "Conta e dados excluídos"}
