# ==========================================
# MODELS - Modelos do Banco de Dados
# Sistema de Apoio Educacional para TEA
# ==========================================

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import json

from database import Base
from data.communication import DEFAULT_REQUESTS, DEFAULT_REWARDS


class User(Base):
    """Usuários do sistema (pais, responsáveis, terapeutas)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="parent")  # parent, therapist, admin
    consent_at = Column(DateTime(timezone=True), nullable=True)  # consentimento LGPD do responsável
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profiles = relationship("Profile", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    """Perfis de crianças (cada usuário pode ter vários)."""
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    avatar = Column(String(10), default="😊")
    birth_date = Column(Date, nullable=True)
    # Sem diagnóstico ou laudo: só o que serve à personalização (minimização de dados, LGPD).
    interests = Column(Text, nullable=True)       # ex.: "dinossauros, trens, música"
    sensory_notes = Column(Text, nullable=True)   # ex.: "sensível a sons altos"
    communication = Column(String(30), nullable=True)  # verbal, gestos, figuras, caa
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="profiles")
    sessions = relationship("Session", back_populates="profile", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="profile", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="profile", cascade="all, delete-orphan")
    plans = relationship("ActivityPlan", back_populates="profile", cascade="all, delete-orphan")
    routine = relationship("RoutineItem", back_populates="profile", cascade="all, delete-orphan")
    access = relationship("ProfileAccess", back_populates="profile", cascade="all, delete-orphan")
    decisions = relationship("RecommendationDecision", back_populates="profile", cascade="all, delete-orphan")
    requests = relationship("ChildRequest", back_populates="profile", cascade="all, delete-orphan")
    moods = relationship("MoodCheck", back_populates="profile", cascade="all, delete-orphan")


class Session(Base):
    """Sessões de atividade registradas."""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    activity_type = Column(String(30), nullable=False)
    level = Column(Integer, default=1)
    total_questions = Column(Integer, default=0)
    correct = Column(Integer, default=0)
    incorrect = Column(Integer, default=0)
    accuracy = Column(Float, default=0.0)
    total_time = Column(Integer, default=0)  # milissegundos
    stars = Column(Integer, default=0)
    is_practice = Column(Boolean, default=False)
    help_level = Column(String(20), nullable=True)  # none, verbal, gesture, physical
    reward = Column(String(60), nullable=True)      # prêmio escolhido no quadro de fichas
    timed_out = Column(Boolean, default=False)      # terminou pelo timer antes das etapas
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="sessions")
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")


class Response(Base):
    """Respostas individuais de cada questão dentro de uma sessão."""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    question_index = Column(Integer, default=0)
    is_correct = Column(Boolean, default=False)
    response_time = Column(Integer, default=0)  # milissegundos
    attempts = Column(Integer, default=1)  # Tentativas até acertar
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="responses")


class Settings(Base):
    """Configurações personalizadas por perfil."""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), unique=True, nullable=False)
    difficulty = Column(Integer, default=1)
    auto_adjust = Column(Boolean, default=True)
    sound_enabled = Column(Boolean, default=True)
    font_size = Column(String(10), default="medium")
    theme = Column(String(20), default="light")
    language = Column(String(5), default="pt")
    auto_backup = Column(Boolean, default=True)
    alerts_enabled = Column(Boolean, default=True)
    voice_enabled = Column(Boolean, default=False)   # elogios falados só se o adulto ligar (RNF03)
    low_stimulus = Column(Boolean, default=False)
    mastery_threshold = Column(Integer, default=85)  # % de acerto para considerar domínio
    mastery_sessions = Column(Integer, default=3)    # sessões seguidas acima do critério
    token_board = Column(Boolean, default=True)      # quadro de fichas antes das atividades
    request_board = Column(Boolean, default=True)    # botão "Pedir" na área da criança
    mood_checkin = Column(Boolean, default=True)     # "Como estou me sentindo?" ao entrar
    rewards_json = Column(Text, nullable=True)       # prêmios que a criança pode escolher
    requests_json = Column(Text, nullable=True)      # pedidos que aparecem na prancha

    profile = relationship("Profile", back_populates="settings")

    @property
    def rewards(self):
        try:
            value = json.loads(self.rewards_json) if self.rewards_json else None
        except ValueError:
            value = None
        return value if value else [dict(r) for r in DEFAULT_REWARDS]

    @property
    def requests(self):
        try:
            value = json.loads(self.requests_json) if self.requests_json else None
        except ValueError:
            value = None
        return value if value else list(DEFAULT_REQUESTS)


class Achievement(Base):
    """Conquistas (badges) desbloqueadas por perfil."""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    badge_id = Column(String(30), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="achievements")


class Goal(Base):
    """Metas personalizadas definidas para cada perfil."""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    activity_type = Column(String(30), nullable=False)
    target_type = Column(String(20), nullable=False)  # accuracy, stars, sessions
    target_value = Column(Float, nullable=False)
    current_value = Column(Float, default=0.0)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile", back_populates="goals")


class Note(Base):
    """Notas de terapeutas/responsáveis sobre sessões."""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=True)
    activity_type = Column(String(30), nullable=True)
    content = Column(Text, nullable=False)
    author = Column(String(100), default="Terapeuta")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="notes")


class ActivityPlan(Base):
    """Plano de uma atividade para a criança, definido pelos adultos.

    Guarda o nível aprovado, se a atividade aparece no menu da criança,
    quantas etapas ela tem e se está marcada como recomendada.
    """
    __tablename__ = "activity_plans"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    activity_type = Column(String(30), nullable=False)
    level = Column(Integer, default=1)
    enabled = Column(Boolean, default=True)
    recommended = Column(Boolean, default=False)
    question_count = Column(Integer, default=5)
    time_limit = Column(Integer, default=0)  # minutos no timer visual (0 = sem timer)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    profile = relationship("Profile", back_populates="plans")


class RecommendationDecision(Base):
    """Decisão do adulto sobre uma recomendação (aceitar, ajustar, descartar)."""
    __tablename__ = "recommendation_decisions"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    rec_key = Column(String(60), nullable=False)
    activity_type = Column(String(30), nullable=True)
    action = Column(String(20), nullable=False)  # accept, adjust, dismiss
    level = Column(Integer, nullable=True)
    decided_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_session_id = Column(Integer, default=0)  # última sessão existente quando o adulto decidiu
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="decisions")


class RoutineItem(Base):
    """Etapa da agenda visual de rotina (pictograma + texto curto)."""
    __tablename__ = "routine_items"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    position = Column(Integer, default=0)
    icon = Column(String(16), default="⭐")
    label = Column(String(60), nullable=False)
    time = Column(String(5), nullable=True)  # "08:00"
    duration = Column(Integer, nullable=True)  # minutos no timer visual
    done_on = Column(Date, nullable=True)    # dia em que foi marcada como feita

    profile = relationship("Profile", back_populates="routine")


class ProfileAccess(Base):
    """Acesso de um profissional ao perfil de uma criança, autorizado pelo responsável."""
    __tablename__ = "profile_access"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    professional_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(20), default="pending")  # pending, active, revoked
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)

    profile = relationship("Profile", back_populates="access")
    professional = relationship("User")


class ChildRequest(Base):
    """Pedido feito pela criança na prancha de comunicação (pausa, água, ajuda...)."""
    __tablename__ = "child_requests"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    key = Column(String(20), nullable=False)
    context = Column(String(60), nullable=True)  # ex.: nome da atividade em andamento
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="requests")


class MoodCheck(Base):
    """Emoção que a criança escolheu em "Como estou me sentindo?"."""
    __tablename__ = "mood_checks"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("profiles.id"), nullable=False)
    mood = Column(String(20), nullable=False)
    moment = Column(String(20), default="entrada")  # entrada (ao abrir a área) ou livre (botão na tela inicial)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="moods")
