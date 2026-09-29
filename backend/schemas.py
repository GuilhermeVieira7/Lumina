# ==========================================
# SCHEMAS - Validação Pydantic
# Sistema de Apoio Educacional para TEA
# ==========================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ---- Auth Schemas ----

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: str = "parent"  # parent (responsável) ou therapist (profissional)
    consent: bool = False  # aceite do termo de consentimento (LGPD)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    consent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class PasswordCheck(BaseModel):
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---- Profile Schemas ----

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    avatar: str = "😊"
    birth_date: Optional[date] = None
    interests: Optional[str] = Field(None, max_length=300)
    sensory_notes: Optional[str] = Field(None, max_length=300)
    communication: Optional[str] = Field(None, max_length=30)

class ProfileUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    avatar: Optional[str] = None
    birth_date: Optional[date] = None
    interests: Optional[str] = Field(None, max_length=300)
    sensory_notes: Optional[str] = Field(None, max_length=300)
    communication: Optional[str] = Field(None, max_length=30)

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    avatar: str
    birth_date: Optional[date] = None
    interests: Optional[str] = None
    sensory_notes: Optional[str] = None
    communication: Optional[str] = None
    is_owner: bool = True
    owner_name: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# ---- Session Schemas ----

class ResponseCreate(BaseModel):
    question_index: int
    is_correct: bool
    response_time: int  # ms
    attempts: int = 1

class SessionCreate(BaseModel):
    profile_id: int
    activity_type: str
    level: int = 1
    total_questions: int
    correct: int
    incorrect: int
    total_time: int  # ms
    is_practice: bool = False
    reward: Optional[str] = Field(None, max_length=60)
    timed_out: bool = False
    responses: List[ResponseCreate] = []

class SessionResponse(BaseModel):
    id: int
    profile_id: int
    activity_type: str
    level: int
    total_questions: int
    correct: int
    incorrect: int
    accuracy: float
    total_time: int
    stars: int
    is_practice: bool
    help_level: Optional[str] = None
    reward: Optional[str] = None
    timed_out: bool = False
    created_at: datetime

    class Config:
        from_attributes = True

class SessionUpdate(BaseModel):
    help_level: Optional[str] = None  # none, verbal, gesture, physical


# ---- Settings Schemas ----

class RewardItem(BaseModel):
    """Prêmio do quadro de fichas: figura + nome curto."""
    icon: str = Field(..., min_length=1, max_length=16)
    label: str = Field(..., min_length=1, max_length=30)


class SettingsUpdate(BaseModel):
    difficulty: Optional[int] = None
    auto_adjust: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    font_size: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    auto_backup: Optional[bool] = None
    alerts_enabled: Optional[bool] = None
    voice_enabled: Optional[bool] = None
    low_stimulus: Optional[bool] = None
    mastery_threshold: Optional[int] = Field(None, ge=50, le=100)
    mastery_sessions: Optional[int] = Field(None, ge=1, le=10)
    token_board: Optional[bool] = None
    request_board: Optional[bool] = None
    rewards: Optional[List["RewardItem"]] = Field(None, min_length=1, max_length=12)
    requests: Optional[List[str]] = Field(None, min_length=1, max_length=20)

class SettingsResponse(BaseModel):
    difficulty: int
    auto_adjust: bool
    sound_enabled: bool
    font_size: str
    theme: str
    language: str
    auto_backup: bool
    alerts_enabled: bool
    voice_enabled: bool = False
    low_stimulus: bool = False
    mastery_threshold: int = 85
    mastery_sessions: int = 3
    token_board: bool = True
    request_board: bool = True
    rewards: List["RewardItem"] = []
    requests: List[str] = []

    class Config:
        from_attributes = True


# ---- Achievement Schemas ----

class AchievementResponse(BaseModel):
    badge_id: str
    name: str
    icon: str
    description: str
    unlocked: bool
    unlocked_at: Optional[datetime] = None

class AchievementCheckResponse(BaseModel):
    newly_unlocked: List[AchievementResponse]
    all_achievements: List[AchievementResponse]


# ---- Goal Schemas ----

