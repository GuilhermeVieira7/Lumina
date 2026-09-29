"""Baixar os pictogramas ARASAAC usados pelo Lumina.

Uso (na raiz do projeto, com internet liberada para api.arasaac.org e
static.arasaac.org):

    python scripts/baixar_pictogramas.py

Para cada figura do catálogo abaixo, o script procura o pictograma no
ARASAAC pela palavra em português (ou usa o número fixado em "id"),
salva o PNG em frontend/img/pictos/ e escreve frontend/img/pictos/index.json.
O Lumina troca o emoji pelo pictograma sempre que ele estiver nesse índice;
o que não foi baixado continua aparecendo como emoji.

Os pictogramas são de autoria de Sergio Palao, propriedade do Governo de
Aragão (Espanha), e distribuídos pelo ARASAAC (https://arasaac.org) sob a
licença Creative Commons BY-NC-SA. Uso não comercial, com atribuição.
"""

import json
import sys
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "frontend" / "img" / "pictos"
API = "https://api.arasaac.org/v1/pictograms/pt/search/{term}"
IMAGE = "https://static.arasaac.org/pictograms/{id}/{id}_300.png"
ATTRIBUTION = (
    "Pictogramas: Sergio Palao. Origem: ARASAAC (https://arasaac.org). "
    "Licença: CC BY-NC-SA. Propriedade: Governo de Aragão (Espanha)."
)

# emoji usado no sistema -> palavra de busca no ARASAAC.
# "id" fixa um pictograma já conferido; "avoid" lista pictogramas que a busca
# encontrou mas não mostram o que o emoji quer dizer (ex.: "cachorro" trazia
# um cachorro-quente). A busca em português do ARASAAC usa muitas palavras de
# Portugal (comboio, bolacha, pequeno-almoço).
CATALOG = {
    # Rotina
    "🌅": {"term": "acordar", "id": 8989},
    "🪥": {"term": "escovar os dentes", "id": 2326},
    "🚿": {"term": "chuveiro", "id": 2370},
    "🛁": {"term": "tomar banho", "id": 6058},
    "👕": {"term": "vestir", "id": 6627},
    "🥣": {"term": "pequeno-almoço", "avoid": [37263]},
    "🍽️": {"term": "almoçar", "id": 28206},
    "🏫": {"term": "escola", "id": 32446},
    "🎒": {"term": "mochila", "id": 2475},
    "📚": {"term": "livro", "id": 25191},
    "✏️": {"term": "lápis", "id": 2440},
    "⭐": {"term": "estrela", "avoid": [2752]},
    "🧸": {"term": "brinquedo", "id": 9813},
    "⚽": {"term": "bola", "id": 3241},
    "🎨": {"term": "pintar", "id": 2348},
    "🎵": {"term": "música", "id": 24791},
    "📺": {"term": "televisão", "id": 25498},
    "🌳": {"term": "parque", "id": 39572},
    "🚗": {"term": "carro", "id": 2339},
    "🛒": {"term": "supermercado", "id": 3389},
    "👨‍👩‍👧": {"term": "família", "id": 38351},
    "🩺": {"term": "médico", "id": 6561},
    "🧩": {"term": "quebra-cabeça", "id": 2540},
    "😴": {"term": "dormir", "id": 6479},
    "🌙": {"term": "noite", "id": 26997},
    "🚽": {"term": "banheiro"},
    # Prancha de pedidos
    "⏸️": {"term": "descansar", "id": 16643},
    "🙋": {"term": "ajuda", "id": 12252},
    "🥤": {"term": "água", "id": 32464},
    "🥪": {"term": "comer", "id": 6456},
    "🤗": {"term": "abraço", "id": 4550},
    "🔇": {"term": "silêncio", "id": 5936},
    "🥱": {"term": "cansado", "id": 35537},
    "🤕": {"term": "dor", "id": 2367},
    "✋": {"term": "terminar", "id": 5358},
    "👍": {"term": "sim", "id": 5584},
    "👎": {"term": "não", "id": 5526},
    # Prêmios do quadro de fichas
    "🍪": {"term": "bolacha", "avoid": [8295]},
    "🛝": {"term": "escorregador"},
    "🫧": {"term": "bolas de sabão", "avoid": [36525]},
    "📱": {"term": "tablet", "id": 28099},
    "🚲": {"term": "bicicleta", "id": 6935},
    # Atividades e figuras das questões
    "🔢": {"term": "números", "id": 2879},
    "➕": {"term": "somar", "id": 5868},
    "🔤": {"term": "alfabeto", "id": 3050},
    "⏰": {"term": "relógio", "id": 2549},
    "💰": {"term": "dinheiro", "id": 4630},
    "📦": {"term": "caixa", "id": 5935},
    "📅": {"term": "agenda", "id": 5898},
    "🎮": {"term": "brincar", "id": 23392},
    "⏳": {"term": "esperar", "id": 36914},
    "😊": {"term": "contente", "id": 35547},
    "😄": {"term": "feliz", "id": 9907},
    "😢": {"term": "triste", "id": 35545},
    "😠": {"term": "zangado", "id": 35539},
    "😰": {"term": "preocupado", "id": 26985},
    "😐": {"term": "sério", "id": 8690},
    "😌": {"term": "calmo"},
    "😨": {"term": "medo"},
    "🍎": {"term": "maçã", "id": 2462},
    "🍌": {"term": "banana", "id": 2530},
    "🍕": {"term": "pizza", "id": 2527},
    "🐱": {"term": "gato", "id": 7114},
    "🐶": {"term": "cão", "avoid": [7201]},
    "🐘": {"term": "elefante", "id": 2372},
    "🌺": {"term": "flor", "id": 7104},
    "🚂": {"term": "comboio", "avoid": [39581]},
    "✈️": {"term": "avião", "id": 2264},
    "👟": {"term": "tênis", "id": 2621},
    "👗": {"term": "vestido", "id": 2613},
}


def slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join("".join(c if c.isalnum() else " " for c in plain.lower()).split())


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Lumina/1.0 (projeto educacional)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def find_id(term: str, avoid=()):
    """Primeiro pictograma cuja palavra-chave é exatamente o termo; senão, o primeiro resultado."""
    results = [p for p in json.loads(fetch(API.format(term=urllib.parse.quote(term)))) if p["_id"] not in avoid]
    for picto in results:
        if any(k.get("keyword", "").lower() == term.lower() for k in picto.get("keywords", [])):
            return picto["_id"]
    return results[0]["_id"] if results else None


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    index_path = OUT_DIR / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8")) if index_path.exists() else {}
    pictos = index.get("pictos", {})
    failures = []

    for emoji, info in CATALOG.items():
        name = f"{slug(info['term'])}.png"
        try:
            picto_id = info.get("id") or find_id(info["term"], info.get("avoid", ()))
            if not picto_id:
                failures.append(f"{emoji} {info['term']}: nenhum resultado")
                continue
            (OUT_DIR / name).write_bytes(fetch(IMAGE.format(id=picto_id)))
            pictos[emoji] = {"file": name, "id": picto_id, "term": info["term"]}
            print(f"ok  {emoji}  {info['term']}  (#{picto_id})")
            time.sleep(0.2)  # respeitar o servidor do ARASAAC
        except Exception as exc:  # noqa: BLE001 - relatar e seguir para os próximos
            failures.append(f"{emoji} {info['term']}: {exc}")

    index = {"attribution": ATTRIBUTION, "pictos": pictos}
    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n{len(pictos)} pictogramas no índice ({index_path.relative_to(ROOT)})")
    if failures:
        print("Falharam:\n  " + "\n  ".join(failures))
    return 1 if failures and not pictos else 0


if __name__ == "__main__":
    sys.exit(main())
