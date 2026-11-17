"""Preenche o "Aluno Demo" com 30 dias de dados FICTÍCIOS para demonstrar o Painel dos Adultos.

Gera sessões (com nível de ajuda que vai diminuindo), emoções do "Como estou?",
metas e algumas observações no diário. Nenhum dado é de criança real.

Uso, com o Docker rodando:
    docker exec tea_application python scripts/dados_demo.py

Só preenche se o Aluno Demo tiver menos de 10 sessões (não duplica os dados).
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from database import SessionLocal  # noqa: E402
from models import ActivityPlan, Goal, MoodCheck, Note, Profile, Response, Session, User  # noqa: E402

DAYS = 30
# atividade -> (acerto inicial, acerto final, ajuda no começo)
ACTIVITIES = {
    "colors": (0.55, 0.95, "verbal"),
    "numbers": (0.40, 0.85, "physical"),
    "shapes": (0.60, 0.95, "gesture"),
    "emotions": (0.35, 0.65, "physical"),
    "letters": (0.45, 0.75, "gesture"),
    "categories": (0.50, 0.80, "verbal"),
}
HELP_STEPS = ["physical", "gesture", "verbal", "none"]
HARD_MOODS = ["cansado", "triste", "bravo"]


def main():
    random.seed(7)
    db = SessionLocal()
    try:
        owner = db.query(User).filter(User.username == "admin").first()
        profile = owner and db.query(Profile).filter(Profile.user_id == owner.id, Profile.name == "Aluno Demo").first()
        if not profile:
            print("Aluno Demo não encontrado. Suba o app uma vez para criar o usuário demo.")
            return
        if db.query(Session).filter(Session.profile_id == profile.id).count() >= 10:
            print("O Aluno Demo já tem dados. Nada foi alterado.")
            return

        for activity in ACTIVITIES:
            if not db.query(ActivityPlan).filter_by(profile_id=profile.id, activity_type=activity).first():
                db.add(ActivityPlan(profile_id=profile.id, activity_type=activity, enabled=True, level=1))

        now = datetime.utcnow().replace(hour=15, minute=0, second=0, microsecond=0)
        hard_days = set(random.sample(range(2, DAYS), 5))
        count = 0
        for day in range(DAYS, 0, -1):
            moment = now - timedelta(days=day)
            if random.random() < 0.15:  # alguns dias sem atividade
                continue
            hard = day in hard_days
            db.add(MoodCheck(profile_id=profile.id, created_at=moment - timedelta(minutes=5),
                             mood=random.choice(HARD_MOODS) if hard else random.choice(["feliz", "calmo", "feliz"]),
                             moment="entrada"))
            progress = 1 - day / DAYS
            for activity in random.sample(list(ACTIVITIES), random.choice([1, 2, 2, 3])):
                start, end, first_help = ACTIVITIES[activity]
                rate = start + (end - start) * progress + random.uniform(-0.08, 0.08) - (0.25 if hard else 0)
                total = 5
                correct = max(0, min(total, round(rate * total)))
                step = min(3, HELP_STEPS.index(first_help) + int(progress * 3.2) + (0 if not hard else -1))
                help_level = HELP_STEPS[max(0, step)] if random.random() < 0.85 else None
                session = Session(
                    profile_id=profile.id, activity_type=activity, level=1, total_questions=total,
                    correct=correct, incorrect=total - correct, accuracy=correct / total * 100,
                    total_time=random.randint(40, 120) * 1000, stars=correct, help_level=help_level,
                    created_at=moment + timedelta(minutes=10 * count % 120),
                )
                session.responses = [
                    Response(question_index=i, is_correct=i < correct, attempts=1 if i < correct else 2,
                             response_time=random.randint(2500, 9000)) for i in range(total)
                ]
                db.add(session)
                count += 1

        db.add(Goal(profile_id=profile.id, activity_type="numbers", target_type="accuracy", target_value=90,
                    description="Contar até 5 sem ajuda", created_at=now - timedelta(days=20)))
        db.add(Goal(profile_id=profile.id, activity_type="emotions", target_type="sessions", target_value=20,
                    description="Praticar emoções com frequência", created_at=now - timedelta(days=20)))
        for days_ago, text in [
            (12, "Na escola, ficou mais tranquilo quando a música estava baixa."),
            (6, "Em casa, pediu ajuda apontando para o cartão. Usamos a prancha antes do jantar."),
            (2, "Dia agitado depois da troca de professora. Fizemos só uma atividade curta."),
        ]:
            db.add(Note(profile_id=profile.id, content=text, author="Responsável", author_id=owner.id,
                        created_at=now - timedelta(days=days_ago)))
        db.commit()
        print(f"Pronto: {count} sessões fictícias, emoções, 2 metas e 3 observações no Aluno Demo.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