class GoalCreate(BaseModel):
    profile_id: int
    activity_type: str
    target_type: str  # accuracy, stars, sessions
    target_value: float
    description: Optional[str] = None

class GoalResponse(BaseModel):
    id: int
    profile_id: int
    activity_type: str
    target_type: str
    target_value: float
    current_value: float
    description: Optional[str]
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ---- AI / Recommendation Schemas ----

class AIAnalysis(BaseModel):
    suggested_level: int
    recommendation: str  # level_up, level_down, reinforce, attention, continue
    reason: str
    avg_accuracy: Optional[float] = None
    trend: Optional[float] = None

class ErrorPattern(BaseModel):
    type: str
    description: str
    suggestion: str

class Recommendation(BaseModel):
    key: str
    kind: str  # level, activity, pattern, general
    type: str  # positive, attention, pattern, general, suggestion
    activity: Optional[str] = None
    current_level: Optional[int] = None
    suggested_level: Optional[int] = None
    title: str
    message: str
    reasons: List[str] = []
    priority: str  # high, medium, low

class RecommendationDecisionIn(BaseModel):
    key: str
    activity_type: Optional[str] = None
    action: str  # accept, adjust, dismiss
    level: Optional[int] = Field(None, ge=1, le=10)


# ---- Plano de atividades ----

class PlanResponse(BaseModel):
    activity_type: str
    name: str
    icon: str
    area: str
    max_level: int
    level: int
    enabled: bool
    recommended: bool
    question_count: int
    time_limit: int = 0

class PlanUpdate(BaseModel):
    level: Optional[int] = Field(None, ge=1, le=10)
    enabled: Optional[bool] = None
    recommended: Optional[bool] = None
    question_count: Optional[int] = Field(None, ge=2, le=10)
    time_limit: Optional[int] = Field(None, ge=0, le=30)  # minutos; 0 desliga o timer


# ---- Diário (notas) ----

class NoteCreate(BaseModel):
    profile_id: int
    content: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[int] = None

class NoteResponse(BaseModel):
    id: int
    profile_id: int
    session_id: Optional[int] = None
    activity_type: Optional[str] = None
    content: str
    author: Optional[str] = None
    author_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Rotina visual ----

class RoutineItemCreate(BaseModel):
    profile_id: int
    icon: str = Field("⭐", max_length=16)
    label: str = Field(..., min_length=1, max_length=60)
    time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    duration: Optional[int] = Field(None, ge=1, le=120)  # minutos no timer visual

class RoutineItemUpdate(BaseModel):
    icon: Optional[str] = Field(None, max_length=16)
    label: Optional[str] = Field(None, min_length=1, max_length=60)
    time: Optional[str] = Field(None, pattern=r"^(\d{2}:\d{2})?$")
    position: Optional[int] = None
    duration: Optional[int] = Field(None, ge=0, le=120)  # 0 remove o timer

class RoutineItemResponse(BaseModel):
    id: int
    profile_id: int
    position: int
    icon: str
    label: str
    time: Optional[str] = None
    duration: Optional[int] = None
    done_today: bool = False


# ---- Prancha de pedidos ----

class ChildRequestCreate(BaseModel):
    profile_id: int
    key: str = Field(..., min_length=1, max_length=20)
    context: Optional[str] = Field(None, max_length=60)

class ChildRequestResponse(BaseModel):
    id: int
    key: str
    icon: str
    label: str
    context: Optional[str] = None
    created_at: datetime


# ---- Acesso de profissionais ----

class AccessInvite(BaseModel):
    profile_id: int
    professional: str = Field(..., min_length=3, max_length=120)  # usuário ou email

class AccessResponse(BaseModel):
    id: int
    profile_id: int
    profile_name: str
    professional_id: int
    professional_name: str
    owner_name: str
    status: str
    created_at: datetime


# ---- Dashboard / Stats Schemas ----

class DashboardStats(BaseModel):
    total_activities: int
    total_correct: int
    total_incorrect: int
    accuracy: float
    total_time: int
    total_stars: int
    avg_response_time: float = 0.0
    avg_attempts: float = 1.0
    activities_breakdown: dict
    recent_sessions: List[SessionResponse]
