# ==========================================
# ROUTER: Sessões de Atividade
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, desc
from typing import List, Optional
from datetime import datetime, timedelta

from database import get_db
from data.activity_bank import ACTIVITY_AREA, AREAS, activity_name
from models import User, Profile, Session, Response as ResponseModel, Note, Goal, ChildRequest, MoodCheck
from schemas import SessionCreate, SessionResponse, SessionUpdate
from routers.goals import refresh_goals
from routers.requests import summarize
from routers.moods import summarize as summarize_moods
from auth import get_current_user
from permissions import get_profile_for

router = APIRouter(prefix="/api/sessions", tags=["Sessões"])


@router.post("", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Salvar uma sessão completa de atividade com todas as respostas."""
    get_profile_for(db, session_data.profile_id, current_user)

    # Calcular accuracy e estrelas
    total = session_data.total_questions
    accuracy = (session_data.correct / total * 100) if total > 0 else 0

    stars = 0
    if accuracy >= 90:
        stars = 3
    elif accuracy >= 70:
        stars = 2
    elif accuracy >= 50:
        stars = 1

    # Criar sessão
    session = Session(
        profile_id=session_data.profile_id,
        activity_type=session_data.activity_type,
        level=session_data.level,
        total_questions=session_data.total_questions,
        correct=session_data.correct,
        incorrect=session_data.incorrect,
        accuracy=round(accuracy, 1),
        total_time=session_data.total_time,
        stars=stars,
        is_practice=session_data.is_practice,
        reward=(session_data.reward or "").strip() or None,
        timed_out=session_data.timed_out,
    )
    db.add(session)
    db.flush()  # obter ID sem commitar

    # Salvar respostas individuais
    for resp in session_data.responses:
        response = ResponseModel(
            session_id=session.id,
            question_index=resp.question_index,
            is_correct=resp.is_correct,
            response_time=resp.response_time,
            attempts=resp.attempts,
        )
        db.add(response)

    db.commit()
    db.refresh(session)
    refresh_goals(db, session_data.profile_id)
    return session


HELP_LEVELS = {"none", "verbal", "gesture", "physical"}


@router.patch("/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: int,
    data: SessionUpdate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Registrar o nível de ajuda dado pelo adulto durante a sessão (RF08)."""
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    get_profile_for(db, session.profile_id, current_user)
    if data.help_level is not None:
        if data.help_level not in HELP_LEVELS:
            raise HTTPException(status_code=400, detail="Nível de ajuda inválido")
        session.help_level = data.help_level
    db.commit()
    db.refresh(session)
    return session


def _since(days: Optional[int]):
    return datetime.utcnow() - timedelta(days=days) if days else None


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    profile_id: int,
    activity_type: str = None,
    limit: int = 50,
    days: Optional[int] = None,
    include_practice: bool = True,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar histórico de sessões de um perfil (mais recentes primeiro)."""
    get_profile_for(db, profile_id, current_user)

    query = db.query(Session).filter(Session.profile_id == profile_id)
    if activity_type:
        query = query.filter(Session.activity_type == activity_type)
    if not include_practice:
        query = query.filter(Session.is_practice == False)  # noqa: E712
    since = _since(days)
    if since:
        query = query.filter(Session.created_at >= since)

    return query.order_by(desc(Session.created_at), desc(Session.id)).limit(limit).all()


@router.get("/stats")
def get_stats(
    profile_id: int,
    days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Estatísticas agregadas de um perfil, opcionalmente só dos últimos N dias."""
    get_profile_for(db, profile_id, current_user)
    since = _since(days)
    period = [Session.created_at >= since] if since else []

    total_sessions = db.query(func.count(Session.id)).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).scalar() or 0

    total_correct = db.query(func.sum(Session.correct)).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).scalar() or 0

    total_incorrect = db.query(func.sum(Session.incorrect)).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).scalar() or 0

    total_time = db.query(func.sum(Session.total_time)).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).scalar() or 0

    total_stars = db.query(func.sum(Session.stars)).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).scalar() or 0

    total = total_correct + total_incorrect
    accuracy = round((total_correct / total * 100), 1) if total > 0 else 0

    # Adicionar médias para o dashboard
    responses = db.query(
        func.avg(ResponseModel.response_time).label("avg_time"),
        func.avg(ResponseModel.attempts).label("avg_attempts")
    ).join(Session).filter(
        Session.profile_id == profile_id, Session.is_practice == False, *period
    ).first()
    
    avg_response_time = round(responses.avg_time or 0, 1)
    avg_attempts = round(responses.avg_attempts or 1.0, 1)

    # Breakdown por atividade
    activities_raw = (
        db.query(
            Session.activity_type,
            func.count(Session.id).label("sessions"),
            func.sum(Session.correct).label("correct"),
            func.sum(Session.incorrect).label("incorrect"),
            func.sum(Session.stars).label("stars"),
            func.max(Session.level).label("current_level"),
        )
        .filter(Session.profile_id == profile_id, Session.is_practice == False, *period)
        .group_by(Session.activity_type)
        .all()
    )

    activities_breakdown = {}
    for row in activities_raw:
        total_act = (row.correct or 0) + (row.incorrect or 0)
        activities_breakdown[row.activity_type] = {
            "sessions": row.sessions,
            "correct": row.correct or 0,
            "incorrect": row.incorrect or 0,
            "accuracy": round(((row.correct or 0) / total_act * 100), 1) if total_act > 0 else 0,
            "stars": row.stars or 0,
            "current_level": row.current_level or 1,
            "name": activity_name(row.activity_type),
            "area": ACTIVITY_AREA.get(row.activity_type, "cognicao"),
        }

    # Agrupamento pelas áreas de habilidade do TCC
    areas_breakdown = {}
    for key, area in AREAS.items():
        rows = [a for a in activities_breakdown.values() if a["area"] == key]
        correct = sum(a["correct"] for a in rows)
        answered = correct + sum(a["incorrect"] for a in rows)
        areas_breakdown[key] = {
            "name": area["name"],
            "icon": area["icon"],
            "sessions": sum(a["sessions"] for a in rows),
            "accuracy": round(correct / answered * 100, 1) if answered else None,
        }

    help_counts = dict(
        db.query(Session.help_level, func.count(Session.id))
        .filter(Session.profile_id == profile_id, Session.is_practice == False, Session.help_level.isnot(None), *period)
        .group_by(Session.help_level)
        .all()
    )

    return {
        "total_activities": total_sessions,
        "total_correct": total_correct,
        "total_incorrect": total_incorrect,
        "accuracy": accuracy,
        "total_time": total_time,
        "total_stars": total_stars,
        "avg_response_time": avg_response_time,
        "avg_attempts": avg_attempts,
        "activities_breakdown": activities_breakdown,
        "areas_breakdown": areas_breakdown,
        "help_levels": help_counts,
        "days": days,
        "recent_sessions": [],
    }

