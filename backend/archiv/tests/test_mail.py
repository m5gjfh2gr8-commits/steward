"""Tests für die Mail-Triage (ohne echten IMAP-Server)"""

from app.dienste import mail


def test_bewertungen_werden_richtig_zugeordnet(fake_modell):
    mails = [
        {"postfach": "iCloud", "absender": "schule@bulme.at", "betreff": "Schularbeit", "datum": "", "anfang": "Termin"},
        {"postfach": "Gmail", "absender": "shop@werbung.at", "betreff": "50% Rabatt", "datum": "", "anfang": "Sale"},
    ]

    fake_modell.antwort_vormerken(
        '{"bewertungen": [{"nummer": 1, "stufe": "wichtig", "grund": "Termin in der Schule"},'
        '{"nummer": 2, "stufe": "egal", "grund": "Werbung"}]}'
    )

    bewertet = mail.mails_bewerten(mails)

    assert bewertet[0]["stufe"] == "wichtig"
    assert bewertet[1]["stufe"] == "egal"
    # der Mailtext selbst wird nicht weitergegeben, nur die Kopfzeilen
    assert "anfang" not in bewertet[0]


def test_fehlende_bewertung_wird_zu_egal(fake_modell):
    mails = [{"postfach": "iCloud", "absender": "a@b.at", "betreff": "Test", "datum": "", "anfang": ""}]
    fake_modell.antwort_vormerken('{"bewertungen": []}')

    bewertet = mail.mails_bewerten(mails)
    assert bewertet[0]["stufe"] == "egal"


def test_ohne_mails_kein_modellaufruf(fake_modell):
    assert mail.mails_bewerten([]) == []
    assert len(fake_modell.aufrufe) == 0


def test_zwischenspeicher_verhindert_zweite_abfrage(fake_modell, monkeypatch):
    aufrufe = {"anzahl": 0}

    def fake_abfragen(tage=2):
        aufrufe["anzahl"] = aufrufe["anzahl"] + 1
        return [{"postfach": "iCloud", "absender": "a@b.at", "betreff": "Hallo", "datum": "", "anfang": ""}], []

    monkeypatch.setattr(mail, "alle_postfaecher_abfragen", fake_abfragen)
    fake_modell.antwort_vormerken('{"bewertungen": [{"nummer": 1, "stufe": "wichtig", "grund": "x"}]}')

    erste = mail.wichtige_mails()
    zweite = mail.wichtige_mails()

    assert erste["anzahl_wichtig"] == 1
    assert zweite["anzahl_wichtig"] == 1
    assert aufrufe["anzahl"] == 1


def test_kopfzeile_dekodieren():
    kodiert = "=?utf-8?B?SGFsbG8gTG9yZW56?="
    assert mail.kopfzeile_dekodieren(kodiert) == "Hallo Lorenz"
    assert mail.kopfzeile_dekodieren(None) == ""
