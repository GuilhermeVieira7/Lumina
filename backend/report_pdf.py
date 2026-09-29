# ==========================================
# RELATÓRIO EM PDF - layout do relatório de acompanhamento (RF12)
# ==========================================
# Recebe os dados já calculados (resumo, estatísticas, metas, emoções...) e
# desenha um relatório de leitura rápida: primeiro a frase de resumo e os
# números principais, depois gráficos simples e, no fim, como ler cada termo.

import re
from datetime import date, datetime, timedelta
from typing import Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos

SYSTEM_NAME = "Lumina TEA Edu"
NEXT = dict(new_x=XPos.LMARGIN, new_y=YPos.NEXT)

# Cores do sistema (as mesmas do tema claro do app)
PRIMARY = (58, 100, 192)
PRIMARY_SOFT = (227, 235, 250)
TEXT = (34, 50, 74)
TEXT_SOFT = (91, 107, 130)
BORDER = (217, 226, 238)
ROW_ALT = (247, 249, 252)
SUCCESS = (36, 121, 84)
WARNING = (147, 98, 19)
DANGER = (182, 58, 55)
AREA_COLORS = {
    "cognicao": (111, 159, 216), "comunicacao": (232, 166, 85),
    "socializacao": (217, 138, 166), "autonomia": (109, 187, 143),
}
HELP_LEVELS = [
    ("none", "Sem ajuda", (36, 121, 84)),
    ("verbal", "Dica verbal", (111, 159, 216)),
    ("gesture", "Gesto ou apontar", (232, 166, 85)),
    ("physical", "Ajuda física", (182, 58, 55)),
]
COMMUNICATION = {
    "verbal": "Fala", "gestures": "Gestos e apontar", "pictures": "Figuras / pictogramas",
    "aac": "Prancha ou app de CAA", "mixed": "Um pouco de cada",
}

GLOSSARY = [
    ("Acerto de primeira", "Parte das respostas certas logo na primeira tentativa. Mostra o que a criança já faz sozinha."),
    ("Nível", "Dificuldade da atividade (1 é o mais fácil). O nível só muda quando um adulto aceita a sugestão."),
    ("Ajuda registrada", "Quanta ajuda o adulto deu na sessão. Mais sessões \"sem ajuda\" indicam mais autonomia."),
    ("Emoções difíceis", "Triste, bravo, com medo ou cansado, escolhidas pela criança no \"Como estou?\"."),
    ("Pedidos", "O que a criança pediu pela prancha (pausa, ajuda, água...). Ajudam a entender necessidades."),
]


def _t(text) -> str:
    """As fontes padrão do PDF só aceitam Latin-1: emojis e outros símbolos são retirados."""
    clean = str(text).encode("latin-1", "ignore").decode("latin-1")
    return re.sub(r" {2,}", " ", clean).strip() if clean != str(text) else clean


def _hex(color: str):
    color = color.lstrip("#")
    return tuple(int(color[i:i + 2], 16) for i in (0, 2, 4))


def _minutes(total: int) -> str:
    return f"{total} min" if total < 60 else f"{total // 60}h {total % 60:02d}min"


def _age(birth: Optional[date]) -> Optional[str]:
    if not birth:
        return None
    today = date.today()
    years = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    return f"{years} {'ano' if years == 1 else 'anos'}"


