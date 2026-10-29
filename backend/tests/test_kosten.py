"""Tests für die Kostenbremse"""

import pytest

from app import planer
from app.config import EINSTELLUNGEN
from app.dienste import berichte as berichte_dienst
from app.dienste import kosten
from app.dienste.kosten import BudgetErschoepft
from app.llm.auswahl import modell


def test_verbrauch_wird_dem_modul_zugeordnet(fake_modell):
    planer.lauf_ausfuehren("modellmodul")
    verbrauch = kosten.verbrauch_heute()

    assert verbrauch["tokens_ein"] == 100
    assert verbrauch["tokens_aus"] == 50
    assert verbrauch["pro_modul"][0]["modul"] == "modellmodul"


def test_tokens_stehen_im_lauf_protokoll(fake_modell):
    planer.lauf_ausfuehren("modellmodul")
    lauf = berichte_dienst.laeufe_von_modul("modellmodul")[0]

    assert lauf["tokens_ein"] == 100
    assert lauf["tokens_aus"] == 50


def test_aufruf_ohne_modul_wird_als_direkt_gebucht(fake_modell):
    modell().text_erzeugen("System", "Frage")
    verbrauch = kosten.verbrauch_heute()

    assert verbrauch["pro_modul"][0]["modul"] == "direkt"


def test_tagesdeckel_lehnt_weitere_aufrufe_ab(fake_modell):
    EINSTELLUNGEN.tokenbudget_pro_tag = 200

    modell().text_erzeugen("System", "Frage")   # 150 Tokens, geht noch
    modell().text_erzeugen("System", "Frage")   # jetzt bei 300, Deckel ueberschritten

    with pytest.raises(BudgetErschoepft):
        modell().text_erzeugen("System", "Frage")


def test_ueberschrittener_deckel_macht_den_lauf_zum_fehler(fake_modell):
    # Der Deckel wird vor dem Aufruf geprueft, vorher kann niemand wissen was er kostet
    # Also erst Verbrauch aufbauen, dann darf der naechste Lauf nicht mehr starten
    EINSTELLUNGEN.tokenbudget_pro_tag = 100
    kosten.verbrauch_buchen(500, 0)

    ergebnis = planer.lauf_ausfuehren("modellmodul")

    assert ergebnis["status"] == "fehler"
    assert "Budget" in ergebnis["meldung"]


def test_lauf_deckel_greift_pro_lauf(fake_modell):
    EINSTELLUNGEN.tokenbudget_pro_lauf = 100

    # erster Aufruf im Lauf geht durch, danach ist der Lauf-Deckel erreicht
    kosten.aktuelles_modul_setzen("modellmodul")
    try:
        modell().text_erzeugen("System", "eins")
        with pytest.raises(BudgetErschoepft):
            modell().text_erzeugen("System", "zwei")
    finally:
        kosten.aktuelles_modul_loeschen()


def test_lauf_deckel_wird_pro_lauf_zurueckgesetzt(fake_modell):
    EINSTELLUNGEN.tokenbudget_pro_lauf = 200

    erster = planer.lauf_ausfuehren("modellmodul")
    zweiter = planer.lauf_ausfuehren("modellmodul")

    assert erster["status"] == "ok"
    assert zweiter["status"] == "ok"


def test_modul_ohne_modell_verbraucht_nichts():
    planer.lauf_ausfuehren("testmodul")
    assert kosten.verbrauch_heute()["tokens_gesamt"] == 0
