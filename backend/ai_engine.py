# ==========================================
# AI ENGINE - Motor de Inteligência Artificial Adaptativa
# Fundamentado em ABA, TEACCH e educação inclusiva
# ==========================================

from typing import List, Dict, Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import func, desc
from models import Session, Profile, Response
from datetime import datetime, timedelta
import math

try:
    from sklearn.ensemble import RandomForestClassifier
    import numpy as np
    
    # Treino base (Dummy) para inicialização rápida antes do joblib no futuro
    # Features: [acuracia_media, tempo_medio_ms, tentativas_medias, erros_seguidos]
    # Labels: -1 (baixo estimulo), 0 (manter), 1 (subir dificuldade)
    X_train_dummy = [
        [95.0, 1500,  1.0, 0], # Rápido e exato -> Subir
        [85.0, 2000,  1.2, 0], # Muito bom -> Subir
        [75.0, 3000,  1.5, 1], # Normal -> Manter
        [60.0, 4000,  2.0, 2], # Dificuldade leve -> Manter
        [20.0, 15000, 4.0, 5], # Lento, muitos erros -> Baixo estimulo
        [40.0, 8000,  3.0, 3], # Frustração -> Baixo estimulo
    ]
    y_train_dummy = [1, 1, 0, 0, -1, -1]
    
    ML_MODEL = RandomForestClassifier(n_estimators=10, random_state=42)
    ML_MODEL.fit(X_train_dummy, y_train_dummy)
    HAS_ML = True
except ImportError:
    HAS_ML = False


ACTIVITY_NAMES = {
    "colors": "Cores",
    "shapes": "Formas",
    "numbers": "Números",
    "sequences": "Sequências",
    "matching": "Pareamento",
    "math": "Matemática",
    "emotions": "Emoções",
    "letters": "Letras",
    "clock": "Relógio",
    "money": "Dinheiro",
    "categories": "Categorias",
    "patterns": "Padrões",
}


