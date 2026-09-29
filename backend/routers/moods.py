# ==========================================
# ROUTER: Como estou me sentindo? (registro de emoções)
# ==========================================
# Ao entrar na sua área, a criança toca no rosto que mostra como está.
# Os adultos veem as emoções por dia no diário e no relatório, para
# relacionar com a rotina e com o desempenho nas atividades.

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from data.communication import MOOD_OPTIONS, MOODS_BY_KEY
from database import get_db
from models import MoodCheck, User
from permissions import get_profile_for
from schemas import MoodCreate, MoodResponse

router = APIRouter(prefix="/api/moods", tags=["Como estou me sentindo"])


def to_response(check: MoodCheck) -> MoodResponse:
    option = MOODS_BY_KEY.get(check.mood, {"icon": "🙂", "label": check.mood})
    return MoodResponse(
        id=check.id, mood=check.mood, icon=option["icon"], label=option["label"],
        moment=check.moment or "entrada", created_at=check.created_at,
    )


def summarize(checks) -> list:
    """Quantas vezes cada emoção foi escolhida, da mais frequente para a menos."""
    counts = Counter(c.mood for c in checks)
    return [
        {"key": key, "icon": MOODS_BY_KEY.get(key, {}).get("icon", "🙂"),
         "label": MOODS_BY_KEY.get(key, {}).get("label", key),
         "color": MOODS_BY_KEY.get(key, {}).get("color", "#999999"),
         "hard": MOODS_BY_KEY.get(key, {}).get("hard", False), "count": count}
        for key, count in counts.most_common()
    ]


def _local_date(moment: datetime, tz_minutes: int):
    """Data no fuso de quem consulta (tz_minutes como no getTimezoneOffset do navegador)."""
    if moment.tzinfo is not None:
        moment = moment.astimezone(timezone.utc).replace(tzinfo=None)
    return (moment - timedelta(minutes=tz_minutes)).date()


@router.get("/options")
def list_options(current_user: User = Depends(get_current_user)):
    """Emoções que aparecem para a criança."""
    return MOOD_OPTIONS


@router.post("", response_model=MoodResponse)
def create_mood(
    data: MoodCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    get_profile_for(db, data.profile_id, current_user)
    if data.mood not in MOODS_BY_KEY:
        raise HTTPException(status_code=400, detail="Emoção desconhecida")
    check = MoodCheck(profile_id=data.profile_id, mood=data.mood, moment=data.moment)
    db.add(check)
    db.commit()
    db.refresh(check)
    return to_response(check)


@router.get("/{profile_id}")
def list_moods(
    profile_id: int,
    days: int = Query(14, ge=1, le=90),
    tz: int = Query(0, ge=-840, le=840),
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Emoções do período: total, contagem por emoção, contagem por dia e as mais recentes."""
    get_profile_for(db, profile_id, current_user)
    today = _local_date(datetime.utcnow(), tz)
    first_day = today - timedelta(days=days - 1)
    # Busca com folga de um dia e filtra pela data local
    since = datetime.utcnow() - timedelta(days=days + 1)
    checks = [
        c for c in db.query(MoodCheck)
        .filter(MoodCheck.profile_id == profile_id, MoodCheck.created_at >= since)
        .order_by(desc(MoodCheck.created_at), desc(MoodCheck.id)).all()
        if c.created_at and _local_date(c.created_at, tz) >= first_day
    ]

    per_day = {first_day + timedelta(days=i): Counter() for i in range(days)}
    for c in checks:
        day = _local_date(c.created_at, tz)
        if day in per_day:
            per_day[day][c.mood] += 1

    return {
        "total": len(checks),
        "hard": sum(1 for c in checks if MOODS_BY_KEY.get(c.mood, {}).get("hard")),
        "summary": summarize(checks),
        "days": [{"date": d.isoformat(), "counts": dict(counts)} for d, counts in per_day.items()],
        "items": [to_response(c) for c in checks[:max(1, min(limit, 100))]],
    }
