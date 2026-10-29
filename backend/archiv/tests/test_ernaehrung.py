"""Tests für den Kalorien-/Makro-Tracker"""

from app.dienste import ernaehrung, naehrwerte


def test_hochrechnen_auf_menge():
    pro_100g = {"kcal": 500.0, "eiweiss_g": 10.0, "kohlenhydrate_g": 50.0, "fett_g": 30.0}
    ergebnis = ernaehrung.auf_menge_hochrechnen(pro_100g, 50)

    assert ergebnis["kcal"] == 250.0
    assert ergebnis["eiweiss_g"] == 5.0
    assert ergebnis["fett_g"] == 15.0


def test_summe_bilden():
    eintraege = [
        {"kcal": 100.0, "eiweiss_g": 5.0, "kohlenhydrate_g": 10.0, "fett_g": 2.0},
        {"kcal": 250.5, "eiweiss_g": 3.0, "kohlenhydrate_g": 20.0, "fett_g": 8.0},
    ]
    summe = ernaehrung.summe_bilden(eintraege)

    assert summe["kcal"] == 350.5
    assert summe["eiweiss_g"] == 8.0


def test_zahl_oder_null_frisst_muell():
    assert naehrwerte.zahl_oder_null(None) == 0.0
    assert naehrwerte.zahl_oder_null("keine Ahnung") == 0.0
    assert naehrwerte.zahl_oder_null("12.5") == 12.5


def test_eintragen_mit_datenbank_treffer(fake_modell, monkeypatch):
    fake_modell.antwort_vormerken(
        '{"items": [{"bezeichnung": "Nutella", "menge_text": "1 EL", "menge_g": 20, '
        '"suchbegriff_deutsch": "Nutella", "suchbegriff_englisch": "hazelnut spread", "ist_markenprodukt": true}]}'
    )

    def fake_nachschlagen(deutsch, englisch, ist_marke):
        werte = {"name": "Nutella", "kcal": 539.0, "eiweiss_g": 6.3, "kohlenhydrate_g": 57.5, "fett_g": 30.9}
        return werte, "open_food_facts"

    monkeypatch.setattr(naehrwerte, "nachschlagen", fake_nachschlagen)

    gespeichert = ernaehrung.eintragen("ein Esslöffel Nutella")

    assert len(gespeichert) == 1
    assert gespeichert[0]["quelle"] == "open_food_facts"
    assert gespeichert[0]["kcal"] == 107.8


def test_eintragen_faellt_auf_schaetzung_zurueck(fake_modell, monkeypatch):
    fake_modell.antwort_vormerken(
        '{"items": [{"bezeichnung": "Omas Apfelstrudel", "menge_text": "1 Stück", "menge_g": 150, '
        '"suchbegriff_deutsch": "Apfelstrudel", "suchbegriff_englisch": "apple strudel", "ist_markenprodukt": false}]}'
    )
    fake_modell.antwort_vormerken('{"kcal": 240, "eiweiss_g": 3, "kohlenhydrate_g": 35, "fett_g": 9}')

    def nichts_gefunden(deutsch, englisch, ist_marke):
        return None, None

    monkeypatch.setattr(naehrwerte, "nachschlagen", nichts_gefunden)

    gespeichert = ernaehrung.eintragen("ein Stück Apfelstrudel")

    assert gespeichert[0]["quelle"] == "geschaetzt"
    assert gespeichert[0]["kcal"] == 360.0


def test_eintrag_bleibt_editierbar(fake_modell, monkeypatch):
    fake_modell.antwort_vormerken(
        '{"items": [{"bezeichnung": "Apfel", "menge_text": "1", "menge_g": 100, '
        '"suchbegriff_deutsch": "Apfel", "suchbegriff_englisch": "apple", "ist_markenprodukt": false}]}'
    )

    def fake_nachschlagen(deutsch, englisch, ist_marke):
        return {"name": "Apfel", "kcal": 52.0, "eiweiss_g": 0.3, "kohlenhydrate_g": 14.0, "fett_g": 0.2}, "usda"

    monkeypatch.setattr(naehrwerte, "nachschlagen", fake_nachschlagen)

    gespeichert = ernaehrung.eintragen("ein Apfel")
    geaendert = ernaehrung.aendern(gespeichert[0]["id"], kcal=95.0)

    assert geaendert["kcal"] == 95.0
    assert geaendert["bearbeitet"] == 1
    # der Rest darf beim Ändern nicht verloren gehen
    assert geaendert["beschreibung"] == "Apfel"


def test_heutiger_stand_zaehlt_zusammen(fake_modell, monkeypatch):
    def fake_nachschlagen(deutsch, englisch, ist_marke):
        return {"name": "x", "kcal": 100.0, "eiweiss_g": 1.0, "kohlenhydrate_g": 1.0, "fett_g": 1.0}, "usda"

    monkeypatch.setattr(naehrwerte, "nachschlagen", fake_nachschlagen)

    fake_modell.antwort_vormerken(
        '{"items": [{"bezeichnung": "a", "menge_g": 100, "suchbegriff_deutsch": "a", "suchbegriff_englisch": "a", "ist_markenprodukt": false},'
        '{"bezeichnung": "b", "menge_g": 200, "suchbegriff_deutsch": "b", "suchbegriff_englisch": "b", "ist_markenprodukt": false}]}'
    )

    ernaehrung.eintragen("a und b")
    stand = ernaehrung.heutiger_stand()

    assert len(stand["eintraege"]) == 2
    assert stand["summe"]["kcal"] == 300.0
