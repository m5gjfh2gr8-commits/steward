"""Tests für die Überwachung: Zustand, Fehler in Folge, Ungelesen-Zähler"""

from app import planer
from app.bots import verzeichnis
from app.dienste import berichte as berichte_dienst


def test_neues_modul_ist_neu():
    zustand = berichte_dienst.zustand_von_modul(verzeichnis.nach_name("testmodul"))

    assert zustand["zustand"] == "neu"
    assert zustand["letzter_erfolg"] is None
    assert zustand["letzter_bericht"] is None


def test_nach_erfolg_ist_der_zustand_ok():
    planer.lauf_ausfuehren("testmodul")
    zustand = berichte_dienst.zustand_von_modul(verzeichnis.nach_name("testmodul"))

    assert zustand["zustand"] == "ok"
    assert zustand["letzter_erfolg"] is not None


def test_ein_fehler_macht_wackelig_drei_machen_kaputt():
    planer.lauf_ausfuehren("kaputt")
    assert berichte_dienst.zustand_von_modul(verzeichnis.nach_name("kaputt"))["zustand"] == "wackelig"

    planer.lauf_ausfuehren("kaputt")
    planer.lauf_ausfuehren("kaputt")
    assert berichte_dienst.zustand_von_modul(verzeichnis.nach_name("kaputt"))["zustand"] == "kaputt"


def test_erfolg_setzt_die_fehlerzaehlung_zurueck():
    planer.lauf_ausfuehren("kaputt")
    planer.lauf_ausfuehren("kaputt")
    assert berichte_dienst.fehler_in_folge("kaputt") == 2

    # dasselbe Modul kann nicht erfolgreich laufen, deshalb am Testmodul pruefen
    planer.lauf_ausfuehren("testmodul")
    assert berichte_dienst.fehler_in_folge("testmodul") == 0


def test_ungelesen_zaehlt_neue_berichte():
    assert berichte_dienst.anzahl_ungelesen("testmodul") == 0

    planer.lauf_ausfuehren("testmodul")
    planer.lauf_ausfuehren("testmodul")
    assert berichte_dienst.anzahl_ungelesen("testmodul") == 2

    berichte_dienst.gelesen_setzen("testmodul")
    assert berichte_dienst.anzahl_ungelesen("testmodul") == 0


def test_nach_dem_lesen_zaehlt_nur_was_danach_kam():
    planer.lauf_ausfuehren("testmodul")
    berichte_dienst.gelesen_setzen("testmodul")

    # Der Zeitstempel hat Sekundengenauigkeit, deshalb einen spaeteren Bericht erzwingen
    berichte_dienst.gelesen_setzen("testmodul", "2020-01-01T00:00:00+01:00")
    assert berichte_dienst.anzahl_ungelesen("testmodul") == 1


def test_zustand_aller_module_liefert_alle():
    alle = berichte_dienst.zustand_aller_module()
    namen = []
    for eintrag in alle:
        namen.append(eintrag["name"])

    assert "testmodul" in namen
    assert "kaputt" in namen
