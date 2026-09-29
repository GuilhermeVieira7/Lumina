# ==========================================
# ACTIVITY BANK - Banco de Questões Pedagógicas
# 12 atividades × 3 níveis de dificuldade
# ==========================================

ACTIVITY_BANK = {
    # 1. Cores - Reconhecimento e discriminação
    "colors": {
        "name": "Cores",
        "icon": "🎨",
        "levels": {
            1: [
                {"question": "Onde está o VERMELHO?", "type": "color", "correct": "#ef4444", "options": ["#ef4444", "#3b82f6", "#fbbf24"]},
                {"question": "Onde está o AZUL?",     "type": "color", "correct": "#3b82f6", "options": ["#10b981", "#3b82f6", "#ef4444"]},
                {"question": "Onde está o AMARELO?",  "type": "color", "correct": "#fbbf24", "options": ["#ef4444", "#10b981", "#fbbf24"]},
                {"question": "Onde está o VERDE?",    "type": "color", "correct": "#10b981", "options": ["#10b981", "#8b5cf6", "#ef4444"]},
            ],
            2: [
                {"question": "Qual NÃO é AZUL?",          "type": "color", "correct": "#ef4444", "options": ["#3b82f6", "#3b82f6", "#ef4444"]},
                {"question": "Encontre a cor diferente",   "type": "color", "correct": "#10b981", "options": ["#ef4444", "#ef4444", "#10b981"]},
                {"question": "Onde está o ROXO?",          "type": "color", "correct": "#8b5cf6", "options": ["#ef4444", "#8b5cf6", "#3b82f6"]},
                {"question": "Qual é LARANJA?",            "type": "color", "correct": "#f97316", "options": ["#fbbf24", "#f97316", "#ef4444"]},
            ],
            3: [
                {"question": "Tons de azul: qual é mais CLARO?", "type": "color", "correct": "#93c5fd", "options": ["#1e3a8a", "#3b82f6", "#93c5fd"]},
                {"question": "Encontre o ROSA",                  "type": "color", "correct": "#ec4899", "options": ["#ef4444", "#ec4899", "#8b5cf6"]},
                {"question": "Qual cor combina com LARANJA?",    "type": "color", "correct": "#fbbf24", "options": ["#3b82f6", "#fbbf24", "#10b981"]},
            ],
        },
    },

    # 2. Formas - Reconhecimento geométrico
    "shapes": {
        "name": "Formas",
        "icon": "⭐",
        "levels": {
            1: [
                {"question": "Onde está o CÍRCULO?",    "type": "shape", "correct": "●", "options": ["●", "■", "▲"]},
                {"question": "Onde está o QUADRADO?",   "type": "shape", "correct": "■", "options": ["▲", "■", "●"]},
                {"question": "Onde está o TRIÂNGULO?",  "type": "shape", "correct": "▲", "options": ["■", "▲", "●"]},
                {"question": "Encontre o CÍRCULO",      "type": "shape", "correct": "●", "options": ["▲", "●", "■"]},
            ],
            2: [
                {"question": "Qual NÃO é CÍRCULO?",       "type": "shape", "correct": "■", "options": ["●", "●", "■"]},
                {"question": "Encontre a forma diferente", "type": "shape", "correct": "★", "options": ["●", "●", "★"]},
                {"question": "Onde está a ESTRELA?",       "type": "shape", "correct": "★", "options": ["★", "●", "■"]},
                {"question": "Qual é o HEXÁGONO?",         "type": "shape", "correct": "⬡", "options": ["■", "⬡", "●"]},
            ],
            3: [
                {"question": "Quantos LADOS tem um triângulo?", "type": "number", "correct": "3", "options": ["2", "3", "4"]},
                {"question": "Qual forma rola?",                "type": "shape",  "correct": "●", "options": ["●", "■", "▲"]},
                {"question": "Qual tem 4 lados IGUAIS?",        "type": "shape",  "correct": "■", "options": ["▭", "■", "▲"]},
            ],
        },
    },

    # 3. Números - Reconhecimento e contagem
    "numbers": {
        "name": "Números",
        "icon": "🔢",
        "levels": {
            1: [
                {"question": "Onde está o número 1?",  "type": "number", "correct": "1", "options": ["1", "2", "3"]},
                {"question": "Onde está o número 2?",  "type": "number", "correct": "2", "options": ["3", "2", "1"]},
                {"question": "Onde está o número 3?",  "type": "number", "correct": "3", "options": ["2", "1", "3"]},
                {"question": "Quantos pontos? ●●",     "type": "number", "correct": "2", "options": ["1", "2", "3"], "visual": "●●"},
            ],
            2: [
                {"question": "Quantos pontos? ●●●",      "type": "number", "correct": "3", "options": ["2", "3", "4"], "visual": "●●●"},
                {"question": "Quantos quadrados? ■■■■",   "type": "number", "correct": "4", "options": ["3", "4", "5"], "visual": "■■■■"},
                {"question": "Qual vem DEPOIS de 3?",     "type": "number", "correct": "4", "options": ["2", "4", "5"]},
                {"question": "Qual vem ANTES de 3?",      "type": "number", "correct": "2", "options": ["1", "2", "4"]},
            ],
            3: [
                {"question": "Conte: ●●●●●",              "type": "number", "correct": "5", "options": ["4", "5", "6"], "visual": "●●●●●"},
                {"question": "Qual é MAIOR: 3 ou 5?",     "type": "number", "correct": "5", "options": ["3", "5", "4"]},
                {"question": "Quantos faltam para 5? ●●●", "type": "number", "correct": "2", "options": ["1", "2", "3"], "visual": "●●●"},
            ],
        },
    },

    # 4. Sequências - Raciocínio lógico
    "sequences": {
        "name": "Sequências",
        "icon": "🧩",
        "levels": {
            1: [
                {"question": "Complete: ● ● __",  "type": "shape", "correct": "●", "options": ["●", "■", "▲"], "sequence": "● ●"},
                {"question": "Complete: ■ ■ __",  "type": "shape", "correct": "■", "options": ["●", "■", "▲"], "sequence": "■ ■"},
                {"question": "Complete: ▲ ▲ __",  "type": "shape", "correct": "▲", "options": ["●", "■", "▲"], "sequence": "▲ ▲"},
            ],
            2: [
                {"question": "Complete: ● ■ ● __",  "type": "shape",  "correct": "■", "options": ["●", "■", "▲"], "sequence": "● ■ ●"},
                {"question": "Complete: ▲ ● ▲ __",  "type": "shape",  "correct": "●", "options": ["●", "■", "▲"], "sequence": "▲ ● ▲"},
                {"question": "Complete: 1 2 1 __",  "type": "number", "correct": "2", "options": ["1", "2", "3"], "sequence": "1 2 1"},
            ],
            3: [
                {"question": "Complete: ● ■ ▲ ● ■ __",     "type": "shape",  "correct": "▲", "options": ["●", "■", "▲"], "sequence": "● ■ ▲ ● ■"},
                {"question": "Complete: 1 2 2 3 3 3 __",    "type": "number", "correct": "4", "options": ["3", "4", "5"], "sequence": "1 2 2 3 3 3"},
                {"question": "O que vem depois? ■ ■ ■■ ■■ __", "type": "shape", "correct": "■■■", "options": ["■", "■■", "■■■"], "sequence": "■ ■ ■■ ■■"},
            ],
        },
    },

    # 5. Pareamento
    "matching": {
        "name": "Pareamento",
        "icon": "👯",
        "levels": {
            1: [
                {"question": "Encontre o IGUAL a: ●",  "type": "shape", "correct": "●", "options": ["●", "■", "▲"], "reference": "●"},
                {"question": "Encontre o IGUAL a: ■",  "type": "shape", "correct": "■", "options": ["▲", "■", "●"], "reference": "■"},
                {"question": "Qual cor é IGUAL?",       "type": "color", "correct": "#ef4444", "options": ["#ef4444", "#3b82f6", "#10b981"], "reference": "#ef4444"},
            ],
            2: [
                {"question": "Qual par está correto? ● com __", "type": "shape",  "correct": "●", "options": ["●", "■", "▲"], "reference": "●"},
                {"question": "Associe: CÍRCULO = __",          "type": "shape",  "correct": "●", "options": ["●", "■", "▲"]},
                {"question": "Qual número é igual a: 3",       "type": "number", "correct": "3", "options": ["2", "3", "5"], "reference": "3"},
            ],
            3: [
                {"question": "Par oposto: ● com __",               "type": "shape",  "correct": "■", "options": ["●", "■", "▲"]},
                {"question": "Categorias: qual também é redondo?", "type": "shape",  "correct": "⚫", "options": ["●", "⚫", "■"], "reference": "●"},
                {"question": "Complete o par: 2 + 2 = __",         "type": "number", "correct": "4", "options": ["3", "4", "5"]},
            ],
        },
    },

    # 6. Matemática
    "math": {
        "name": "Matemática",
        "icon": "➕",
        "levels": {
            1: [
                {"question": "1 + 1 = ?",      "type": "number", "correct": "2", "options": ["1", "2", "3"]},
                {"question": "2 + 1 = ?",      "type": "number", "correct": "3", "options": ["2", "3", "4"]},
                {"question": "● + ● = ?",      "type": "number", "correct": "2", "options": ["1", "2", "3"], "visual": "● ●"},
            ],
            2: [
                {"question": "2 + 2 = ?",      "type": "number", "correct": "4", "options": ["3", "4", "5"]},
                {"question": "3 + 1 = ?",      "type": "number", "correct": "4", "options": ["3", "4", "5"]},
                {"question": "3 - 1 = ?",      "type": "number", "correct": "2", "options": ["1", "2", "3"]},
                {"question": "●●● - ● = ?",    "type": "number", "correct": "2", "options": ["1", "2", "3"], "visual": "●●● - ●"},
            ],
            3: [
                {"question": "4 + 2 = ?",      "type": "number", "correct": "6", "options": ["5", "6", "7"]},
                {"question": "5 - 2 = ?",      "type": "number", "correct": "3", "options": ["2", "3", "4"]},
                {"question": "2 + 2 + 1 = ?",  "type": "number", "correct": "5", "options": ["4", "5", "6"]},
                {"question": "Qual é MAIOR?",   "type": "number", "correct": "5", "options": ["3", "4", "5"]},
            ],
        },
    },

    # 7. Emoções
    "emotions": {
        "name": "Emoções",
        "icon": "😊",
        "levels": {
            1: [
                {"question": "Quem está feliz?",      "type": "shape", "correct": "😊", "options": ["😊", "😢", "😠"]},
                {"question": "Quem está triste?",      "type": "shape", "correct": "😢", "options": ["😊", "😢", "😠"]},
                {"question": "Quem está com raiva?",   "type": "shape", "correct": "😠", "options": ["😊", "😢", "😠"]},
                {"question": "Quem está com sono?",    "type": "shape", "correct": "😴", "options": ["😊", "😢", "😴"]},
            ],
            2: [
                {"question": "Como se sente ao ganhar um presente?", "type": "shape", "correct": "😊", "options": ["😊", "😢", "😠"]},
                {"question": "Como se sente quando está cansado?",  "type": "shape", "correct": "🥱", "options": ["😊", "😢", "🥱"]},
                {"question": "Como se sente ao brincar com amigos?","type": "shape", "correct": "😄", "options": ["😄", "😢", "😠"]},
                {"question": "Como se sente quando não pode sair?", "type": "shape", "correct": "😢", "options": ["😊", "😢", "😐"]},
            ],
            3: [
                {"question": "Se alguém ajuda você, você deve sentir:", "type": "shape", "correct": "😊", "options": ["😊", "😢", "😠"]},
                {"question": "Quando faz algo errado sem querer:",     "type": "shape", "correct": "😰", "options": ["😰", "😊", "😠"]},
                {"question": "Ao ver alguém chorando, pode sentir:",   "type": "shape", "correct": "😢", "options": ["😊", "😢", "😠"]},
                {"question": "Quando alguém elogia você:",             "type": "shape", "correct": "😊", "options": ["😊", "😢", "😰"]},
            ],
        },
    },

    # 8. Letras
    "letters": {
        "name": "Letras",
        "icon": "🔤",
        "levels": {
            1: [
                {"question": "Qual é a primeira letra do alfabeto?", "type": "shape", "correct": "A", "options": ["A", "B", "C"]},
                {"question": "Qual letra vem depois de A?",          "type": "shape", "correct": "B", "options": ["A", "B", "C"]},
                {"question": "Qual letra vem depois de B?",          "type": "shape", "correct": "C", "options": ["A", "B", "C"]},
                {"question": "Qual é a letra M?",                    "type": "shape", "correct": "M", "options": ["N", "M", "O"]},
            ],
            2: [
                {"question": "BOLA começa com qual letra?", "type": "shape", "correct": "B", "options": ["A", "B", "C"]},
                {"question": "CASA começa com qual letra?", "type": "shape", "correct": "C", "options": ["A", "B", "C"]},
                {"question": "DADO começa com qual letra?", "type": "shape", "correct": "D", "options": ["C", "D", "E"]},
                {"question": "GATO começa com qual letra?", "type": "shape", "correct": "G", "options": ["F", "G", "H"]},
            ],
            3: [
                {"question": "Quantas letras tem SOL?",        "type": "number", "correct": "3", "options": ["2", "3", "4"]},
                {"question": "Quantas letras tem CASA?",       "type": "number", "correct": "4", "options": ["3", "4", "5"]},
                {"question": "Qual palavra tem mais letras?",  "type": "shape",  "correct": "BOLA", "options": ["BOI", "BOLA", "BO"]},
                {"question": "Qual letra está no meio de ABA?","type": "shape",  "correct": "B", "options": ["A", "B", "C"]},
            ],
        },
    },

    # 9. Relógio
    "clock": {
        "name": "Relógio",
        "icon": "⏰",
        "levels": {
            1: [
                {"question": "Que horas são? 3 horas",   "type": "shape", "correct": "03:00", "options": ["03:00", "02:00", "04:00"]},
                {"question": "Que horas são? 6 horas",   "type": "shape", "correct": "06:00", "options": ["06:00", "05:00", "07:00"]},
                {"question": "Que horas são? 12 horas",  "type": "shape", "correct": "12:00", "options": ["12:00", "11:00", "01:00"]},
            ],
            2: [
                {"question": "Que horas são? 6 e meia",     "type": "shape", "correct": "06:30", "options": ["06:30", "06:00", "07:30"]},
                {"question": "Que horas são? 3 e meia",     "type": "shape", "correct": "03:30", "options": ["03:30", "03:00", "04:30"]},
                {"question": "Que horas são? meio-dia",      "type": "shape", "correct": "12:00", "options": ["12:00", "11:00", "12:30"]},
            ],
            3: [
                {"question": "Que horas são? 9 e quinze",    "type": "shape", "correct": "09:15", "options": ["09:15", "09:30", "09:00"]},
                {"question": "Que horas são? 2 e quarenta e cinco", "type": "shape", "correct": "02:45", "options": ["02:45", "02:30", "03:00"]},
                {"question": "Quantas horas tem um dia?",    "type": "number", "correct": "24", "options": ["12", "24", "60"]},
            ],
        },
    },

    # 10. Dinheiro
    "money": {
        "name": "Dinheiro",
        "icon": "💰",
        "levels": {
            1: [
                {"question": "Quanto vale? 1 real",         "type": "shape", "correct": "R$ 1,00", "options": ["R$ 1,00", "R$ 0,50", "R$ 2,00"]},
                {"question": "Quanto vale? 50 centavos",    "type": "shape", "correct": "R$ 0,50", "options": ["R$ 0,50", "R$ 1,00", "R$ 0,25"]},
                {"question": "Quanto vale? 5 reais",        "type": "shape", "correct": "R$ 5,00", "options": ["R$ 5,00", "R$ 10,00", "R$ 2,00"]},
            ],
            2: [
                {"question": "Quanto vale? 10 reais",       "type": "shape", "correct": "R$ 10,00", "options": ["R$ 10,00", "R$ 5,00", "R$ 20,00"]},
                {"question": "1 real + 1 real = ?",          "type": "shape", "correct": "R$ 2,00", "options": ["R$ 1,00", "R$ 2,00", "R$ 3,00"]},
                {"question": "Qual vale MAIS?",              "type": "shape", "correct": "R$ 10,00", "options": ["R$ 5,00", "R$ 2,00", "R$ 10,00"]},
            ],
            3: [
                {"question": "5 reais + 5 reais = ?",       "type": "shape", "correct": "R$ 10,00", "options": ["R$ 10,00", "R$ 5,00", "R$ 15,00"]},
                {"question": "Troco: paguei R$ 5 em algo de R$ 3", "type": "shape", "correct": "R$ 2,00", "options": ["R$ 1,00", "R$ 2,00", "R$ 3,00"]},
                {"question": "Quanto falta para R$ 10? Tenho R$ 7", "type": "shape", "correct": "R$ 3,00", "options": ["R$ 2,00", "R$ 3,00", "R$ 4,00"]},
            ],
        },
    },

    # 11. Categorias
    "categories": {
        "name": "Categorias",
        "icon": "📦",
        "levels": {
            1: [
                {"question": "🍎 pertence a qual categoria?", "type": "shape", "correct": "Frutas",   "options": ["Frutas", "Animais", "Veículos"]},
                {"question": "🐶 pertence a qual categoria?", "type": "shape", "correct": "Animais",  "options": ["Animais", "Frutas", "Roupas"]},
                {"question": "🚗 pertence a qual categoria?", "type": "shape", "correct": "Veículos", "options": ["Veículos", "Frutas", "Animais"]},
                {"question": "👕 pertence a qual categoria?", "type": "shape", "correct": "Roupas",   "options": ["Roupas", "Frutas", "Animais"]},
            ],
            2: [
                {"question": "Qual é uma FRUTA?",     "type": "shape", "correct": "🍌", "options": ["🍌", "🐱", "🚂"]},
                {"question": "Qual é um ANIMAL?",     "type": "shape", "correct": "🐘", "options": ["🍎", "🐘", "🚗"]},
                {"question": "Qual NÃO é um veículo?","type": "shape", "correct": "🌺", "options": ["🚗", "🚂", "🌺"]},
            ],
            3: [
                {"question": "O que comemos?",              "type": "shape", "correct": "🍕", "options": ["🍕", "🚗", "👟"]},
                {"question": "O que usamos para vestir?",   "type": "shape", "correct": "👗", "options": ["🍎", "🐶", "👗"]},
                {"question": "O que voa?",                  "type": "shape", "correct": "✈️", "options": ["✈️", "🚗", "🚂"]},
            ],
        },
    },

    # 12. Padrões
    "patterns": {
        "name": "Padrões",
        "icon": "🔄",
        "levels": {
            1: [
                {"question": "Complete: 🔴 🔵 🔴 🔵 ...", "type": "shape", "correct": "🔴", "options": ["🔴", "🔵", "🟢"]},
                {"question": "Complete: ⭐ ⭐ ⭐ ...",     "type": "shape", "correct": "⭐", "options": ["⭐", "🌟", "✨"]},
                {"question": "Complete: 🟦 🟩 🟦 🟩 ...", "type": "shape", "correct": "🟦", "options": ["🟦", "🟩", "🟥"]},
            ],
            2: [
                {"question": "Complete: 🔺 🔻 🔺 ...",       "type": "shape", "correct": "🔻", "options": ["🔻", "🔺", "🔶"]},
                {"question": "Complete: 🔴 🔴 🔵 🔴 🔴 ...", "type": "shape", "correct": "🔵", "options": ["🔴", "🔵", "🟢"]},
                {"question": "Complete: A B A B ...",          "type": "shape", "correct": "A",  "options": ["A", "B", "C"]},
            ],
            3: [
                {"question": "Complete: 🔴 🔵 🟢 🔴 🔵 ...",  "type": "shape", "correct": "🟢", "options": ["🔴", "🔵", "🟢"]},
                {"question": "Complete: 1 2 3 1 2 ...",        "type": "number", "correct": "3", "options": ["1", "2", "3"]},
                {"question": "Complete: ⬆️ ➡️ ⬇️ ⬅️ ⬆️ ...", "type": "shape", "correct": "➡️", "options": ["⬆️", "➡️", "⬇️"]},
            ],
        },
    },
}


