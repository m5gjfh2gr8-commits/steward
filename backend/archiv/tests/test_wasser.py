"""Tests für den Flüssigkeits-Counter"""

from app.dienste import wasser


def test_eintragen_und_zusammenzaehlen():
    wasser.eintragen(250)
    wasser.eintragen(500)

    stand = wasser.heutiger_stand()
    assert stand["summe_ml"] == 750
    assert len(stand["eintraege"]) == 2


def test_letzter_eintrag_wird_gemerkt():
    leer = wasser.heutiger_stand()
    assert leer["letzter_eintrag"] is None

    wasser.eintragen(300)
    voll = wasser.heutiger_stand()
    assert voll["letzter_eintrag"] is not None


def test_loeschen():
    eintrag_id = wasser.eintragen(250)
    assert wasser.loeschen(eintrag_id) is True
    assert wasser.heutiger_stand()["summe_ml"] == 0
