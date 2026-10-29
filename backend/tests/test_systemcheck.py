"""Tests für das echte Systemcheck-Modul"""

import pytest

from app import planer
from app.bots import systemcheck, verzeichnis
from app.dienste import berichte as berichte_dienst


@pytest.fixture
def echtes_systemcheck(testmodule):
    """Das echte Modul neben die Testmodule stellen"""
    verzeichnis.MODULE.append(systemcheck.SystemCheck())
    yield
    verzeichnis.MODULE.pop()


def test_systemcheck_laeuft_ohne_modell_und_ohne_netz(echtes_systemcheck):
    ergebnis = planer.lauf_ausfuehren("systemcheck")

    assert ergebnis["status"] == "ok"

    from app.dienste import kosten
    assert kosten.verbrauch_heute()["tokens_gesamt"] == 0


def test_systemcheck_meldet_ruhe_wenn_alles_laeuft(echtes_systemcheck):
    planer.lauf_ausfuehren("testmodul")
    planer.lauf_ausfuehren("systemcheck")

    bericht = berichte_dienst.letzter_bericht("systemcheck")

    # "kaputt" und "modellmodul" sind noch nie gelaufen, die gelten als auffaellig
    assert "Module auffällig" == bericht["kennzahlen"][0]["name"]


def test_systemcheck_findet_wiederholte_fehler(echtes_systemcheck):
    for durchgang in range(3):
        planer.lauf_ausfuehren("kaputt")

    planer.lauf_ausfuehren("systemcheck")
    bericht = berichte_dienst.letzter_bericht("systemcheck")

    gesammelt = ""
    for eintrag in bericht["eintraege"]:
        gesammelt = gesammelt + eintrag["titel"]

    assert "Kaputtes Modul" in gesammelt
    assert "Fehler in Folge" in gesammelt


def test_systemcheck_schaut_sich_selbst_nicht_an(echtes_systemcheck):
    planer.lauf_ausfuehren("systemcheck")
    bericht = berichte_dienst.letzter_bericht("systemcheck")

    for eintrag in bericht["eintraege"]:
        assert "Systemcheck" not in eintrag["titel"]


def test_kennzahlen_sind_vollstaendig(echtes_systemcheck):
    planer.lauf_ausfuehren("systemcheck")
    bericht = berichte_dienst.letzter_bericht("systemcheck")

    namen = []
    for kennzahl in bericht["kennzahlen"]:
        namen.append(kennzahl["name"])

    assert "Platte frei" in namen
    assert "Datenbank" in namen
    assert "Tokens heute" in namen