class AIEngine:
    """
    Motor de IA Adaptativa baseado em ABA (Applied Behavior Analysis).
    
    Todas as decisões são explicáveis e documentadas.
    Critérios de progressão:
      - >=85% acerto consistente → avança nível
      - 70-85% → mantém nível (consolidação)
      - <50% → retorna nível anterior
    """

    @staticmethod
    def analyze_performance(db: DBSession, profile_id: int, activity_type: str) -> dict:
        """
        Analisar desempenho recente e sugerir ajuste de nível.
        Baseado nas últimas 5 sessões (critério ABA de consistência).
        """
        recent_sessions = (
            db.query(Session)
            .filter(
                Session.profile_id == profile_id,
                Session.activity_type == activity_type,
                Session.is_practice == False
            )
            .order_by(desc(Session.created_at))
            .limit(5)
            .all()
        )

        if len(recent_sessions) < 2:
            return {
                "suggested_level": 1,
                "recommendation": "continue",
                "reason": "Dados insuficientes para análise. Continue praticando!",
                "avg_accuracy": 0,
                "trend": 0,
            }

        # Calcular métricas
        accuracies = [s.accuracy for s in recent_sessions]
        avg_accuracy = sum(accuracies) / len(accuracies)
        trend = AIEngine._calculate_trend(accuracies)
        current_level = recent_sessions[0].level  # Nível mais recente

        # Carregar respostas baseadas nas sessões para IA preditiva
        session_ids = [s.id for s in recent_sessions]
        if session_ids:
            resp_stats = db.query(
                func.avg(Response.response_time).label("avg_time"),
                func.avg(Response.attempts).label("avg_attempts")
            ).filter(Response.session_id.in_(session_ids)).first()
            avg_time = resp_stats.avg_time or 3000
            avg_attempts = resp_stats.avg_attempts or 1.0
        else:
            avg_time = 3000
            avg_attempts = 1.0
            
        consecutive_errors = 0
        if recent_sessions and recent_sessions[0].accuracy < 50:
            consecutive_errors = 1 # simplificação

        suggested_level = current_level
        recommendation = "continue"
        reason = ""

        # Usar Modelo ML Preditivo se disponível, caso contrário falhar elegantemente para regras
        predicted_action = 0
        if HAS_ML:
            features = np.array([[avg_accuracy, avg_time, avg_attempts, consecutive_errors]])
            predicted_action = ML_MODEL.predict(features)[0]
        else:
            if avg_accuracy >= 85: predicted_action = 1
            elif avg_accuracy < 50: predicted_action = -1
            else: predicted_action = 0

        if predicted_action == 1:
            suggested_level = min(current_level + 1, 5)
            recommendation = "level_up"
            reason = (
                f"<strong>O que manter:</strong> Domínio lógico detectado pela IA (Acerto: {avg_accuracy:.1f}%, Tentativas: {avg_attempts:.1f}).<br><br>"
                f"<strong>O que melhorar:</strong> Adaptação a novos desafios.<br><br>"
                f"<strong>Ideias de melhoria:</strong> Avançar para o nível {suggested_level} e introduzir conceitos novos."
            )
        elif predicted_action == -1:
            suggested_level = max(current_level - 1, 1)
            recommendation = "attention"
            reason = (
                f"<strong>O que manter:</strong> O engajamento na atividade.<br><br>"
                f"<strong>O que melhorar:</strong> Foco ou controle de fadiga (Tempo alto detectado pela IA: {avg_time/1000:.1f}s).<br><br>"
                f"<strong>Ideias de melhoria:</strong> Sugerimos ativar o modo de Baixo Estímulo e focar nos fundamentos no nível {suggested_level}."
            )
        else:
            recommendation = "reinforce"
            reason = (
                f"<strong>O que manter:</strong> O ritmo de aprendizado adequado (Acerto: {avg_accuracy:.1f}%).<br><br>"
                f"<strong>O que melhorar:</strong> A precisão até consolidar o conceito.<br><br>"
                f"<strong>Ideias de melhoria:</strong> Manter atual nível e reforçar elogios."
            )

        return {
            "suggested_level": suggested_level,
            "recommendation": recommendation,
            "reason": reason,
            "avg_accuracy": round(avg_accuracy, 1),
            "trend": round(trend, 1),
        }

    @staticmethod
    def identify_error_patterns(db: DBSession, profile_id: int, activity_type: str) -> List[dict]:
        """
        Identificar padrões de erro para fornecer insights aos pais/terapeutas.
        """
        recent_sessions = (
            db.query(Session)
            .filter(
                Session.profile_id == profile_id,
                Session.activity_type == activity_type,
                Session.is_practice == False
            )
            .order_by(desc(Session.created_at))
            .limit(10)
            .all()
        )

        if not recent_sessions:
            return []

        patterns = []
        accuracies = [s.accuracy for s in recent_sessions]

        # Inconsistência (variância alta)
        variance = AIEngine._calculate_variance(accuracies)
        if variance > 400:
            patterns.append({
                "type": "inconsistency",
                "description": "Desempenho inconsistente entre sessões",
                "suggestion": "<strong>Ideias de melhoria:</strong> Revisar condições de prática (horário, ambiente, estado emocional).",
            })

        # Tempo de resposta elevado
        avg_time = sum(s.total_time for s in recent_sessions) / len(recent_sessions)
        if avg_time > 600000:  # 10 minutos
            patterns.append({
                "type": "slow_response",
                "description": "Tempo de resposta elevado",
                "suggestion": "<strong>Ideias de melhoria:</strong> Considerar simplificação das instruções ou redução de estímulos visuais/sonoros.",
            })

        # Queda progressiva
        trend = AIEngine._calculate_trend(accuracies)
        if trend < -15:
            patterns.append({
                "type": "declining_performance",
                "description": "Queda progressiva no desempenho",
                "suggestion": "<strong>Ideias de melhoria:</strong> Possível fadiga ou perda de motivação. Considerar pausas mais frequentes no processo.",
            })

        return patterns

    @staticmethod
    def generate_recommendations(db: DBSession, profile_id: int) -> List[dict]:
        """
        Gerar recomendações personalizadas baseadas em todo o histórico.
        """
        recommendations = []

        # Obter tipos de atividade praticados
        activity_types = (
            db.query(Session.activity_type)
            .filter(Session.profile_id == profile_id, Session.is_practice == False)
            .distinct()
            .all()
        )

        for (activity_type,) in activity_types:
            analysis = AIEngine.analyze_performance(db, profile_id, activity_type)
            patterns = AIEngine.identify_error_patterns(db, profile_id, activity_type)
            act_name = ACTIVITY_NAMES.get(activity_type, activity_type)

            if analysis["recommendation"] == "level_up":
                recommendations.append({
                    "type": "positive",
                    "activity": activity_type,
                    "title": f"{act_name}: Pronto para avançar!",
                    "message": analysis["reason"],
                    "priority": "medium",
                })
            elif analysis["recommendation"] in ("level_down", "attention"):
                recommendations.append({
                    "type": "attention",
                    "activity": activity_type,
                    "title": f"{act_name}: Atenção necessária",
                    "message": analysis["reason"],
                    "priority": "high",
                })

            for pattern in patterns:
                recommendations.append({
                    "type": "pattern",
                    "activity": activity_type,
                    "title": f"{act_name}: {pattern['description']}",
                    "message": pattern["suggestion"],
                    "priority": "medium",
                })

        # Recomendação geral
        total_correct = db.query(func.sum(Session.correct)).filter(
            Session.profile_id == profile_id, Session.is_practice == False
        ).scalar() or 0
        total_incorrect = db.query(func.sum(Session.incorrect)).filter(
            Session.profile_id == profile_id, Session.is_practice == False
        ).scalar() or 0
        total = total_correct + total_incorrect

        if total > 0:
            overall_accuracy = (total_correct / total) * 100
            if overall_accuracy >= 80:
                recommendations.append({
                    "type": "general",
                    "activity": None,
                    "title": "Excelente progresso geral!",
                    "message": f"Taxa de acerto geral de {overall_accuracy:.1f}%. Continue o ótimo trabalho!",
                    "priority": "low",
                })

        # Ordenar por prioridade
        priority_order = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda r: priority_order.get(r["priority"], 2))

        return recommendations

    @staticmethod
    def _calculate_trend(accuracies: List[float]) -> float:
        """Calcular tendência: diferença entre primeira e última acurácia."""
        if len(accuracies) < 2:
            return 0
        # Note: list is ordered desc (most recent first), so reverse for trend
        return accuracies[0] - accuracies[-1]

    @staticmethod
    def _calculate_variance(values: List[float]) -> float:
        """Calcular variância estatística."""
        if not values:
            return 0
        mean = sum(values) / len(values)
        squared_diffs = [(v - mean) ** 2 for v in values]
        return sum(squared_diffs) / len(squared_diffs)
