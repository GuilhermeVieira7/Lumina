# ==========================================
# ROUTER: Atividades e Questões
# ==========================================

from fastapi import APIRouter
from data.activity_bank import get_activity_list, get_questions

router = APIRouter(prefix="/api/activities", tags=["Atividades"])


@router.get("")
def list_activities():
    """Listar todas as atividades disponíveis."""
    return get_activity_list()


@router.get("/{activity_type}/questions")
def get_activity_questions(activity_type: str, level: int = 1):
    """Obter questões de uma atividade específica por nível."""
    questions = get_questions(activity_type, level)
    if not questions:
        return {"error": "Atividade ou nível não encontrado", "questions": []}
    return {"activity_type": activity_type, "level": level, "questions": questions}