class ReportPDF(FPDF):
    def __init__(self, child_name: str):
        super().__init__(format="A4")
        self.child_name = child_name
        self.set_margins(15, 15, 15)
        self.set_auto_page_break(True, margin=20)
        self.alias_nb_pages()
        self.set_title(_t(f"Relatório de acompanhamento - {child_name}"))
        self.set_author(SYSTEM_NAME)
        self.set_creator(SYSTEM_NAME)

    def header(self):
        if self.page_no() == 1:
            return  # a primeira página tem a faixa de capa
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*PRIMARY)
        self.cell(90, 6, _t(SYSTEM_NAME))
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*TEXT_SOFT)
        self.cell(0, 6, _t(f"Relatório de acompanhamento · {self.child_name}"), align="R", **NEXT)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.3)
        self.line(15, self.get_y() + 1, 195, self.get_y() + 1)
        self.ln(6)

    def footer(self):
        self.set_y(-14)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())
        self.ln(2)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*TEXT_SOFT)
        self.cell(120, 5, _t("Documento confidencial. Compartilhe só com quem acompanha a criança."))
        self.cell(0, 5, _t(f"Página {self.page_no()} de {{nb}}"), align="R")

    # ---------- blocos reutilizáveis ----------
    def ensure_space(self, height: float):
        if self.get_y() + height > self.page_break_trigger:
            self.add_page()

    def section(self, title: str, subtitle: Optional[str] = None, need: float = 40):
        self.ensure_space(need)
        self.ln(5)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*TEXT)
        self.set_fill_color(*PRIMARY)
        y = self.get_y()
        self.rect(15, y + 1.2, 1.6, 5.6, style="F")
        self.set_x(19)
        self.cell(0, 8, _t(title), **NEXT)
        if subtitle:
            self.set_font("Helvetica", "", 9)
            self.set_text_color(*TEXT_SOFT)
            self.set_x(19)
            self.multi_cell(176, 4.5, _t(subtitle), align="L", **NEXT)
        self.ln(2)

    def muted(self, text: str):
        self.set_font("Helvetica", "I", 10)
        self.set_text_color(*TEXT_SOFT)
        self.multi_cell(0, 6, _t(text), align="L", **NEXT)

    def hbar(self, x, y, width, pct, color, height=4.2):
        """Barra horizontal com trilho claro atrás."""
        self.set_fill_color(*ROW_ALT)
        self.set_draw_color(*BORDER)
        self.set_line_width(0.2)
        self.rect(x, y, width, height, style="DF", round_corners=True, corner_radius=1.5)
        if pct and pct > 0:
            self.set_fill_color(*color)
            self.rect(x, y, max(3, width * min(pct, 100) / 100), height, style="F", round_corners=True, corner_radius=1.5)


def _cover(pdf: ReportPDF, profile, period_text: str):
    # Faixa de capa
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(0, 0, 210, 38, style="F")
    pdf.set_xy(15, 10)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 20)
    pdf.cell(110, 9, _t(SYSTEM_NAME))
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 9, _t(f"Emitido em {datetime.now().strftime('%d/%m/%Y')}"), align="R", **NEXT)
    pdf.set_x(15)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, _t("Relatório de acompanhamento educacional"), **NEXT)

    # Quem é a criança e qual período
    pdf.set_y(46)
    pdf.set_text_color(*TEXT)
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 10, _t(profile.name), **NEXT)
    facts = [f"Período: {period_text}"]
    age = _age(profile.birth_date)
    if age:
        facts.append(f"Idade: {age}")
    if profile.communication in COMMUNICATION:
        facts.append(f"Comunica-se por: {COMMUNICATION[profile.communication]}")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*TEXT_SOFT)
    pdf.cell(0, 6, _t("   ·   ".join(facts)), **NEXT)
    if profile.interests:
        pdf.cell(0, 6, _t(f"Interesses: {profile.interests}"), **NEXT)
    pdf.ln(4)


def _headline(pdf: ReportPDF, text: str):
    pdf.set_font("Helvetica", "", 11.5)
    lines = pdf.multi_cell(168, 6, _t(text), align="L", dry_run=True, output="LINES")
    height = 13 + 6 * len(lines)
    y = pdf.get_y()
    pdf.set_fill_color(*PRIMARY_SOFT)
    pdf.rect(15, y, 180, height, style="F", round_corners=True, corner_radius=3)
    pdf.set_fill_color(*PRIMARY)
    pdf.rect(15, y, 2, height, style="F")
    pdf.set_xy(21, y + 4)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*PRIMARY)
    pdf.cell(0, 4, _t("EM RESUMO"), **NEXT)
    pdf.set_xy(21, y + 9)
    pdf.set_font("Helvetica", "", 11.5)
    pdf.set_text_color(*TEXT)
    pdf.multi_cell(168, 6, _t(text), align="L", **NEXT)
    pdf.set_y(y + height + 5)


