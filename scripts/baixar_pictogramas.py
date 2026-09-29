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

# emoji usado no sistema -> palavra de busca no ARASAAC (e "id" para fixar um pictograma)
CATALOG = {
    # Rotina
    "🌅": {"term": "acordar"},
    "🪥": {"term": "escovar os dentes"},
    "🚿": {"term": "chuveiro"},
    "🛁": {"term": "tomar banho"},
    "👕": {"term": "vestir"},
    "🥣": {"term": "tomar o café da manhã"},
    "🍽️": {"term": "almoçar"},
    "🏫": {"term": "escola"},
    "🎒": {"term": "mochila"},
    "📚": {"term": "livro"},
    "✏️": {"term": "lápis"},
    "⭐": {"term": "estrela"},
    "🧸": {"term": "brinquedo"},
    "⚽": {"term": "bola"},
    "🎨": {"term": "pintar"},
    "🎵": {"term": "música"},
    "📺": {"term": "televisão"},
    "🌳": {"term": "parque"},
    "🚗": {"term": "carro"},
    "🛒": {"term": "supermercado"},
    "👨‍👩‍👧": {"term": "família"},
    "🩺": {"term": "médico"},
    "🧩": {"term": "quebra-cabeça"},
    "😴": {"term": "dormir"},
    "🌙": {"term": "noite"},
    "🚽": {"term": "banheiro"},
    # Prancha de pedidos
    "⏸️": {"term": "descansar"},
    "🙋": {"term": "ajuda"},
    "🥤": {"term": "água"},
    "🥪": {"term": "comer"},
    "🤗": {"term": "abraço"},
    "🔇": {"term": "silêncio"},
    "🥱": {"term": "cansado"},
    "🤕": {"term": "dor"},
    "✋": {"term": "terminar"},
    "👍": {"term": "sim"},
    "👎": {"term": "não"},
    # Prêmios do quadro de fichas
    "🍪": {"term": "biscoito"},
    "🛝": {"term": "escorregador"},
    "🫧": {"term": "bolhas de sabão"},
    "📱": {"term": "tablet"},
    "🚲": {"term": "bicicleta"},
    # Atividades e figuras das questões
    "🔢": {"term": "números"},
    "➕": {"term": "somar"},
    "🔤": {"term": "alfabeto"},
    "⏰": {"term": "relógio"},
    "💰": {"term": "dinheiro"},
    "📦": {"term": "caixa"},
    "📅": {"term": "agenda"},
    "🎮": {"term": "brincar"},
    "⏳": {"term": "esperar"},
    "😊": {"term": "feliz"},
    "😄": {"term": "contente"},
    "😢": {"term": "triste"},
    "😠": {"term": "zangado"},
    "😰": {"term": "preocupado"},
    "😐": {"term": "sério"},
    "🍎": {"term": "maçã"},
    "🍌": {"term": "banana"},
    "🍕": {"term": "pizza"},
    "🐱": {"term": "gato"},
    "🐶": {"term": "cachorro"},
    "🐘": {"term": "elefante"},
    "🌺": {"term": "flor"},
    "🚂": {"term": "trem"},
    "✈️": {"term": "avião"},
    "👟": {"term": "tênis"},
    "👗": {"term": "vestido"},
}


def slug(text: str) -> str:
    plain = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return "-".join("".join(c if c.isalnum() else " " for c in plain.lower()).split())


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Lumina/1.0 (projeto educacional)"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def find_id(term: str):
    """Primeiro pictograma cuja palavra-chave é exatamente o termo; senão, o primeiro resultado."""
    results = json.loads(fetch(API.format(term=urllib.parse.quote(term))))
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
            picto_id = info.get("id") or find_id(info["term"])
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
