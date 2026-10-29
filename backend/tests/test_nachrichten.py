"""Tests für News-Filter, Interessensprofil und Feedback"""

from app.dienste import nachrichten


def test_standard_interessen_werden_angelegt():
    angelegt = nachrichten.standard_interessen_anlegen()
    assert len(angelegt) > 0

    # ein zweiter Aufruf darf nicht doppelt anlegen
    nochmal = nachrichten.standard_interessen_anlegen()
    assert len(nochmal) == len(angelegt)


def test_interessen_ersetzen():
    nachrichten.interessen_setzen(["KI", "Halbleiter", "Fussball"])
    aktuell = nachrichten.interessen_holen()

    stichwoerter = []
    for eintrag in aktuell:
        stichwoerter.append(eintrag["stichwort"])

    assert stichwoerter == ["KI", "Halbleiter", "Fussball"]


def test_daumen_runter_filtert_die_meldung_raus():
    nachrichten.feedback_speichern("Promi trennt sich", "down")

    schlagzeilen = [
        {"quelle": "ORF", "titel": "Promi trennt sich", "beschreibung": "", "link": ""},
        {"quelle": "heise", "titel": "Neuer Chip von TSMC", "beschreibung": "", "link": ""},
    ]
    uebrig = nachrichten.schon_bewertet_filtern(schlagzeilen)

    assert len(uebrig) == 1
    assert uebrig[0]["titel"] == "Neuer Chip von TSMC"


def test_feedback_landet_im_prompt():
    nachrichten.feedback_speichern("Chipfertigung in Europa", "up")
    nachrichten.feedback_speichern("Fussball-Ergebnisse", "down")

    gut, schlecht = nachrichten.feedback_zusammenfassen()
    assert "Chipfertigung in Europa" in gut
    assert "Fussball-Ergebnisse" in schlecht


def test_meldungen_holen_ordnet_quelle_zu(fake_modell, monkeypatch):
    def fake_feeds():
        return [
            {"quelle": "heise", "titel": "Neuer Chip", "beschreibung": "schnell", "link": "https://heise.de/1"},
            {"quelle": "ORF", "titel": "Wetter", "beschreibung": "", "link": "https://orf.at/2"},
        ]

    monkeypatch.setattr(nachrichten, "alle_feeds_einlesen", fake_feeds)
    fake_modell.antwort_vormerken(
        '{"meldungen": [{"nummer": 1, "titel": "Chip-News", "zusammenfassung": "Ein neuer Chip ist da."}]}'
    )

    meldungen = nachrichten.meldungen_holen()

    assert len(meldungen) == 1
    assert meldungen[0]["quelle"] == "heise"
    assert meldungen[0]["link"] == "https://heise.de/1"


def test_meldungen_ohne_feeds_ohne_modellaufruf(fake_modell, monkeypatch):
    def keine_feeds():
        return []

    monkeypatch.setattr(nachrichten, "alle_feeds_einlesen", keine_feeds)

    meldungen = nachrichten.meldungen_holen()

    assert meldungen == []
    # wichtig fürs Token-Sparen: ohne Inhalt darf gar kein Modellaufruf passieren
    assert len(fake_modell.aufrufe) == 0