# Áreas de habilidade descritas no TCC (seção 4.2)
AREAS = {
    "comunicacao": {"name": "Comunicação", "icon": "💬"},
    "cognicao": {"name": "Cognição", "icon": "🧠"},
    "autonomia": {"name": "Autonomia na vida diária", "icon": "🏠"},
    "socializacao": {"name": "Socialização", "icon": "🤝"},
}

ACTIVITY_AREA = {
    "colors": "cognicao", "shapes": "cognicao", "numbers": "cognicao",
    "sequences": "cognicao", "matching": "cognicao", "math": "cognicao",
    "patterns": "cognicao", "categories": "comunicacao", "letters": "comunicacao",
    "emotions": "socializacao", "clock": "autonomia", "money": "autonomia",
}

# Atividades que aparecem no menu da criança até o adulto mudar (RNF01: poucos itens por tela)
DEFAULT_ENABLED = ["colors", "shapes", "numbers", "emotions", "letters", "categories"]


def activity_name(activity_type: str) -> str:
    activity = ACTIVITY_BANK.get(activity_type)
    return activity["name"] if activity else activity_type


def max_level(activity_type: str) -> int:
    activity = ACTIVITY_BANK.get(activity_type)
    return max(activity["levels"]) if activity else 1


def get_activity_list():
    """Retorna lista resumida de todas as atividades disponíveis."""
    return [
        {
            "type": key,
            "name": val["name"],
            "icon": val["icon"],
            "area": ACTIVITY_AREA.get(key, "cognicao"),
            "levels": list(val["levels"].keys()),
        }
        for key, val in ACTIVITY_BANK.items()
    ]


def get_questions(activity_type: str, level: int = 1):
    """Retorna questões para um tipo de atividade e nível específico.

    Um nível acima do máximo usa o nível mais alto disponível (não volta ao 1).
    """
    activity = ACTIVITY_BANK.get(activity_type)
    if not activity:
        return []
    levels = activity.get("levels", {})
    level = max(1, min(level, max(levels)))
    return levels.get(level, [])
