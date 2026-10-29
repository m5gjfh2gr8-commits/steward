"""Tests für das eine Eingabefeld der App"""

from app import planer
from app.dienste import chat


def test_aufgabe_wird_angelegt(fake_modell):
    fake_modell.antwort_vormerken('{"art": "aufgabe"}')
    fake_modell.antwort_vormerken('{"inhalt": "Zahnarzt", "faellig_am": "2026-10-20T15:00:00", "ist_termin": true}')

    ergebnis = chat.verarbeiten("montag um 3 zum Zahnarzt")

    assert ergebnis["art"] == "aufgabe"
    assert ergebnis["daten"]["inhalt"] == "Zahnarzt"


def test_frage_bekommt_den_modulstand_mit(fake_modell):
    planer.lauf_ausfuehren("testmodul")

    fake_modell.antwort_vormerken('{"art": "frage"}')
    fake_modell.antwort_vormerken("Alles ruhig.")

    ergebnis = chat.verarbeiten("wie schaut es aus")

    assert ergebnis["art"] == "frage"
    # Der Kontext muss die Module samt letztem Bericht enthalten, sonst raet das Modell
    kontext = fake_modell.aufrufe[1]["text"]
    assert "Testmodul" in kontext
    assert "Testbericht" in kontext


def test_unbekannte_art_wird_zur_frage(fake_modell):
    fake_modell.antwort_vormerken('{"art": "irgendwas"}')
    fake_modell.antwort_vormerken("Antwort")

    ergebnis = chat.verarbeiten("hm")
    assert ergebnis["art"] == "frage"