def _kpis(pdf: ReportPDF, summary: dict):
    change = summary["accuracy_change"]
    if change is None or summary["accuracy"] is None:
        acc_note, acc_color = ("sem período anterior para comparar" if summary["accuracy"] is not None else ""), TEXT_SOFT
    elif abs(change) < 3:
        acc_note, acc_color = "estável em relação ao período anterior", TEXT_SOFT
    else:
        acc_note = f"{'+' if change > 0 else '-'}{abs(round(change))} pontos em relação ao período anterior"
        acc_color = SUCCESS if change > 0 else DANGER
    cards = [
        ("Atividades feitas", str(summary["activities"]), "", TEXT_SOFT),
        ("Acerto de primeira", "-" if summary["accuracy"] is None else f"{round(summary['accuracy'])}%", acc_note, acc_color),
        ("Tempo de prática", _minutes(summary["minutes"]), "", TEXT_SOFT),
        ("Dias com atividade", str(summary["active_days"]), f"{summary['stars']} estrelas ganhas", TEXT_SOFT),
    ]
    width, gap, height = 42, 4, 30
    y = pdf.get_y()
    for i, (label, value, note, color) in enumerate(cards):
        x = 15 + i * (width + gap)
        pdf.set_fill_color(255, 255, 255)
        pdf.set_draw_color(*BORDER)
        pdf.set_line_width(0.3)
        pdf.rect(x, y, width, height, style="DF", round_corners=True, corner_radius=3)
        pdf.set_xy(x + 4, y + 4)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.cell(width - 8, 4, _t(label.upper()))
        pdf.set_xy(x + 4, y + 9)
        pdf.set_font("Helvetica", "B", 19)
        pdf.set_text_color(*TEXT)
        pdf.cell(width - 8, 10, _t(value))
        if note:
            pdf.set_xy(x + 4, y + 20)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(*color)
            pdf.multi_cell(width - 8, 3.2, _t(note), align="L")
    pdf.set_y(y + height + 2)


def _timeline(pdf: ReportPDF, daily: list):
    points = [(i, d["accuracy"]) for i, d in enumerate(daily) if d["accuracy"] is not None]
    pdf.section("Evolução do acerto de primeira",
                "Média de cada dia em que a criança fez atividades. Dias sem atividade ficam de fora.", need=70)
    if not points:
        pdf.muted("Nenhuma atividade no período.")
        return
    x0, y0, w, h = 27, pdf.get_y() + 2, 154, 48
    # Grade de 0% a 100%
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_line_width(0.2)
    for pct in (0, 25, 50, 75, 100):
        y = y0 + h - h * pct / 100
        pdf.set_draw_color(*BORDER)
        pdf.line(x0, y, x0 + w, y)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.set_xy(15, y - 2)
        pdf.cell(10, 4, f"{pct}%", align="R")
    n = len(daily)
    x_of = (lambda i: x0 + w / 2) if n == 1 else (lambda i: x0 + w * i / (n - 1))
    y_of = lambda v: y0 + h - h * v / 100
    # Datas no eixo (no máximo 7 rótulos)
    step = max(1, round((n - 1) / 6)) if n > 1 else 1
    for i in range(0, n, step):
        day = daily[i]["date"]
        pdf.set_xy(x_of(i) - 8, y0 + h + 1.5)
        pdf.cell(16, 4, f"{day[8:10]}/{day[5:7]}", align="C")
    # Linha e pontos
    pdf.set_draw_color(*PRIMARY)
    pdf.set_line_width(0.8)
    coords = [(x_of(i), y_of(v)) for i, v in points]
    for a, b in zip(coords, coords[1:]):
        pdf.line(*a, *b)
    pdf.set_fill_color(*PRIMARY)
    for x, y in coords:
        pdf.ellipse(x - 1.2, y - 1.2, 2.4, 2.4, style="F")
    # Média do período (linha tracejada) e valor do último dia, para leitura rápida
    average = sum(v for _, v in points) / len(points)
    pdf.set_draw_color(*TEXT_SOFT)
    pdf.set_line_width(0.3)
    pdf.set_dash_pattern(dash=1.2, gap=1.2)
    pdf.line(x0, y_of(average), x0 + w, y_of(average))
    pdf.set_dash_pattern()
    pdf.set_font("Helvetica", "", 7.5)
    pdf.set_text_color(*TEXT_SOFT)
    pdf.set_xy(x0 + w + 2, y_of(average) - 2)
    pdf.cell(22, 4, _t(f"média {round(average)}%"))
    last_x, last_y = coords[-1]
    if abs(last_y - y_of(average)) > 4:
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*PRIMARY)
        pdf.set_xy(x0 + w + 2, last_y - 2)
        pdf.cell(22, 4, _t(f"último {round(points[-1][1])}%"))
    pdf.set_y(y0 + h + 8)


