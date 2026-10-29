"""
Flüssigkeits-Counter

Kein Modellaufruf nötig, reines Zusammenzählen
"""

from app.datenbank import verbindung, zeilen_zu_dicts
from app.zeit import heute_text, jetzt_text


def eintragen(menge_ml):
    verb = verbindung()
    zeiger = verb.execute(
        "INSERT INTO wasser_log (zeitpunkt, menge_ml) VALUES (?, ?)",
        (jetzt_text(), int(menge_ml)),
    )
    neue_id = zeiger.lastrowid
    verb.commit()
    verb.close()
    return neue_id


def eintraege_von_heute():
    verb = verbindung()
    zeilen = verb.execute(
        "SELECT * FROM wasser_log WHERE substr(zeitpunkt, 1, 10) = ? ORDER BY zeitpunkt ASC",
        (heute_text(),),
    ).fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def heutiger_stand():
    eintraege = eintraege_von_heute()

    summe = 0
    for eintrag in eintraege:
        summe = summe + eintrag["menge_ml"]

    letzter_zeitpunkt = None
    if len(eintraege) > 0:
        letzter_zeitpunkt = eintraege[-1]["zeitpunkt"]

    return {
        "datum": heute_text(),
        "summe_ml": summe,
        "letzter_eintrag": letzter_zeitpunkt,
        "eintraege": eintraege,
    }


def loeschen(eintrag_id):
    verb = verbindung()
    zeiger = verb.execute("DELETE FROM wasser_log WHERE id = ?", (eintrag_id,))
    geloescht = zeiger.rowcount
    verb.commit()
    verb.close()
    return geloescht > 0
