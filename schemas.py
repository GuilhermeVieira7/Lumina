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
    password: str = Field(..., min_length=4)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# ---- Profile Schemas ----

class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    avatar: str = "😊"
    birth_date: Optional[date] = None
    diagnosis: Optional[str] = None

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    avatar: Optional[str] = None
    birth_date: Optional[date] = None
    diagnosis: Optional[str] = None

class ProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    avatar: str
    birth_date: Optional[date] = None
    diagnosis: Optional[str] = None
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
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Settings Schemas ----

class SettingsUpdate(BaseModel):
    difficulty: Optional[int] = None
    auto_adjust: Optional[bool] = None
    sound_enabled: Optional[bool] = None
    font_size: Optional[str] = None
    theme: Optional[str] = None
    language: Optional[str] = None
    auto_backup: Optional[bool] = None
    alerts_enabled: Optional[bool] = None

class SettingsResponse(BaseModel):
    difficulty: int
    auto_adjust: bool
    sound_enabled: bool
    font_size: str
    theme: str
    language: str
    auto_backup: bool
    alerts_enabled: bool

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
    type: str  # positive, attention, pattern, general
    activity: Optional[str] = None
    title: str
    message: str
    priority: str  # high, medium, low


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
