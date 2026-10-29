"""Tests fürs Morning Briefing"""

from app.dienste import briefing, kalender, mail, nachrichten, todos


def alles_faken(monkeypatch, meldungen):
    def keine_termine(tage=1):
        return [{"titel": "Mathe-Schularbeit", "beginn": "2026-09-14T08:00:00", "ende": "", "ganztaegig": False, "ort": "BULME"}], ""

    def kein_newsletter():
        return ""

    def feste_meldungen(newsletter_text=""):
        return meldungen

    monkeypatch.setattr(kalender, "termine_holen", keine_termine)
    monkeypatch.setattr(mail, "newsletter_text_holen", kein_newsletter)
    monkeypatch.setattr(nachrichten, "meldungen_holen", feste_meldungen)


def test_briefing_setzt_sich_zusammen(monkeypatch):
    alles_faken(monkeypatch, [{"titel": "Chip-News", "zusammenfassung": "Was Neues.", "quelle": "heise", "link": ""}])
    todos.anlegen("Hausuebung machen")

    ergebnis = briefing.bauen(neu_laden=True)

    assert len(ergebnis["termine"]) == 1
    assert len(ergebnis["todos"]) == 1
    assert len(ergebnis["news"]) == 1


def test_briefing_kommt_beim_zweiten_mal_aus_dem_zwischenspeicher(monkeypatch):
    aufrufe = {"anzahl": 0}

    def zaehlende_meldungen(newsletter_text=""):
        aufrufe["anzahl"] = aufrufe["anzahl"] + 1
        return []

    alles_faken(monkeypatch, [])
    monkeypatch.setattr(nachrichten, "meldungen_holen", zaehlende_meldungen)

    briefing.bauen(neu_laden=True)
    briefing.bauen()
    briefing.bauen()

    assert aufrufe["anzahl"] == 1


def test_kaputte_news_legen_das_briefing_nicht_lahm(monkeypatch):
    def geht_schief(newsletter_text=""):
        raise RuntimeError("Feed nicht erreichbar")

    alles_faken(monkeypatch, [])
    monkeypatch.setattr(nachrichten, "meldungen_holen", geht_schief)

    ergebnis = briefing.bauen(neu_laden=True)

    assert ergebnis["news"] == []
    assert len(ergebnis["hinweise"]) > 0
    assert len(ergebnis["termine"]) == 1


def test_erledigte_todos_kommen_nicht_ins_briefing(monkeypatch):
    alles_faken(monkeypatch, [])
    fertig = todos.anlegen("schon erledigt")
    todos.aendern(fertig["id"], erledigt=True)
    todos.anlegen("noch offen")

    ergebnis = briefing.bauen(neu_laden=True)
    assert len(ergebnis["todos"]) == 1


def test_todos_in_der_zukunft_kommen_noch_nicht(monkeypatch):
    alles_faken(monkeypatch, [])
    todos.anlegen("nächste Woche", "2099-01-01T09:00:00")
    todos.anlegen("ohne Datum")

    ergebnis = briefing.bauen(neu_laden=True)
    assert len(ergebnis["todos"]) == 1
    assert ergebnis["todos"][0]["inhalt"] == "ohne Datum"


def test_vorlesetext_enthaelt_alles(monkeypatch):
    alles_faken(monkeypatch, [{"titel": "Chip-News", "zusammenfassung": "Was Neues.", "quelle": "heise", "link": ""}])
    todos.anlegen("Hausuebung machen")

    text = briefing.als_text(briefing.bauen(neu_laden=True))

    assert "Mathe-Schularbeit" in text
    assert "Hausuebung machen" in text
    assert "Chip-News" in text