def _areas(pdf: ReportPDF, areas: dict):
    pdf.section("Por área de habilidade", "Acerto de primeira em cada área trabalhada no período.", need=45)
    for key, area in areas.items():
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT)
        pdf.set_xy(15, y)
        pdf.cell(52, 7, _t(area["name"]))
        if area["accuracy"] is None:
            pdf.set_font("Helvetica", "I", 9)
            pdf.set_text_color(*TEXT_SOFT)
            pdf.cell(0, 7, _t("sem atividades no período"), **NEXT)
            continue
        pdf.hbar(67, y + 1.4, 95, area["accuracy"], AREA_COLORS.get(key, PRIMARY))
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_xy(165, y)
        pdf.cell(12, 7, f"{round(area['accuracy'])}%", align="R")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.cell(0, 7, _t(f"  {area['sessions']} sess."), **NEXT)


def _activities(pdf: ReportPDF, activities: dict, area_names: dict):
    pdf.section("Por atividade", need=40)
    if not activities:
        pdf.muted("Nenhuma atividade registrada no período.")
        return
    cols = [("Atividade", 48), ("Área", 40), ("Sessões", 18), ("Acerto de primeira", 56), ("Nível", 18)]

    def head():
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_fill_color(*PRIMARY)
        pdf.set_text_color(255, 255, 255)
        for label, width in cols:
            pdf.cell(width, 7, _t(f" {label}"), fill=True, align="C" if label in ("Sessões", "Nível") else "L")
        pdf.ln()

    head()
    rows = sorted(activities.values(), key=lambda a: a["accuracy"], reverse=True)
    for i, a in enumerate(rows):
        if pdf.get_y() + 7 > pdf.page_break_trigger:
            pdf.add_page()
            head()
        y = pdf.get_y()
        pdf.set_fill_color(*(ROW_ALT if i % 2 else (255, 255, 255)))
        pdf.rect(15, y, 180, 7, style="F")
        pdf.set_text_color(*TEXT)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.cell(48, 7, _t(f" {a['name']}"))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.cell(40, 7, _t(f" {area_names.get(a['area'], a['area'])}"))
        pdf.set_text_color(*TEXT)
        pdf.cell(18, 7, str(a["sessions"]), align="C")
        pdf.hbar(pdf.get_x() + 2, y + 1.6, 38, a["accuracy"], AREA_COLORS.get(a["area"], PRIMARY), height=3.8)
        pdf.set_x(pdf.get_x() + 42)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(14, 7, f"{round(a['accuracy'])}%", align="R")
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(18, 7, str(a["current_level"]), align="C", **NEXT)
    pdf.set_draw_color(*BORDER)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())


def _help(pdf: ReportPDF, help_levels: dict):
    total = sum(help_levels.values())
    if not total:
        return
    pdf.section("Ajuda que a criança precisou",
                f"Registrada pelos adultos em {total} {'sessão' if total == 1 else 'sessões'}. Quanto mais \"sem ajuda\", mais autonomia.", need=30)
    y, x = pdf.get_y(), 15
    for key, label, color in HELP_LEVELS:
        count = help_levels.get(key, 0)
        if not count:
            continue
        width = 180 * count / total
        pdf.set_fill_color(*color)
        pdf.rect(x, y, width, 7, style="F")
        if width > 12:
            pdf.set_xy(x, y)
            pdf.set_font("Helvetica", "B", 8.5)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(width, 7, f"{round(100 * count / total)}%", align="C")
        x += width
    pdf.set_y(y + 10)
    pdf.set_font("Helvetica", "", 8.5)
    for key, label, color in HELP_LEVELS:
        count = help_levels.get(key, 0)
        if not count:
            continue
        pdf.set_fill_color(*color)
        pdf.rect(pdf.get_x(), pdf.get_y() + 1.2, 3, 3, style="F")
        pdf.set_x(pdf.get_x() + 4.5)
        pdf.set_text_color(*TEXT)
        pdf.cell(pdf.get_string_width(_t(f"{label}: {count}")) + 7, 5.5, _t(f"{label}: {count}"))
    pdf.ln(7)


