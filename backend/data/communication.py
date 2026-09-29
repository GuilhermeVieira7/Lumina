# ==========================================
# COMUNICAÇÃO - Prancha de pedidos e prêmios do quadro de fichas
# ==========================================
# Os pedidos seguem o que as pranchas de Comunicação Alternativa costumam
# trazer primeiro: necessidades básicas, pausa, ajuda, sim e não.

REQUEST_OPTIONS = [
    {"key": "pausa", "icon": "⏸️", "label": "Pausa", "phrase": "Eu quero uma pausa"},
    {"key": "ajuda", "icon": "🙋", "label": "Ajuda", "phrase": "Eu preciso de ajuda"},
    {"key": "agua", "icon": "🥤", "label": "Água", "phrase": "Eu quero água"},
    {"key": "comer", "icon": "🥪", "label": "Comer", "phrase": "Eu estou com fome"},
    {"key": "banheiro", "icon": "🚽", "label": "Banheiro", "phrase": "Eu quero ir ao banheiro"},
    {"key": "abraco", "icon": "🤗", "label": "Abraço", "phrase": "Eu quero um abraço"},
    {"key": "barulho", "icon": "🔇", "label": "Barulho", "phrase": "Está muito barulho"},
    {"key": "cansado", "icon": "🥱", "label": "Cansado", "phrase": "Eu estou cansado"},
    {"key": "dor", "icon": "🤕", "label": "Dor", "phrase": "Eu estou com dor"},
    {"key": "acabou", "icon": "✋", "label": "Acabou", "phrase": "Eu quero parar"},
    {"key": "sim", "icon": "👍", "label": "Sim", "phrase": "Sim"},
    {"key": "nao", "icon": "👎", "label": "Não", "phrase": "Não"},
]

REQUESTS_BY_KEY = {r["key"]: r for r in REQUEST_OPTIONS}
DEFAULT_REQUESTS = [r["key"] for r in REQUEST_OPTIONS]

REWARD_OPTIONS = [
    {"icon": "🧸", "label": "Brinquedo"},
    {"icon": "📺", "label": "Desenho"},
    {"icon": "🎵", "label": "Música"},
    {"icon": "⚽", "label": "Bola"},
    {"icon": "🍪", "label": "Lanche"},
    {"icon": "🤗", "label": "Abraço"},
    {"icon": "🛝", "label": "Parquinho"},
    {"icon": "🫧", "label": "Bolhas"},
    {"icon": "📱", "label": "Tablet"},
    {"icon": "🎨", "label": "Pintar"},
    {"icon": "🚲", "label": "Bicicleta"},
    {"icon": "🧩", "label": "Quebra-cabeça"},
]

DEFAULT_REWARDS = REWARD_OPTIONS[:6]

# ---------- "Como estou me sentindo?" ----------
# Poucas emoções, com rosto claro, como nos quadros de emoções usados com
# crianças autistas. "hard" marca as que pedem atenção do adulto.
MOOD_OPTIONS = [
    {"key": "feliz", "icon": "😊", "label": "Feliz", "phrase": "Eu estou feliz", "color": "#F2B632", "hard": False},
    {"key": "calmo", "icon": "😌", "label": "Calmo", "phrase": "Eu estou calmo", "color": "#4CB68D", "hard": False},
    {"key": "triste", "icon": "😢", "label": "Triste", "phrase": "Eu estou triste", "color": "#5B8DEF", "hard": True},
    {"key": "bravo", "icon": "😠", "label": "Bravo", "phrase": "Eu estou bravo", "color": "#E5604D", "hard": True},
    {"key": "medo", "icon": "😨", "label": "Com medo", "phrase": "Eu estou com medo", "color": "#9B7FD1", "hard": True},
    {"key": "cansado", "icon": "😴", "label": "Cansado", "phrase": "Eu estou cansado", "color": "#8C939D", "hard": True},
]

MOODS_BY_KEY = {m["key"]: m for m in MOOD_OPTIONS}
