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
#   - domínio com ajuda: acertou, mas com gesto ou ajuda física em alguma dessas sessões
#     -> antes de subir, sugerir retirar a ajuda aos poucos (esvanecimento de dicas, ABA)
#   - dificuldade recorrente: 2 das 3 últimas sessões abaixo de 50% -> sugerir descer
#     de nível e aumentar os apoios
#   - caso contrário -> manter e reforçar
#
# Padrões que cruzam dados (para o adulto observar):
#   - oscilação grande, respostas lentas, queda no acerto
#   - emoções x desempenho: acerto bem menor nos dias em que a criança disse
#     estar triste, brava, com medo ou cansada ("Como estou?")
#
# Pontuação para sugerir a próxima atividade:
#   + afinidade com os interesses registrados no perfil
#   + meta aberta para a atividade
#   + desempenho na "zona de aprendizagem" (50% a 85%) ou atividade ainda não tentada
#   + variedade: evita repetir as atividades mais recentes

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session as DBSession

from data.activity_bank import ACTIVITY_BANK, DEFAULT_ENABLED, activity_name, max_level
from data.communication import MOODS_BY_KEY
from models import ActivityPlan, Goal, MoodCheck, Profile, RecommendationDecision, Response, Session, Settings

DEFAULT_MASTERY_THRESHOLD = 85
DEFAULT_MASTERY_SESSIONS = 3
DIFFICULTY_THRESHOLD = 50
MOOD_GAP = 15          # pontos de acerto a menos nos dias difíceis para virar alerta
MOOD_WINDOW_DAYS = 30

# Nível de ajuda registrado pelo adulto em cada sessão (RF08), do mais ao menos independente
HELP_LABELS = {"none": "sem ajuda", "verbal": "dica verbal", "gesture": "gesto", "physical": "ajuda física"}
HEAVY_HELP = {"gesture", "physical"}


def to_utc(moment: datetime) -> datetime:
    """SQLite devolve datas sem fuso e o PostgreSQL com fuso: compara tudo em UTC sem fuso."""
    if moment is not None and moment.tzinfo is not None:
        return moment.astimezone(timezone.utc).replace(tzinfo=None)
    return moment


def accuracy_of(sessions) -> Optional[float]:
    """Acerto de primeira somando as questões das sessões (e não a média das porcentagens)."""
    correct = sum(s.correct or 0 for s in sessions)
    answered = correct + sum(s.incorrect or 0 for s in sessions)
    return round(correct / answered * 100, 1) if answered else None