@router.get("/export/pdf")
def export_pdf(
    profile_id: int,
    days: Optional[int] = None,
    tz: int = 0,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Relatório de acompanhamento em PDF (RF12), para compartilhar com escola e equipe."""
    try:
        from report_pdf import build_report
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca fpdf2 não instalada no servidor.")
    from ai_engine import AIEngine
    from routers.summary import get_summary

    profile = get_profile_for(db, profile_id, current_user)
    stats = get_stats(profile_id=profile_id, days=days, current_user=current_user, db=db)
    summary = get_summary(profile_id=profile_id, days=days or 7, all_time=not days, tz=tz,
                          current_user=current_user, db=db)
    notes = (
        db.query(Note).filter(Note.profile_id == profile_id)
        .order_by(desc(Note.created_at), desc(Note.id)).limit(6).all()
    )
    refresh_goals(db, profile_id)
    goals = db.query(Goal).filter(Goal.profile_id == profile_id).all()
    request_query = db.query(ChildRequest).filter(ChildRequest.profile_id == profile_id)
    mood_query = db.query(MoodCheck).filter(MoodCheck.profile_id == profile_id)
    since = _since(days)
    if since:
        request_query = request_query.filter(ChildRequest.created_at >= since)
        mood_query = mood_query.filter(MoodCheck.created_at >= since)

    content = build_report(
        profile=profile, days=days, summary=summary, stats=stats, goals=goals, notes=notes,
        requests=summarize(request_query.all()), moods=summarize_moods(mood_query.all()),
        recs=AIEngine.generate_recommendations(db, profile_id),
        area_names={k: a["name"] for k, a in AREAS.items()}, activity_name=activity_name,
    )
    safe_name = "".join(c if c.isalnum() else "_" for c in profile.name)
    return Response(
        content=content,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_lumina_{safe_name}.pdf"},
    )
