"""
Kalorien- und Makro-Tracker

Ablauf bei einer Eingabe wie "2 Scheiben Schwarzbrot mit Nutella":
1. Modell zerlegt den Satz in Einzel-Items mit geschätzter Grammzahl
2. pro Item wird in Open Food Facts / USDA nachgeschlagen
3. nur wenn dort nichts gefunden wird, schätzt das Modell selbst
4. jedes Item wird als eigene Zeile gespeichert und bleibt einzeln editierbar
"""

from app.datenbank import verbindung, zeilen_zu_dicts
from app.dienste import naehrwerte
from app.llm.auswahl import modell
from app.zeit import heute_text, jetzt_text, tag_vor_x_tagen_text

SYSTEM_ZERLEGEN = """Du zerlegst eine deutschsprachige Mahlzeitenbeschreibung in einzelne Lebensmittel.
Antworte ausschliesslich mit JSON, ohne Erklärung, in genau dieser Form:
{"items": [{"bezeichnung": "...", "menge_text": "...", "menge_g": 0, "suchbegriff_deutsch": "...", "suchbegriff_englisch": "...", "ist_markenprodukt": true}]}

Regeln:
- ein Eintrag pro Lebensmittel, Belag und Brot getrennt
- "menge_g" ist die geschätzte Menge in Gramm als Zahl, bei Getränken Milliliter als Gramm
- "menge_text" ist die Menge so wie sie genannt wurde, z.B. "2 Scheiben"
- "suchbegriff_deutsch" ist der Produktname wie am Etikett, ohne Menge
- "suchbegriff_englisch" ist die englische Bezeichnung der generischen Zutat, ohne Menge
- "ist_markenprodukt" ist true bei einer konkreten Marke, false bei einer generischen Zutat"""

SYSTEM_SCHAETZEN = """Du schätzt Nährwerte pro 100 Gramm eines Lebensmittels.
Antworte ausschliesslich mit JSON, ohne Erklärung:
{"kcal": 0, "eiweiss_g": 0, "kohlenhydrate_g": 0, "fett_g": 0}"""


def text_zerlegen(text):
    """
    Eingabe: Freitext der Mahlzeit
    Ausgabe: Liste von Item-Dicts wie im System-Prompt beschrieben
    """
    ergebnis = modell().json_erzeugen(SYSTEM_ZERLEGEN, text, max_tokens=800)

    if isinstance(ergebnis, list):
        return ergebnis

    return ergebnis.get("items", [])


def werte_schaetzen(bezeichnung):
    """Rückfall wenn beide Datenbanken nichts liefern - Werte pro 100 g"""
    geschaetzt = modell().json_erzeugen(SYSTEM_SCHAETZEN, bezeichnung, max_tokens=200)
    return {
        "kcal": naehrwerte.zahl_oder_null(geschaetzt.get("kcal")),
        "eiweiss_g": naehrwerte.zahl_oder_null(geschaetzt.get("eiweiss_g")),
        "kohlenhydrate_g": naehrwerte.zahl_oder_null(geschaetzt.get("kohlenhydrate_g")),
        "fett_g": naehrwerte.zahl_oder_null(geschaetzt.get("fett_g")),
    }


def auf_menge_hochrechnen(werte_pro_100g, menge_g):
    faktor = menge_g / 100.0
    return {
        "kcal": round(werte_pro_100g["kcal"] * faktor, 1),
        "eiweiss_g": round(werte_pro_100g["eiweiss_g"] * faktor, 1),
        "kohlenhydrate_g": round(werte_pro_100g["kohlenhydrate_g"] * faktor, 1),
        "fett_g": round(werte_pro_100g["fett_g"] * faktor, 1),
    }


def item_verarbeiten(item):
    """
    Eingabe: ein Item-Dict aus text_zerlegen
    Ausgabe: fertige Zeile mit hochgerechneten Werten, noch nicht gespeichert
    """
    bezeichnung = item.get("bezeichnung", "unbekannt")
    menge_g = naehrwerte.zahl_oder_null(item.get("menge_g"))
    if menge_g <= 0:
        menge_g = 100.0

    menge_text = item.get("menge_text", "")
    such_deutsch = item.get("suchbegriff_deutsch", bezeichnung)
    such_englisch = item.get("suchbegriff_englisch", "")
    ist_marke = bool(item.get("ist_markenprodukt", False))

    gefunden, quelle = naehrwerte.nachschlagen(such_deutsch, such_englisch, ist_marke)

    if gefunden is None:
        werte_pro_100g = werte_schaetzen(bezeichnung)
        quelle = "geschaetzt"
    else:
        werte_pro_100g = gefunden

    hochgerechnet = auf_menge_hochrechnen(werte_pro_100g, menge_g)
    hochgerechnet["beschreibung"] = bezeichnung
    hochgerechnet["menge_text"] = menge_text
    hochgerechnet["quelle"] = quelle
    return hochgerechnet


