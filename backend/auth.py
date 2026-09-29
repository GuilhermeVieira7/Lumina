# ==========================================
# AUTH - Autenticação JWT
# Sistema de Apoio Educacional para TEA
# ==========================================

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session as DBSession
import os
import secrets
from dotenv import load_dotenv

from database import get_db
from models import User

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    # Sem chave configurada, cria uma aleatória a cada início: ninguém consegue
    # forjar um login, mas quem estava logado precisa entrar de novo após reiniciar.
    SECRET_KEY = secrets.token_urlsafe(48)
    print("[AUTH] SECRET_KEY não definida no .env; usando uma chave aleatória temporária.")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _bcrypt_bytes(password: str) -> bytes:
    # O bcrypt só usa os primeiros 72 bytes e a versão 5 recusa senhas maiores
    return password.encode('utf-8')[:72]


def hash_password(password: str) -> str:
    """Gerar hash bcrypt da senha."""
    return bcrypt.hashpw(_bcrypt_bytes(password), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar senha contra hash."""
    try:
        return bcrypt.checkpw(_bcrypt_bytes(plain_password), hashed_password.encode('utf-8'))
    except ValueError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Criar token JWT."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: DBSession = Depends(get_db)
) -> User:
    """Dependency para obter o usuário autenticado pelo token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        raise credentials_exception

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        sub_val = payload.get("sub")
        if sub_val is None:
            raise credentials_exception
        user_id: int = int(sub_val)
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


from models import User, Profile, ProfileAccess

DEMO_THERAPIST = "terapeuta"


def create_demo_user(db: DBSession):
    """Criar contas de demonstração se não existirem.

    - admin / admin1234: responsável, com o perfil "Aluno Demo"
    - terapeuta / terapeuta1234: profissional com acesso autorizado ao "Aluno Demo"
    """
    demo_user = db.query(User).filter(User.username == "admin").first()
    if not demo_user:
        demo_user = User(
            username="admin",
            email="admin@tea-system.com",
            password_hash=hash_password("admin1234"),
            role="admin",
            consent_at=datetime.utcnow(),
        )
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        db.add(Profile(user_id=demo_user.id, name="Aluno Demo", avatar="😊", interests="animais, números, música"))
        db.commit()
        print("[AUTH] Usuario demo criado: admin / admin1234 com Perfil Padrão")

    therapist = db.query(User).filter(User.username == DEMO_THERAPIST).first()
    if not therapist:
        therapist = User(
            username=DEMO_THERAPIST,
            email="terapeuta@tea-system.com",
            password_hash=hash_password("terapeuta1234"),
            role="therapist",
            consent_at=datetime.utcnow(),
        )
        db.add(therapist)
        db.commit()
        db.refresh(therapist)
        demo_profile = db.query(Profile).filter(Profile.user_id == demo_user.id).first()
        if demo_profile:
            db.add(ProfileAccess(profile_id=demo_profile.id, professional_id=therapist.id, status="active"))
            db.commit()
        print("[AUTH] Profissional demo criado: terapeuta / terapeuta1234")
