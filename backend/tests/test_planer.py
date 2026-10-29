"""Tests für den Planer: Lauf-Umklammerung, Protokoll, Fehlerfang, Sperre"""

import threading

from app import planer
from app.dienste import berichte as berichte_dienst


def test_erfolgreicher_lauf_wird_protokolliert():
    ergebnis = planer.lauf_ausfuehren("testmodul")

    assert ergebnis["status"] == "ok"
    assert ergebnis["bericht"]["titel"] == "Testbericht"

    laeufe = berichte_dienst.laeufe_von_modul("testmodul")
    assert len(laeufe) == 1
    assert laeufe[0]["status"] == "ok"
    assert laeufe[0]["ende"] is not None


def test_bericht_behaelt_kennzahlen_und_eintraege():
    planer.lauf_ausfuehren("testmodul")
    bericht = berichte_dienst.letzter_bericht("testmodul")

    assert bericht["kennzahlen"][0]["name"] == "Zahl"
    assert bericht["kennzahlen"][0]["wert"] == "7"
    assert bericht["eintraege"][0]["link"] == "https://example.at"


def test_kaputtes_modul_wirft_nicht_hoch():
    ergebnis = planer.lauf_ausfuehren("kaputt")

    assert ergebnis["status"] == "fehler"
    assert "geht schief" in ergebnis["meldung"]
    assert ergebnis["bericht"] is None


def test_fehler_landet_im_protokoll_und_kein_bericht():
    planer.lauf_ausfuehren("kaputt")

    laeufe = berichte_dienst.laeufe_von_modul("kaputt")
    assert laeufe[0]["status"] == "fehler"
    assert "RuntimeError" in laeufe[0]["meldung"]
    assert berichte_dienst.letzter_bericht("kaputt") is None


def test_ein_kaputtes_modul_blockiert_die_anderen_nicht():
    planer.lauf_ausfuehren("kaputt")
    ergebnis = planer.lauf_ausfuehren("testmodul")

    assert ergebnis["status"] == "ok"


def test_unbekanntes_modul():
    ergebnis = planer.lauf_ausfuehren("gibtsnicht")
    assert ergebnis["status"] == "unbekannt"


def test_doppelter_start_wird_abgewiesen():
    sperre = planer.sperre_fuer("testmodul")
    sperre.acquire()

    try:
        ergebnis = planer.lauf_ausfuehren("testmodul")
        assert ergebnis["status"] == "beschaeftigt"
    finally:
        sperre.release()


def test_haengende_laeufe_werden_aufgeraeumt():
    lauf_id = berichte_dienst.lauf_beginnen("testmodul")
    assert berichte_dienst.laeufe_von_modul("testmodul")[0]["status"] == "laeuft"

    anzahl = berichte_dienst.haengende_laeufe_aufraeumen()

    assert anzahl == 1
    assert berichte_dienst.laeufe_von_modul("testmodul")[0]["status"] == "abgebrochen"


def test_zwei_module_gleichzeitig_gehen():
    ergebnisse = {}

    def laufen(name):
        ergebnisse[name] = planer.lauf_ausfuehren(name)["status"]

    erster = threading.Thread(target=laufen, args=("testmodul",))
    zweiter = threading.Thread(target=laufen, args=("kaputt",))

    erster.start()
    zweiter.start()
    erster.join(timeout=10)
    zweiter.join(timeout=10)

    assert ergebnisse["testmodul"] == "ok"
    assert ergebnisse["kaputt"] == "fehler"
