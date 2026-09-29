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

HELP_LABELS = {"none": "Sem ajuda", "verbal": "Dica verbal", "gesture": "Gesto/apontar", "physical": "Ajuda física"}


def _latin1(text) -> str:
    """As fontes padrão do PDF só aceitam Latin-1; emojis e afins viram '?'."""
    return str(text).encode("latin-1", "replace").decode("latin-1")


@router.get("/export/pdf")
def export_pdf(
    profile_id: int,
    days: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Relatório de acompanhamento em PDF (RF12), para compartilhar com escola e equipe."""
    try:
        from fpdf import FPDF
        from fpdf.enums import XPos, YPos
    except ImportError:
        raise HTTPException(status_code=500, detail="Biblioteca fpdf2 não instalada no servidor.")

    profile = get_profile_for(db, profile_id, current_user)
    stats = get_stats(profile_id=profile_id, days=days, current_user=current_user, db=db)
    notes = (
        db.query(Note).filter(Note.profile_id == profile_id)
        .order_by(desc(Note.created_at), desc(Note.id)).limit(8).all()
    )
    refresh_goals(db, profile_id)
    goals = db.query(Goal).filter(Goal.profile_id == profile_id).all()
    request_query = db.query(ChildRequest).filter(ChildRequest.profile_id == profile_id)
    since = _since(days)
    if since:
        request_query = request_query.filter(ChildRequest.created_at >= since)
    request_summary = summarize(request_query.all())
    mood_query = db.query(MoodCheck).filter(MoodCheck.profile_id == profile_id)
    if since:
        mood_query = mood_query.filter(MoodCheck.created_at >= since)
    mood_summary = summarize_moods(mood_query.all())

    SYSTEM_NAME = "Lumina TEA Edu"
    NEXT = dict(new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(41, 128, 185)
            self.cell(0, 10, SYSTEM_NAME, align="L", **NEXT)
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, _latin1("Relatório de Acompanhamento Educacional"), align="L", **NEXT)
            self.line(10, 26, 200, 26)
            self.ln(10)

        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(169, 169, 169)
            self.cell(0, 10, _latin1(f"Documento confidencial gerado por {SYSTEM_NAME} - Página {self.page_no()}"), align="C")

    pdf = PDF()
    pdf.add_page()

    def section(title):
        pdf.ln(4)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_fill_color(41, 128, 185)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 9, _latin1(f" {title}"), border=0, fill=True, **NEXT)
        pdf.set_text_color(44, 62, 80)
        pdf.ln(1)

    def metric_line(label, value):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 7, _latin1(f" {label}"), border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, _latin1(value), border=0, **NEXT)

    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, _latin1(f"Criança: {profile.name}"), align="C", **NEXT)
    pdf.set_font("Helvetica", "", 10)
    period = f"últimos {days} dias" if days else "todo o histórico"
    pdf.cell(0, 6, _latin1(f"Período: {period}  |  Emitido em {datetime.now().strftime('%d/%m/%Y')}"), align="C", **NEXT)

    section("Visão geral")
    metric_line("Atividades concluídas:", stats["total_activities"])
    metric_line("Taxa de acerto:", f"{stats['accuracy']}%")
    metric_line("Estrelas:", stats["total_stars"])
    total_minutes = stats["total_time"] // 60000
    metric_line("Tempo de prática:", f"{total_minutes} min" if total_minutes < 60 else f"{total_minutes // 60}h {total_minutes % 60}min")
    metric_line("Tempo médio por resposta:", f"{stats['avg_response_time'] / 1000:.1f} s")
    metric_line("Tentativas por questão:", stats["avg_attempts"])
    if stats["help_levels"]:
        metric_line("Ajuda registrada:", ", ".join(f"{HELP_LABELS.get(k, k)}: {v}" for k, v in stats["help_levels"].items()))

    section("Por área de habilidade")
    for area in stats["areas_breakdown"].values():
        value = f"{area['accuracy']}% de acerto em {area['sessions']} sessões" if area["accuracy"] is not None else "sem registros"
        metric_line(f"{area['name']}:", value)

    section("Por atividade")
    if not stats["activities_breakdown"]:
        pdf.set_font("Helvetica", "I", 11)
        pdf.cell(0, 8, _latin1(" Nenhuma atividade registrada ainda."), **NEXT)
    for data in stats["activities_breakdown"].values():
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(55, 8, _latin1(f" {data['name']}"), border="B")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, _latin1(f"Acerto: {data['accuracy']}%  |  Sessões: {data['sessions']}  |  Nível: {data['current_level']}"), border="B", **NEXT)

    if goals:
        section("Metas")
        for goal in goals:
            status = "concluída" if goal.completed else f"{goal.current_value:g} de {goal.target_value:g}"
            metric_line(f"{activity_name(goal.activity_type)}:", f"{goal.description or goal.target_type} ({status})")

    if request_summary:
        section("Pedidos feitos pela criança na prancha")
        metric_line("Total no período:", sum(r["count"] for r in request_summary))
        metric_line("Mais frequentes:", ", ".join(f"{r['label']} ({r['count']})" for r in request_summary[:6]))

    if mood_summary:
        section("Como a criança disse que estava se sentindo")
        total_moods = sum(m["count"] for m in mood_summary)
        metric_line("Registros no período:", total_moods)
        for m in mood_summary:
            metric_line(f"{m['label']}:", f"{m['count']} {'vez' if m['count'] == 1 else 'vezes'}")
        hard = sum(m["count"] for m in mood_summary if m["hard"])
        metric_line("Emoções difíceis:", f"{hard} de {total_moods} ({round(100 * hard / total_moods)}%)")

    if notes:
        section("Diário de observações (mais recentes)")
        for note in notes:
            pdf.set_font("Helvetica", "B", 10)
            when = note.created_at.strftime("%d/%m/%Y") if note.created_at else ""
            pdf.cell(0, 6, _latin1(f" {when} - {note.author or ''}"), **NEXT)
            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 5, _latin1(f" {note.content}"), **NEXT)
            pdf.ln(1)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(127, 140, 141)
    nota = ("Este relatório apoia o acompanhamento e não é diagnóstico. As informações devem ser "
            "interpretadas pelos responsáveis e pela equipe que acompanha a criança.")
    pdf.multi_cell(0, 5, text=_latin1(nota))

    safe_name = "".join(c if c.isalnum() else "_" for c in profile.name)
    return Response(
        content=bytes(pdf.output()),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=relatorio_lumina_{safe_name}.pdf"},
    )
