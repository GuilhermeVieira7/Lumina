# ==========================================
# TESTES - Relatório em PDF
# ==========================================

from test_features import _new_family, _session


def test_report_with_data_and_empty(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    empty = client.get(f"/api/sessions/export/pdf?profile_id={pid}&tz=180", headers=headers)
    assert empty.status_code == 200 and empty.content[:4] == b"%PDF"

    for correct in (5, 1, 4, 0, 5):
        _session(client, headers, pid, "colors", correct=correct)
    _session(client, headers, pid, "numbers", correct=3)
    client.post("/api/moods", headers=headers, json={"profile_id": pid, "mood": "triste"})
    client.post("/api/notes", headers=headers, json={"profile_id": pid, "content": "Ficou calmo 😌 com música baixa.\nPediu água."})
    for days in ("&days=7", "&days=30", ""):
        resp = client.get(f"/api/sessions/export/pdf?profile_id={pid}{days}&tz=180", headers=headers)
        assert resp.status_code == 200 and resp.content[:4] == b"%PDF"
        assert resp.headers["content-disposition"].endswith("relatorio_lumina_Bia.pdf")


def test_report_text_drops_symbols_the_pdf_font_cannot_draw():
    from report_pdf import _t

    assert _t("Ação ✔ concluída ⭐") == "Ação concluída"
    assert _t("Linha 1\nLinha 2") == "Linha 1\nLinha 2"