def _moods(pdf: ReportPDF, moods: list):
    if not moods:
        return
    total = sum(m["count"] for m in moods)
    hard = sum(m["count"] for m in moods if m["hard"])
    pdf.section("Como a criança disse que estava se sentindo",
                f"{total} {'registro' if total == 1 else 'registros'} no \"Como estou?\"; "
                f"{hard} de {total} ({round(100 * hard / total)}%) foram emoções difíceis.", need=20 + 7 * len(moods))
    top = max(m["count"] for m in moods)
    for m in moods:
        y = pdf.get_y()
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT)
        pdf.cell(40, 7, _t(m["label"]))
        pdf.hbar(55, y + 1.4, 110, 100 * m["count"] / top, _hex(m["color"]))
        pdf.set_xy(167, y)
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.cell(0, 7, _t(f"{m['count']} {'vez' if m['count'] == 1 else 'vezes'}"), **NEXT)


def _requests(pdf: ReportPDF, requests: list):
    if not requests:
        return
    total = sum(r["count"] for r in requests)
    pdf.section("Pedidos feitos na prancha", f"{total} {'pedido' if total == 1 else 'pedidos'} no período, dos mais frequentes para os menos.", need=24)
    pdf.set_font("Helvetica", "", 9.5)
    x = 15
    for r in requests[:8]:
        text = _t(f"{r['label']}  {r['count']}x")
        width = pdf.get_string_width(text) + 8
        if x + width > 195:
            x = 15
            pdf.ln(9)
        y = pdf.get_y()
        pdf.set_fill_color(*PRIMARY_SOFT)
        pdf.rect(x, y, width, 7, style="F", round_corners=True, corner_radius=3.5)
        pdf.set_xy(x, y)
        pdf.set_text_color(*TEXT)
        pdf.cell(width, 7, text, align="C")
        x += width + 3
    pdf.ln(10)


def _goals(pdf: ReportPDF, goals: list, activity_name):
    if not goals:
        return
    unit = {"accuracy": "%", "sessions": " sessões", "stars": " estrelas"}
    pdf.section("Metas", need=20 + 9 * min(len(goals), 3))
    for g in goals:
        pdf.ensure_space(10)
        y = pdf.get_y()
        pct = 100 if g.completed else min(100, round(100 * (g.current_value or 0) / g.target_value)) if g.target_value else 0
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT)
        pdf.cell(48, 6, _t(activity_name(g.activity_type)))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.cell(62, 6, _t((g.description or "")[:40]))
        pdf.hbar(125, y + 1, 40, pct, SUCCESS if g.completed else PRIMARY, height=4)
        pdf.set_xy(167, y)
        pdf.set_font("Helvetica", "B" if g.completed else "", 9)
        pdf.set_text_color(*(SUCCESS if g.completed else TEXT))
        pdf.cell(0, 6, _t("concluída" if g.completed else f"{g.current_value:g} de {g.target_value:g}{unit.get(g.target_type, '')}"), **NEXT)
        pdf.ln(2)


