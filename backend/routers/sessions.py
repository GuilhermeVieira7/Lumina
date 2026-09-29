# ==========================================
# ROUTER: Sessões de Atividade
# ==========================================

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, desc
from typing import List

from database import get_db
from models import User, Profile, Session, Response as ResponseModel
from schemas import SessionCreate, SessionResponse
from auth import get_current_user

router = APIRouter(prefix="/api/sessions", tags=["Sessões"])


@router.post("", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Salvar uma sessão completa de atividade com todas as respostas."""
    # Verificar se o perfil pertence ao usuário
    profile = db.query(Profile).filter(
        Profile.id == session_data.profile_id,
        Profile.user_id == current_user.id,
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

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
    return session


@router.get("", response_model=List[SessionResponse])
def list_sessions(
    profile_id: int,
    activity_type: str = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Listar histórico de sessões de um perfil."""
    # Verificar ownership
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    query = db.query(Session).filter(Session.profile_id == profile_id)
    if activity_type:
        query = query.filter(Session.activity_type == activity_type)

    sessions = query.order_by(desc(Session.created_at)).limit(limit).all()
    return sessions


@router.get("/stats")
def get_stats(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Estatísticas agregadas de um perfil."""
    profile = db.query(Profile).filter(
        Profile.id == profile_id, Profile.user_id == current_user.id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    total_sessions = db.query(func.count(Session.id)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total_correct = db.query(func.sum(Session.correct)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total_incorrect = db.query(func.sum(Session.incorrect)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total_time = db.query(func.sum(Session.total_time)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total_stars = db.query(func.sum(Session.stars)).filter(
        Session.profile_id == profile_id, Session.is_practice == False
    ).scalar() or 0

    total = total_correct + total_incorrect
    accuracy = round((total_correct / total * 100), 1) if total > 0 else 0

    # Adicionar médias para o dashboard
    responses = db.query(
        func.avg(ResponseModel.response_time).label("avg_time"),
        func.avg(ResponseModel.attempts).label("avg_attempts")
    ).join(Session).filter(
        Session.profile_id == profile_id, Session.is_practice == False
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
        .filter(Session.profile_id == profile_id, Session.is_practice == False)
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
        }

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
        "recent_sessions": [],
    }

@router.get("/export/pdf")
def export_pdf(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: DBSession = Depends(get_db),
):
    """Gerar um relatorio PDF de acompanhamento clinico escolar."""
    try:
        from fpdf import FPDF
    except ImportError:
        raise HTTPException(status_code=500, detail="FPDF2 library not available on server.")
        
    stats = get_stats(profile_id=profile_id, current_user=current_user, db=db)
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    
    SYSTEM_NAME = "Lumina TEA Edu"

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 18)
            self.set_text_color(41, 128, 185)
            self.cell(0, 10, SYSTEM_NAME, ln=True, align="L")
            self.set_font("Helvetica", "I", 10)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, "Relatório Analítico de Desenvolvimento Funcional", ln=True, align="L")
            self.line(10, 26, 200, 26)
            self.ln(10)
            
        def footer(self):
            self.set_y(-15)
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(169, 169, 169)
            self.cell(0, 10, f"Documento confidencial gerado por {SYSTEM_NAME} - Página {self.page_no()}", align="C")

    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 10, f"ESTUDANTE: {profile.name.upper()}", ln=True, align="C")
    pdf.ln(5)
    
    # Bloco Visao Geral
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(236, 240, 241)
    pdf.cell(0, 10, " Visão Geral de Desempenho", border=1, fill=True, ln=True)
    
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(44, 62, 80)
    
    # helper para linha
    def metric_line(label, value):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(80, 8, f" {label}", border=0)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, str(value), border=0, ln=True)

    metric_line("Total de Atividades Concluídas:", stats['total_activities'])
    metric_line("Taxa de Acerto Consolidada:", f"{stats['accuracy']}%")
    metric_line("Estrelas Acumuladas:", stats['total_stars'])
    
    # Formatar tempo total corretamente (ms -> min/h)
    total_minutes = stats['total_time'] // 60000
    if total_minutes < 60:
        time_str = f"{total_minutes} minutos"
    else:
        hours = total_minutes // 60
        mins = total_minutes % 60
        time_str = f"{hours}h {mins}m"
    metric_line("Tempo Total de Pratica:", time_str)
    
    metric_line("Tempo Tipico de Resposta:", f"{stats['avg_response_time']} ms")
    metric_line("Tentativas Medias / Questao:", stats['avg_attempts'])
    
    if profile.diagnosis:
        metric_line("Diagnostico Clinico:", profile.diagnosis)
    
    
    # Bloco Detalhado
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 10, " Desempenho Clínico por Habilidade", border=1, fill=True, ln=True)
    
    pdf.set_text_color(44, 62, 80)
    if not stats['activities_breakdown']:
         pdf.set_font("Helvetica", "I", 11)
         pdf.cell(0, 10, " Nenhum registro de habilidade treinado ainda.", ln=True)
         
    for act, data in stats['activities_breakdown'].items():
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(60, 10, f" {act.capitalize()}", border="B")
        
        pdf.set_font("Helvetica", "", 11)
        res = f"Acerto: {data['accuracy']}%  |  Sessões: {data['sessions']}  |  Nível Atual: {data['current_level']}"
        pdf.cell(0, 10, res, border="B", ln=True)
        
    pdf.ln(15)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(127, 140, 141)
    nota = ("Nota: Este relatório serve como instrumento analítico de rastreamento do esforço cognitivo e adaptação "
            "funcional. Deve ser interpretado por equipe multidisciplinar ou terapeuta responsável.")
    pdf.multi_cell(0, 5, text=nota)
        
    pdf_content = bytes(pdf.output())
    return Response(
        content=pdf_content, 
        media_type="application/pdf", 
        headers={"Content-Disposition": f"attachment; filename=relatorio_lumina_{profile.name.replace(' ','_')}.pdf"}
    )