def independence_of(sessions) -> Optional[float]:
    """% das sessões com ajuda registrada em que a criança fez sem ajuda."""
    helped = [s for s in sessions if s.help_level]
    if not helped:
        return None
    return round(sum(1 for s in helped if s.help_level == "none") / len(helped) * 100, 1)

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

        # Acertar com a mão do adulto guiando não é domínio: primeiro retirar a ajuda
        heavy = [s.help_level for s in recent[:needed] if s.help_level in HEAVY_HELP]
        if mastered and heavy:
            kinds = " e ".join(sorted({HELP_LABELS[h] for h in heavy}))
            return {
                "suggested_level": current_level,
                "recommendation": "fade_help",
                "reason": (
                    f"Acertou {threshold}% ou mais nas {needed} últimas sessões, mas precisou de {kinds} "
                    f"em {len(heavy)} delas. Antes de subir de nível, diminua a ajuda aos poucos "
                    "(física → gesto → dica verbal → sem ajuda)."
                ),
                "avg_accuracy": round(avg_accuracy, 1),
                "trend": round(trend, 1),
            }

        if mastered and current_level < top_level:
            suggested = current_level + 1
            unregistered = sum(1 for s in recent[:needed] if not s.help_level)
            help_note = (
                " Registre a ajuda dada nas sessões para a sugestão considerar também a independência."
                if unregistered else " Fez sem gesto nem ajuda física."
            )
            return {
                "suggested_level": suggested,
                "recommendation": "level_up",
                "reason": (
                    f"Acertou {threshold}% ou mais nas {needed} últimas sessões seguidas "
                    f"(critério de domínio). Sugestão: passar para o nível {suggested}.{help_note}"
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
    def mood_performance(db: DBSession, profile_id: int, days: int = MOOD_WINDOW_DAYS) -> Optional[dict]:
        """Comparar o acerto nos dias difíceis ("Como estou?") com os outros dias.

        Só compara com pelo menos 2 sessões de cada lado. Devolve None sem dados suficientes.
        """
        since = datetime.utcnow() - timedelta(days=days)
        moods = [m for m in db.query(MoodCheck).filter(MoodCheck.profile_id == profile_id).all()
                 if m.created_at and to_utc(m.created_at) >= since]
        hard_moods = [m for m in moods if MOODS_BY_KEY.get(m.mood, {}).get("hard")]
        if not hard_moods:
            return None
        hard_days = {to_utc(m.created_at).date() for m in hard_moods}
        sessions = [
            s for s in db.query(Session).filter(Session.profile_id == profile_id, Session.is_practice == False)  # noqa: E712
            if s.created_at and to_utc(s.created_at) >= since
        ]
        on_hard = [s for s in sessions if to_utc(s.created_at).date() in hard_days]
        others = [s for s in sessions if to_utc(s.created_at).date() not in hard_days]
        if len(on_hard) < 2 or len(others) < 2:
            return None
        hard_acc, other_acc = accuracy_of(on_hard), accuracy_of(others)
        if hard_acc is None or other_acc is None:
            return None
        common = Counter(m.mood for m in hard_moods).most_common(2)
        return {
            "hard_accuracy": hard_acc,
            "other_accuracy": other_acc,
            "gap": round(other_acc - hard_acc, 1),
            "hard_days": len(hard_days),
            "hard_sessions": len(on_hard),
            "moods": [MOODS_BY_KEY[k]["label"].lower() for k, _ in common],
        }

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
            elif analysis["recommendation"] == "fade_help":
                recommendations.append({
                    "key": f"help:{activity_type}:fade",
                    "kind": "pattern", "type": "help", "activity": activity_type,
                    "current_level": current,
                    "title": f"{name}: acerta, mas ainda com ajuda",
                    "message": analysis["reason"],
                    "reasons": [analysis["reason"]], "priority": "medium",
                })

            for pattern in AIEngine.identify_error_patterns(db, profile_id, activity_type):
                recommendations.append({
                    "key": f"pattern:{activity_type}:{pattern['type']}",
                    "kind": "pattern", "type": "pattern", "activity": activity_type,
                    "title": f"{name}: {pattern['description']}",
                    "message": pattern["suggestion"],
                    "reasons": [pattern["suggestion"]], "priority": "medium",
                })

        mood = AIEngine.mood_performance(db, profile_id)
        if mood and mood["gap"] >= MOOD_GAP:
            felt = " ou ".join(mood["moods"])
            recommendations.append({
                "key": "mood:hard_days", "kind": "pattern", "type": "pattern", "activity": None,
                "title": "Nos dias difíceis, o acerto cai",
                "message": "Cruzamento do \"Como estou?\" com o desempenho dos últimos 30 dias.",
                "reasons": [
                    f"Nos {mood['hard_days']} dias em que disse estar {felt}, acertou {mood['hard_accuracy']:.0f}% "
                    f"de primeira, contra {mood['other_accuracy']:.0f}% nos outros dias.",
                    "Nesses dias, prefira atividades que a criança já domina, sessões mais curtas, "
                    "pausas e o Modo Baixo Estímulo.",
                ],
                "priority": "medium",
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
            Session.id > (decision.last_session_id or 0),
        )
        if rec.get("activity"):
            newer = newer.filter(Session.activity_type == rec["activity"])
        newer = newer.first()
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