def _suggestions(pdf: ReportPDF, recs: list):
    if not recs:
        return
    pdf.section("Próximos passos sugeridos pelo sistema",
                "Sugestões por regras explícitas. Nada muda para a criança até um adulto aceitar no painel.", need=30)
    # O mesmo padrão em várias atividades vira um item só
    grouped, by_type = [], {}
    for r in recs:
        if r.get("kind") == "pattern" and ": " in r["title"]:
            name, description = r["title"].split(": ", 1)
            if description in by_type:
                by_type[description]["names"].append(name)
                continue
            by_type[description] = {"names": [name], "description": description, "reasons": r.get("reasons")}
            grouped.append(by_type[description])
        else:
            grouped.append(r)
    for g in by_type.values():
        g["title"] = f"{g['description']}: {', '.join(g['names'])}" if len(g["names"]) > 1 else f"{g['names'][0]}: {g['description']}"
    recs = grouped
    for r in recs[:5]:
        pdf.ensure_space(14)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*TEXT)
        pdf.set_fill_color(*PRIMARY)
        pdf.ellipse(18.2, pdf.get_y() + 2, 1.6, 1.6, style="F")
        pdf.set_x(23)
        pdf.multi_cell(172, 5.5, _t(r["title"]), align="L", **NEXT)
        if r.get("reasons"):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(*TEXT_SOFT)
            pdf.set_x(23)
            pdf.multi_cell(172, 4.8, _t(r["reasons"][0]), align="L", **NEXT)
        pdf.ln(1.5)


def _notes(pdf: ReportPDF, notes: list):
    if not notes:
        return
    pdf.section("Observações do diário", "As mais recentes, escritas pelos adultos que acompanham a criança.", need=30)
    for note in notes:
        pdf.set_font("Helvetica", "", 9.5)
        lines = pdf.multi_cell(170, 5, _t(note.content), align="L", dry_run=True, output="LINES")
        height = 8 + 5 * len(lines)
        pdf.ensure_space(height + 3)
        y = pdf.get_y()
        pdf.set_fill_color(*BORDER)
        pdf.rect(15, y, 1.2, height, style="F")
        pdf.set_xy(20, y)
        pdf.set_font("Helvetica", "B", 8.5)
        pdf.set_text_color(*TEXT_SOFT)
        when = note.created_at.strftime("%d/%m/%Y") if note.created_at else ""
        pdf.cell(0, 5.5, _t(f"{when}  ·  {note.author or ''}"), **NEXT)
        pdf.set_x(20)
        pdf.set_font("Helvetica", "", 9.5)
        pdf.set_text_color(*TEXT)
        pdf.multi_cell(170, 5, _t(note.content), align="L", **NEXT)
        pdf.set_y(y + height + 3)


def _glossary(pdf: ReportPDF):
    pdf.section("Como ler este relatório", need=60)
    for term, meaning in GLOSSARY:
        pdf.ensure_space(10)
        pdf.set_font("Helvetica", "B", 9.5)
        pdf.set_text_color(*TEXT)
        pdf.cell(40, 5.5, _t(term))
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(*TEXT_SOFT)
        pdf.multi_cell(140, 5.5, _t(meaning), align="L", **NEXT)
        pdf.ln(1)
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8.5)
    pdf.set_text_color(*TEXT_SOFT)
    pdf.multi_cell(0, 4.5, _t(
        "Este relatório apoia o acompanhamento e não é diagnóstico. Os números devem ser lidos junto com "
        "as observações dos responsáveis e da equipe que acompanha a criança."), align="L", **NEXT)


def build_report(*, profile, days, summary, stats, goals, notes, requests, moods, recs, area_names, activity_name) -> bytes:
    """Monta o PDF completo e devolve os bytes."""
    today = date.today()
    if days:
        start = today - timedelta(days=days - 1)
        period_text = f"últimos {days} dias ({start.strftime('%d/%m')} a {today.strftime('%d/%m/%Y')})"
    else:
        period_text = "todo o histórico"

    pdf = ReportPDF(profile.name)
    pdf.add_page()
    _cover(pdf, profile, period_text)
    _headline(pdf, summary["headline"])
    _kpis(pdf, summary)
    _timeline(pdf, summary["daily"])
    _areas(pdf, stats["areas_breakdown"])
    _activities(pdf, stats["activities_breakdown"], area_names)
    _help(pdf, stats["help_levels"])
    _moods(pdf, moods)
    _requests(pdf, requests)
    _goals(pdf, goals, activity_name)
    _suggestions(pdf, recs)
    _notes(pdf, notes)
    _glossary(pdf)
    return bytes(pdf.output())
