"""Tests für den PC-Zugang im Browser"""


def test_ohne_cookie_leitet_zum_anmelden(klient):
    antwort = klient.get("/", follow_redirects=False)

    assert antwort.status_code == 303
    assert antwort.headers["location"] == "/anmelden"


def test_anmeldeformular_kommt(klient):
    antwort = klient.get("/anmelden")
    assert antwort.status_code == 200
    assert "API-Key" in antwort.text


def test_falscher_key_fuehrt_zurueck_zum_formular(klient):
    antwort = klient.post("/anmelden", data={"key": "falsch"}, follow_redirects=False)

    assert antwort.status_code == 303
    assert "fehler" in antwort.headers["location"]
    assert "steward_key" not in antwort.cookies


def test_richtiger_key_setzt_das_cookie(klient):
    antwort = klient.post("/anmelden", data={"key": "test-key"}, follow_redirects=False)

    assert antwort.status_code == 303
    assert antwort.headers["location"] == "/"
    # HttpOnly, damit der Key nicht per JavaScript auslesbar ist
    assert "httponly" in antwort.headers["set-cookie"].lower()


def test_uebersicht_zeigt_die_module(klient, kopf):
    klient.post("/module/testmodul/lauf", headers=kopf)
    klient.post("/anmelden", data={"key": "test-key"})

    antwort = klient.get("/")

    assert antwort.status_code == 200
    assert "Testmodul" in antwort.text
    assert "Testbericht" in antwort.text


def test_abmelden_loescht_das_cookie(klient):
    klient.post("/anmelden", data={"key": "test-key"})
    antwort = klient.get("/abmelden", follow_redirects=False)

    assert antwort.status_code == 303
    assert klient.get("/", follow_redirects=False).status_code == 303
