"""Tests für die Endpunkte, so wie App und PC-Seite sie aufrufen"""


def test_health_geht_ohne_key(klient):
    antwort = klient.get("/health")
    assert antwort.status_code == 200
    assert antwort.json()["status"] == "ok"


def test_ohne_key_kommt_401(klient):
    assert klient.get("/module").status_code == 401
    assert klient.get("/tasks").status_code == 401
    assert klient.get("/status").status_code == 401


def test_falscher_key_kommt_401(klient):
    assert klient.get("/module", headers={"X-API-Key": "falsch"}).status_code == 401


def test_modulliste_zeigt_alle_module(klient, kopf):
    alle = klient.get("/module", headers=kopf).json()

    namen = []
    for eintrag in alle:
        namen.append(eintrag["name"])

    assert "testmodul" in namen
    assert "kaputt" in namen


def test_modul_von_hand_starten_und_bericht_lesen(klient, kopf):
    gestartet = klient.post("/module/testmodul/lauf", headers=kopf).json()
    assert gestartet["status"] == "ok"

    antwort = klient.get("/module/testmodul/berichte", headers=kopf).json()
    assert len(antwort["berichte"]) == 1
    assert antwort["berichte"][0]["titel"] == "Testbericht"
    assert antwort["berichte"][0]["kennzahlen"][0]["wert"] == "7"


def test_kaputtes_modul_gibt_200_mit_fehlerstatus(klient, kopf):
    # Der Endpunkt selbst ist nicht kaputt, nur das Modul - deshalb 200 plus Status im Inhalt
    antwort = klient.post("/module/kaputt/lauf", headers=kopf)
    assert antwort.status_code == 200
    assert antwort.json()["status"] == "fehler"


def test_unbekanntes_modul_gibt_404(klient, kopf):
    assert klient.get("/module/gibtsnicht", headers=kopf).status_code == 404
    assert klient.post("/module/gibtsnicht/lauf", headers=kopf).status_code == 404
    assert klient.get("/module/gibtsnicht/berichte", headers=kopf).status_code == 404


def test_laeufe_endpunkt(klient, kopf):
    klient.post("/module/testmodul/lauf", headers=kopf)
    laeufe = klient.get("/module/testmodul/laeufe", headers=kopf).json()["laeufe"]

    assert len(laeufe) == 1
    assert laeufe[0]["status"] == "ok"


def test_gelesen_setzen_nullt_den_zaehler(klient, kopf):
    klient.post("/module/testmodul/lauf", headers=kopf)
    assert klient.get("/module/testmodul", headers=kopf).json()["ungelesen"] == 1

    klient.post("/module/testmodul/gelesen", json={}, headers=kopf)
    assert klient.get("/module/testmodul", headers=kopf).json()["ungelesen"] == 0


def test_zustandsuebersicht_meldet_auffaellige(klient, kopf):
    for durchgang in range(3):
        klient.post("/module/kaputt/lauf", headers=kopf)

    zustand = klient.get("/module/zustand", headers=kopf).json()

    namen = []
    for eintrag in zustand["auffaellig"]:
        namen.append(eintrag["name"])

    assert "kaputt" in namen
    assert zustand["anzahl_module"] == 3


def test_status_zeigt_module_und_verbrauch(klient, kopf):
    status = klient.get("/status", headers=kopf).json()

    assert "testmodul" in status["module"]
    assert status["llm_anbieter"] in ["claude", "ollama"]
    assert "verbrauch_heute" in status


def test_kostenendpunkt(klient, kopf):
    antwort = klient.get("/kosten", headers=kopf).json()
    assert antwort["heute"]["tokens_gesamt"] == 0


def test_todo_anlegen_und_abhaken(klient, kopf):
    angelegt = klient.post("/tasks", json={"inhalt": "Test", "faellig_am": None}, headers=kopf).json()
    assert angelegt["inhalt"] == "Test"

    klient.patch("/tasks/" + str(angelegt["id"]), json={"erledigt": True}, headers=kopf)
    assert len(klient.get("/tasks", headers=kopf).json()) == 0


def test_swagger_ist_im_betrieb_aus(klient):
    assert klient.get("/docs").status_code == 404
    assert klient.get("/openapi.json").status_code == 404


def test_modellfehler_wird_lesbar_statt_500(klient, kopf, monkeypatch):
    from app.llm import auswahl
    from app.llm.basis import ModellBasis, ModellFehler

    class KaputtesModell(ModellBasis):
        def _aufruf(self, system_anweisung, benutzer_text, max_tokens, gross):
            raise ModellFehler("Key passt nicht")

    auswahl.modell_ersetzen(KaputtesModell())
    try:
        antwort = klient.post("/chat", json={"text": "Hallo"}, headers=kopf)
        assert antwort.status_code == 503
        assert "Modell nicht verfügbar" in antwort.json()["detail"]
    finally:
        auswahl.zwischenspeicher_leeren()


def test_budgetfehler_wird_lesbar_statt_500(klient, kopf, fake_modell):
    from app.config import EINSTELLUNGEN
    from app.dienste import kosten

    EINSTELLUNGEN.tokenbudget_pro_tag = 100
    kosten.verbrauch_buchen(500, 0)

    antwort = klient.post("/chat", json={"text": "Hallo"}, headers=kopf)
    assert antwort.status_code == 429
    assert "Budget" in antwort.json()["detail"]


def test_fehlendes_modell_paket_wird_lesbar(klient, kopf, monkeypatch):
    # Wenn das anthropic-Paket fehlt, darf das kein nackter Absturz sein
    import builtins
    from app.llm import auswahl

    auswahl.zwischenspeicher_leeren()
    echter_import = builtins.__import__

    def import_mit_luecke(name, *weitere, **benannte):
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return echter_import(name, *weitere, **benannte)

    monkeypatch.setattr(builtins, "__import__", import_mit_luecke)
    try:
        antwort = klient.post("/chat", json={"text": "Hallo"}, headers=kopf)
        assert antwort.status_code == 503
        assert "fehlt" in antwort.json()["detail"]
    finally:
        auswahl.zwischenspeicher_leeren()
