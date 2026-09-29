# ==========================================
# AI ENGINE - Recomendação baseada em regras e pontuação
# Fundamentado em ABA, TEACCH e educação inclusiva (TCC, seção 4.2)
# ==========================================
#
# Sistema baseado em conhecimento: regras explícitas e uma função de pontuação.
# Toda recomendação sai com a lista de motivos que a produziram e só muda
# alguma coisa para a criança depois que um adulto aceita (RNF10).
#
# Regras de nível (tomada de decisão baseada em dados, ABA):
#   - domínio: acerto >= critério nas N últimas sessões seguidas -> sugerir subir de nível
#   - dificuldade recorrente: 2 das 3 últimas sessões abaixo de 50% -> sugerir descer
#     de nível e aumentar os apoios
#   - caso contrário -> manter e reforçar
#
# Pontuação para sugerir a próxima atividade:
#   + afinidade com os interesses registrados no perfil
#   + meta aberta para a atividade
#   + desempenho na "zona de aprendizagem" (50% a 85%) ou atividade ainda não tentada
#   + variedade: evita repetir as atividades mais recentes

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from data.activity_bank import ACTIVITY_BANK, DEFAULT_ENABLED, activity_name, max_level
from models import ActivityPlan, Goal, Profile, RecommendationDecision, Response, Session, Settings

DEFAULT_MASTERY_THRESHOLD = 85
DEFAULT_MASTERY_SESSIONS = 3
DIFFICULTY_THRESHOLD = 50

# Palavras dos interesses (perfil) que aproximam a criança de cada atividade
INTEREST_KEYWORDS: Dict[str, List[str]] = {
    "colors": ["cor", "cores", "pintar", "pintura", "desenho", "arte", "arco-íris"],
    "shapes": ["forma", "formas", "blocos", "lego", "montar", "geometria"],
    "numbers": ["número", "numeros", "números", "contar", "conta"],
    "math": ["matemática", "matematica", "conta", "contas", "somar"],
    "sequences": ["sequência", "sequencia", "ordem", "trem", "trens", "fila"],
    "patterns": ["padrão", "padroes", "padrões", "música", "musica", "ritmo", "quebra-cabeça"],
    "matching": ["pares", "memória", "memoria", "iguais", "quebra-cabeça"],
    "emotions": ["emoção", "emoções", "emocoes", "amigos", "rostos", "sentimentos"],
    "letters": ["letra", "letras", "ler", "leitura", "livro", "livros", "histórias", "historias"],
    "clock": ["relógio", "relogio", "horas", "tempo"],
    "money": ["dinheiro", "moeda", "moedas", "mercado", "compras", "loja"],
    "categories": ["animais", "animal", "frutas", "comida", "carros", "veículos", "veiculos", "dinossauro", "dinossauros", "bichos"],
}


def _mastery_rules(db: DBSession, profile_id: int):
    settings = db.query(Settings).filter(Settings.profile_id == profile_id).first()
    threshold = (settings.mastery_threshold if settings and settings.mastery_threshold else DEFAULT_MASTERY_THRESHOLD)
    sessions = (settings.mastery_sessions if settings and settings.mastery_sessions else DEFAULT_MASTERY_SESSIONS)
    return threshold, sessions


def _recent_sessions(db: DBSession, profile_id: int, activity_type: str, limit: int) -> List[Session]:
    return (
        db.query(Session)
        .filter(
            Session.profile_id == profile_id,
            Session.activity_type == activity_type,
            Session.is_practice == False,  # noqa: E712
        )
        .order_by(desc(Session.created_at), desc(Session.id))
        .limit(limit)
        .all()
    )


def _plan(db: DBSession, profile_id: int, activity_type: str) -> Optional[ActivityPlan]:
    return db.query(ActivityPlan).filter(
        ActivityPlan.profile_id == profile_id, ActivityPlan.activity_type == activity_type
    ).first()


