# ==========================================
# MODELS - Modelos do Banco de Dados
# Sistema de Apoio Educacional para TEA
# ==========================================

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, Date
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """Usuários do sistema (pais, responsáveis, terapeutas)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="parent")  # parent, therapist, admin
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
    diagnosis = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="profiles")
    sessions = relationship("Session", back_populates="profile", cascade="all, delete-orphan")
    settings = relationship("Settings", back_populates="profile", uselist=False, cascade="all, delete-orphan")
    achievements = relationship("Achievement", back_populates="profile", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="profile", cascade="all, delete-orphan")
    notes = relationship("Note", back_populates="profile", cascade="all, delete-orphan")


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

    profile = relationship("Profile", back_populates="settings")


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
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    profile = relationship("Profile", back_populates="notes")
