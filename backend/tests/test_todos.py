"""Tests für Todos inklusive Freitext-Zerlegung"""

from app.dienste import todos


def test_anlegen_und_lesen():
    angelegt = todos.anlegen("Mathe lernen", "2026-09-20T15:00:00")

    assert angelegt["inhalt"] == "Mathe lernen"
    assert angelegt["erledigt"] == 0

    offene = todos.liste_holen(nur_offen=True)
    assert len(offene) == 1


def test_erledigt_setzen_versteckt_das_todo():
    angelegt = todos.anlegen("Mist rausbringen")
    todos.aendern(angelegt["id"], erledigt=True)

    assert len(todos.liste_holen(nur_offen=True)) == 0
    assert len(todos.liste_holen(nur_offen=False)) == 1


def test_loeschen():
    angelegt = todos.anlegen("weg damit")
    assert todos.loeschen(angelegt["id"]) is True
    assert todos.loeschen(angelegt["id"]) is False


def test_sortierung_faellige_zuerst():
    todos.anlegen("ohne Datum")
    todos.anlegen("spaet", "2026-12-01T09:00:00")
    todos.anlegen("frueh", "2026-09-15T09:00:00")

    offene = todos.liste_holen(nur_offen=True)
    assert offene[0]["inhalt"] == "frueh"
    assert offene[1]["inhalt"] == "spaet"
    assert offene[2]["inhalt"] == "ohne Datum"


def test_freitext_zerlegen(fake_modell):
    fake_modell.antwort_vormerken('{"inhalt": "Zahnarzt", "faellig_am": "2026-09-15T15:00:00", "ist_termin": true}')

    ergebnis = todos.freitext_zerlegen("morgen um 3 zum Zahnarzt")

    assert ergebnis["inhalt"] == "Zahnarzt"
    assert ergebnis["ist_termin"] is True
    # das heutige Datum muss im Prompt stehen, sonst kann das Modell "morgen" nicht ausrechnen
    assert "Aktuelles Datum" in fake_modell.aufrufe[0]["text"]