def eintragen(text):
    """
    Kompletter Weg von Freitext bis gespeicherte Zeilen
    Ausgabe: Liste der gespeicherten Datenbankzeilen
    """
    items = text_zerlegen(text)

    gespeichert = []
    for item in items:
        fertig = item_verarbeiten(item)
        zeile = zeile_speichern(fertig)
        gespeichert.append(zeile)

    return gespeichert


def zeile_speichern(werte):
    verb = verbindung()
    zeiger = verb.execute(
        """INSERT INTO ernaehrung_log
           (zeitpunkt, beschreibung, menge_text, kcal, eiweiss_g, kohlenhydrate_g, fett_g, quelle, bearbeitet)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
        (
            jetzt_text(),
            werte["beschreibung"],
            werte.get("menge_text", ""),
            werte["kcal"],
            werte["eiweiss_g"],
            werte["kohlenhydrate_g"],
            werte["fett_g"],
            werte.get("quelle", "geschaetzt"),
        ),
    )
    neue_id = zeiger.lastrowid
    verb.commit()
    verb.close()
    return einzeln_holen(neue_id)


def einzeln_holen(eintrag_id):
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM ernaehrung_log WHERE id = ?", (eintrag_id,)).fetchone()
    verb.close()
    if zeile is None:
        return None
    return dict(zeile)


def eintraege_von_tag(datum_text):
    verb = verbindung()
    zeilen = verb.execute(
        "SELECT * FROM ernaehrung_log WHERE substr(zeitpunkt, 1, 10) = ? ORDER BY zeitpunkt ASC",
        (datum_text,),
    ).fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def summe_bilden(eintraege):
    summe = {"kcal": 0.0, "eiweiss_g": 0.0, "kohlenhydrate_g": 0.0, "fett_g": 0.0}
    for eintrag in eintraege:
        summe["kcal"] = summe["kcal"] + eintrag["kcal"]
        summe["eiweiss_g"] = summe["eiweiss_g"] + eintrag["eiweiss_g"]
        summe["kohlenhydrate_g"] = summe["kohlenhydrate_g"] + eintrag["kohlenhydrate_g"]
        summe["fett_g"] = summe["fett_g"] + eintrag["fett_g"]

    for schluessel in summe:
        summe[schluessel] = round(summe[schluessel], 1)

    return summe


def heutiger_stand():
    eintraege = eintraege_von_tag(heute_text())
    return {"datum": heute_text(), "eintraege": eintraege, "summe": summe_bilden(eintraege)}


def verlauf(tage=30):
    """
    Tagessummen rückwärts ab heute
    Ausgabe: [{"datum": "2026-09-14", "kcal": ..., "eiweiss_g": ..., ...}]
    """
    ab_datum = tag_vor_x_tagen_text(tage)

    verb = verbindung()
    zeilen = verb.execute(
        """SELECT substr(zeitpunkt, 1, 10) AS datum,
                  ROUND(SUM(kcal), 1) AS kcal,
                  ROUND(SUM(eiweiss_g), 1) AS eiweiss_g,
                  ROUND(SUM(kohlenhydrate_g), 1) AS kohlenhydrate_g,
                  ROUND(SUM(fett_g), 1) AS fett_g
           FROM ernaehrung_log
           WHERE substr(zeitpunkt, 1, 10) >= ?
           GROUP BY datum
           ORDER BY datum DESC""",
        (ab_datum,),
    ).fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def aendern(eintrag_id, beschreibung=None, menge_text=None, kcal=None, eiweiss_g=None, kohlenhydrate_g=None, fett_g=None):
    vorhanden = einzeln_holen(eintrag_id)
    if vorhanden is None:
        return None

    if beschreibung is None:
        beschreibung = vorhanden["beschreibung"]
    if menge_text is None:
        menge_text = vorhanden["menge_text"]
    if kcal is None:
        kcal = vorhanden["kcal"]
    if eiweiss_g is None:
        eiweiss_g = vorhanden["eiweiss_g"]
    if kohlenhydrate_g is None:
        kohlenhydrate_g = vorhanden["kohlenhydrate_g"]
    if fett_g is None:
        fett_g = vorhanden["fett_g"]

    verb = verbindung()
    verb.execute(
        """UPDATE ernaehrung_log
           SET beschreibung = ?, menge_text = ?, kcal = ?, eiweiss_g = ?, kohlenhydrate_g = ?, fett_g = ?, bearbeitet = 1
           WHERE id = ?""",
        (beschreibung, menge_text, kcal, eiweiss_g, kohlenhydrate_g, fett_g, eintrag_id),
    )
    verb.commit()
    verb.close()
    return einzeln_holen(eintrag_id)


def loeschen(eintrag_id):
    verb = verbindung()
    zeiger = verb.execute("DELETE FROM ernaehrung_log WHERE id = ?", (eintrag_id,))
    geloescht = zeiger.rowcount
    verb.commit()
    verb.close()
    return geloescht > 0