class AIEngine:
    """Motor de recomendação explicável (regras + pontuação)."""

    @staticmethod
    def analyze_performance(db: DBSession, profile_id: int, activity_type: str) -> dict:
        """Aplicar as regras de nível a uma atividade e explicar a decisão."""
        threshold, needed = _mastery_rules(db, profile_id)
        recent = _recent_sessions(db, profile_id, activity_type, max(needed, 3))

        if len(recent) < 2:
            return {
                "suggested_level": 1,
                "recommendation": "continue",
                "reason": "Ainda há poucas sessões para analisar. Continue praticando.",
                "avg_accuracy": 0,
                "trend": 0,
            }

        plan = _plan(db, profile_id, activity_type)
        current_level = plan.level if plan else recent[0].level
        top_level = max_level(activity_type)
        accuracies = [s.accuracy for s in recent]
        avg_accuracy = sum(accuracies) / len(accuracies)
        trend = AIEngine._calculate_trend(accuracies)

        last_n = accuracies[:needed]
        mastered = len(last_n) >= needed and all(a >= threshold for a in last_n)
        struggling = sum(1 for a in accuracies[:3] if a < DIFFICULTY_THRESHOLD) >= 2

        if mastered and current_level < top_level:
            suggested = current_level + 1
            return {
                "suggested_level": suggested,
                "recommendation": "level_up",
                "reason": (
                    f"Acertou {threshold}% ou mais nas {needed} últimas sessões seguidas "
                    f"(critério de domínio). Sugestão: passar para o nível {suggested}."
                ),
                "avg_accuracy": round(avg_accuracy, 1),
                "trend": round(trend, 1),
            }
        if struggling:
            suggested = max(current_level - 1, 1)
            action = f"voltar ao nível {suggested}" if suggested < current_level else "manter o nível 1"
            return {
                "suggested_level": suggested,
                "recommendation": "attention",
                "reason": (
                    f"Ficou abaixo de {DIFFICULTY_THRESHOLD}% em 2 das 3 últimas sessões. "
                    f"Sugestão: {action} e aumentar o apoio (dicas, Modo Baixo Estímulo)."
                ),
                "avg_accuracy": round(avg_accuracy, 1),
                "trend": round(trend, 1),
            }
        return {
            "suggested_level": current_level,
            "recommendation": "reinforce",
            "reason": f"Acerto médio de {avg_accuracy:.0f}%. Sugestão: manter o nível {current_level} e reforçar.",
            "avg_accuracy": round(avg_accuracy, 1),
            "trend": round(trend, 1),
        }

    @staticmethod
    def identify_error_patterns(db: DBSession, profile_id: int, activity_type: str) -> List[dict]:
        """Padrões que merecem a atenção do adulto."""
        recent = _recent_sessions(db, profile_id, activity_type, 10)
        if len(recent) < 3:
            return []

        patterns = []
        accuracies = [s.accuracy for s in recent]

        if AIEngine._calculate_variance(accuracies) > 400:
            patterns.append({
                "type": "inconsistency",
                "description": "Desempenho oscila muito entre as sessões",
                "suggestion": "Vale observar horário, ambiente e estado emocional nos dias de prática.",
            })

        avg_time = db.query(func.avg(Response.response_time)).filter(
            Response.session_id.in_([s.id for s in recent])
        ).scalar() or 0
        if avg_time > 15000:
            patterns.append({
                "type": "slow_response",
                "description": "Respostas levando mais de 15 segundos",
                "suggestion": "Considere instruções mais curtas, menos etapas ou mais apoio visual.",
            })

        if AIEngine._calculate_trend(accuracies) < -15:
            patterns.append({
                "type": "declining_performance",
                "description": "Queda no acerto nas últimas sessões",
                "suggestion": "Pode ser cansaço ou perda de interesse. Considere pausas ou outra atividade.",
            })
        return patterns

    @staticmethod
    def score_activities(db: DBSession, profile: Profile) -> List[dict]:
        """Pontuar as atividades para sugerir a próxima, com os motivos."""
        interests = (profile.interests or "").lower()
        plans = {p.activity_type: p for p in db.query(ActivityPlan).filter(ActivityPlan.profile_id == profile.id)}
        open_goals = {
            g.activity_type for g in db.query(Goal).filter(Goal.profile_id == profile.id, Goal.completed == False)  # noqa: E712
        }
        last_two = [
            s.activity_type for s in db.query(Session)
            .filter(Session.profile_id == profile.id, Session.is_practice == False)  # noqa: E712
            .order_by(desc(Session.created_at), desc(Session.id)).limit(2)
        ]

        scored = []
        for activity_type in ACTIVITY_BANK:
            plan = plans.get(activity_type)
            enabled = plan.enabled if plan else activity_type in DEFAULT_ENABLED
            if not enabled:
                continue

            score, reasons = 0, []
            matched = [w for w in INTEREST_KEYWORDS.get(activity_type, []) if w in interests]
            if matched:
                score += 3
                reasons.append(f"Combina com os interesses da criança ({matched[0]})")
            if activity_type in open_goals:
                score += 2
                reasons.append("Há uma meta aberta nesta atividade")

            recent = _recent_sessions(db, profile.id, activity_type, 3)
            if not recent:
                score += 1
                reasons.append("Ainda não foi praticada")
            else:
                avg = sum(s.accuracy for s in recent) / len(recent)
                if DIFFICULTY_THRESHOLD <= avg < DEFAULT_MASTERY_THRESHOLD:
                    score += 2
                    reasons.append(f"Está aprendendo: acerto médio de {avg:.0f}%")
                if recent[0].created_at and recent[0].created_at.replace(tzinfo=None) < datetime.utcnow() - timedelta(days=3):
                    score += 1
                    reasons.append("Não pratica há mais de 3 dias")
            if activity_type in last_two:
                score -= 2

            scored.append({"activity": activity_type, "score": score, "reasons": reasons})

        scored.sort(key=lambda a: a["score"], reverse=True)
        return scored

    @staticmethod
    def generate_recommendations(db: DBSession, profile_id: int) -> List[dict]:
        """Montar as recomendações pendentes de decisão do adulto."""
        profile = db.query(Profile).filter(Profile.id == profile_id).first()
        recommendations = []

        played = [
            a for (a,) in db.query(Session.activity_type)
            .filter(Session.profile_id == profile_id, Session.is_practice == False)  # noqa: E712
            .distinct()
        ]
        for activity_type in played:
            analysis = AIEngine.analyze_performance(db, profile_id, activity_type)
            name = activity_name(activity_type)
            plan = _plan(db, profile_id, activity_type)
            current = plan.level if plan else analysis["suggested_level"]

            if analysis["recommendation"] == "level_up":
                recommendations.append({
                    "key": f"level:{activity_type}:{analysis['suggested_level']}",
                    "kind": "level", "type": "positive", "activity": activity_type,
                    "current_level": current, "suggested_level": analysis["suggested_level"],
                    "title": f"{name}: pronto para o nível {analysis['suggested_level']}",
                    "message": analysis["reason"],
                    "reasons": [analysis["reason"]], "priority": "medium",
                })
            elif analysis["recommendation"] == "attention":
                recommendations.append({
                    "key": f"level:{activity_type}:{analysis['suggested_level']}:support",
                    "kind": "level", "type": "attention", "activity": activity_type,
                    "current_level": current, "suggested_level": analysis["suggested_level"],
                    "title": f"{name}: precisa de mais apoio",
                    "message": analysis["reason"],
                    "reasons": [analysis["reason"]], "priority": "high",
                })

            for pattern in AIEngine.identify_error_patterns(db, profile_id, activity_type):
                recommendations.append({
                    "key": f"pattern:{activity_type}:{pattern['type']}",
                    "kind": "pattern", "type": "pattern", "activity": activity_type,
                    "title": f"{name}: {pattern['description']}",
                    "message": pattern["suggestion"],
                    "reasons": [pattern["suggestion"]], "priority": "medium",
                })

        if profile:
            plans = {p.activity_type: p for p in db.query(ActivityPlan).filter(ActivityPlan.profile_id == profile_id)}
            suggestions = [
                a for a in AIEngine.score_activities(db, profile)
                if a["score"] > 0 and a["reasons"] and not (plans.get(a["activity"]) and plans[a["activity"]].recommended)
            ][:2]
            for item in suggestions:
                name = activity_name(item["activity"])
                recommendations.append({
                    "key": f"activity:{item['activity']}",
                    "kind": "activity", "type": "suggestion", "activity": item["activity"],
                    "title": f"Sugerir {name} como próxima atividade",
                    "message": "Se aceitar, a atividade ganha uma estrela de destaque no menu da criança.",
                    "reasons": item["reasons"], "priority": "low",
                })

        recommendations = [r for r in recommendations if not AIEngine._already_decided(db, profile_id, r)]
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 2))
        return recommendations

    @staticmethod
    def _already_decided(db: DBSession, profile_id: int, rec: dict) -> bool:
        """Uma recomendação decidida some até surgir uma sessão nova daquela atividade."""
        decision = (
            db.query(RecommendationDecision)
            .filter(RecommendationDecision.profile_id == profile_id, RecommendationDecision.rec_key == rec["key"])
            .order_by(desc(RecommendationDecision.created_at), desc(RecommendationDecision.id))
            .first()
        )
        if not decision:
            return False
        newer = db.query(Session.id).filter(
            Session.profile_id == profile_id,
            Session.activity_type == rec["activity"],
            Session.id > (decision.last_session_id or 0),
        ).first()
        return newer is None

    @staticmethod
    def _calculate_trend(accuracies: List[float]) -> float:
        """Diferença entre a sessão mais recente e a mais antiga da lista (lista em ordem decrescente)."""
        if len(accuracies) < 2:
            return 0
        return accuracies[0] - accuracies[-1]

    @staticmethod
    def _calculate_variance(values: List[float]) -> float:
        if not values:
            return 0
        mean = sum(values) / len(values)
        return sum((v - mean) ** 2 for v in values) / len(values)
