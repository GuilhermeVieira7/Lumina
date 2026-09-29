# ==========================================
# ROUTER: Resumo do período (topo do Painel dos Adultos)
# ==========================================
# Em vez de muitos números soltos, uma frase que diz como a criança está,
# três números principais e o acerto médio por dia para o gráfico.

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session as DBSession

from auth import get_current_user
from data.activity_bank import activity_name
from data.communication import MOODS_BY_KEY
from database import get_db
from models import ChildRequest, MoodCheck, Session, User
from permissions import get_profile_for
from routers.moods import _local_date

router = APIRouter(prefix="/api/summary", tags=["Resumo"])

MAX_DAYS = 180  # "Tudo": o gráfico mostra no máximo os últimos 6 meses


def _accuracy(sessions) -> Optional[float]:
    correct = sum(s.correct or 0 for s in sessions)
    answered = correct + sum(s.incorrect or 0 for s in sessions)
    return round(correct / answered * 100, 1) if answered else None


def _plural(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def _period_label(days: Optional[int]) -> str:
    if days == 7:
        return "Nos últimos 7 dias"
    if days:
        return f"Nos últimos {days} dias"
    return "Desde o início"


def build_headline(name: str, days: Optional[int], data: dict) -> str:
    """Frase curta, em linguagem simples, para o topo do painel e o WhatsApp."""
    if not data["activities"]:
        return f"{_period_label(days)}, {name} ainda não fez atividades. Que tal começar por uma atividade destacada com ⭐?"
    parts = [f"{_period_label(days)}, {name} fez {_plural(data['activities'], 'atividade', 'atividades')}"]
    if data["accuracy"] is not None:
        text = f"e acertou {round(data['accuracy'])}% de primeira"
        change = data["accuracy_change"]
        if change is not None and abs(change) >= 3:
            text += f", {abs(round(change))} pontos a {'mais' if change > 0 else 'menos'} que no período anterior"
        parts.append(text)
    sentences = [" ".join(parts) + "."]
    if data["best"] and data["support"]:
        sentences.append(f"Foi bem em {data['best']['name']}; {data['support']['name']} precisa de mais apoio.")
    elif data["best"]:
        sentences.append(f"Foi bem em {data['best']['name']}.")
    elif data["support"]:
        sentences.append(f"{data['support']['name']} precisa de mais apoio.")
    if data["hard_days"]:
        sentences.append(f"Teve {_plural(data['hard_days'], 'dia difícil', 'dias difíceis')} segundo o \"Como estou?\".")
    return " ".join(sentences)


@router.get("/{profile_id}")
def get_summary(
    profile_id: int,
    days: Optional[int] = Query(7, ge=1, le=365),
    all_time: bool = False,
    tz: int = Query(0, ge=-840, le=840),
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Resumo do período. Com all_time=true, considera tudo (sem comparação com período anterior)."""
    profile = get_profile_for(db, profile_id, current_user)
    now = datetime.utcnow()
    period = None if all_time else days
    since = now - timedelta(days=period) if period else None

    query = db.query(Session).filter(Session.profile_id == profile_id, Session.is_practice == False)  # noqa: E712
    sessions = [s for s in query.all() if s.created_at and (since is None or s.created_at >= since)]
    previous = []
    if period:
        before = now - timedelta(days=2 * period)
        previous = [s for s in query.filter(Session.created_at >= before, Session.created_at < since).all()]

    accuracy = _accuracy(sessions)
    previous_accuracy = _accuracy(previous)
    change = round(accuracy - previous_accuracy, 1) if accuracy is not None and previous_accuracy is not None else None

    # Melhor atividade e a que precisa de apoio (com pelo menos 2 sessões no período)
    by_activity = defaultdict(list)
    for s in sessions:
        by_activity[s.activity_type].append(s)
    ranked = sorted(
        ({"activity": a, "name": activity_name(a), "accuracy": _accuracy(rows), "sessions": len(rows)}
         for a, rows in by_activity.items() if len(rows) >= 2 and _accuracy(rows) is not None),
        key=lambda r: r["accuracy"], reverse=True,
    )
    best = ranked[0] if ranked and ranked[0]["accuracy"] >= 70 else None
    support = ranked[-1] if ranked and ranked[-1]["accuracy"] < 60 else None
    if best and support and best["activity"] == support["activity"]:
        support = None

    moods = [m for m in db.query(MoodCheck).filter(MoodCheck.profile_id == profile_id).all()
             if m.created_at and (since is None or m.created_at >= since)]
    hard_days = len({_local_date(m.created_at, tz) for m in moods if MOODS_BY_KEY.get(m.mood, {}).get("hard")})
    common = Counter(m.mood for m in moods).most_common(1)
    requests = sum(1 for r in db.query(ChildRequest).filter(ChildRequest.profile_id == profile_id).all()
                   if r.created_at and (since is None or r.created_at >= since))

    # Acerto médio por dia (para o gráfico de evolução)
    per_day = defaultdict(list)
    for s in sessions:
        per_day[_local_date(s.created_at, tz)].append(s)
    today = _local_date(now, tz)
    span = period or min(MAX_DAYS, max(7, (today - min(per_day)).days + 1 if per_day else 7))
    first_day = today - timedelta(days=span - 1)
    daily = []
    for i in range(span):
        day = first_day + timedelta(days=i)
        rows = per_day.get(day, [])
        daily.append({"date": day.isoformat(), "sessions": len(rows), "accuracy": _accuracy(rows)})

    data = {
        "days": period,
        "activities": len(sessions),
        "accuracy": accuracy,
        "previous_accuracy": previous_accuracy,
        "accuracy_change": change,
        "minutes": round(sum(s.total_time or 0 for s in sessions) / 60000),
        "stars": sum(s.stars or 0 for s in sessions),
        "active_days": len(per_day),
        "best": best,
        "support": support,
        "moods": len(moods),
        "hard_days": hard_days,
        "common_mood": MOODS_BY_KEY[common[0][0]]["label"] if common and common[0][0] in MOODS_BY_KEY else None,
        "requests": requests,
        "daily": daily,
    }
    data["headline"] = build_headline(profile.name, period, data)
    return data
