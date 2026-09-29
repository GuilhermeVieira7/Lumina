# ==========================================
# TESTES - Foto da criança (várias crianças por família)
# ==========================================

import base64

from test_features import _headers, _new_family, _register

JPEG = "data:image/jpeg;base64," + base64.b64encode(b"\xff\xd8\xff\xe0" + b"0" * 64).decode()
PNG = "data:image/png;base64," + base64.b64encode(b"\x89PNG\r\n\x1a\n" + b"0" * 64).decode()


def test_owner_sets_and_removes_photo(client):
    headers, profile = _new_family(client)
    pid = profile["id"]
    assert profile["photo"] is None

    resp = client.put(f"/api/profiles/{pid}/photo", headers=headers, json={"photo": JPEG})
    assert resp.status_code == 200, resp.text
    assert resp.json()["photo"] == JPEG
    listed = client.get("/api/profiles", headers=headers).json()
    assert next(p for p in listed if p["id"] == pid)["photo"] == JPEG

    assert client.put(f"/api/profiles/{pid}/photo", headers=headers, json={"photo": PNG}).json()["photo"] == PNG
    resp = client.delete(f"/api/profiles/{pid}/photo", headers=headers)
    assert resp.status_code == 200 and resp.json()["photo"] is None


def test_photo_must_be_a_real_image(client):
    headers, profile = _new_family(client)
    url = f"/api/profiles/{profile['id']}/photo"
    fake = "data:image/jpeg;base64," + base64.b64encode(b"<script>alert(1)</script>").decode()
    for bad in [fake, "data:text/html;base64,PGgxPg==", "data:image/jpeg;base64,@@@", "https://exemplo.com/foto.jpg"]:
        assert client.put(url, headers=headers, json={"photo": bad}).status_code == 400, bad
    huge = "data:image/jpeg;base64," + "A" * 300_001
    assert client.put(url, headers=headers, json={"photo": huge}).status_code == 422


def test_only_the_owner_changes_the_photo(client):
    headers, profile = _new_family(client)
    other, _, _ = _register(client)
    stranger = _headers(other)
    url = f"/api/profiles/{profile['id']}/photo"
    assert client.put(url, headers=stranger, json={"photo": JPEG}).status_code == 404
    assert client.delete(url, headers=stranger).status_code == 404


def test_each_child_keeps_its_own_photo(client):
    headers, first = _new_family(client)
    second = client.post("/api/profiles", headers=headers, json={"name": "Irmão", "avatar": "🦊"}).json()
    client.put(f"/api/profiles/{first['id']}/photo", headers=headers, json={"photo": JPEG})
    kids = {p["id"]: p for p in client.get("/api/profiles", headers=headers).json()}
    assert kids[first["id"]]["photo"] == JPEG
    assert kids[second["id"]]["photo"] is None and kids[second["id"]]["avatar"] == "🦊"
