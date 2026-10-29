"""
Tagesziele für Kalorien, Makros und Wasser

Immer genau eine Zeile in der Tabelle (id = 1)
"""

from app.datenbank import verbindung


def holen():
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM tagesziele WHERE id = 1").fetchone()
    verb.close()
    if zeile is None:
        return None
    return dict(zeile)


def setzen(kcal_ziel=None, eiweiss_ziel_g=None, kohlenhydrate_ziel_g=None, fett_ziel_g=None, wasser_ziel_ml=None):
    aktuell = holen()

    if kcal_ziel is None:
        kcal_ziel = aktuell["kcal_ziel"]
    if eiweiss_ziel_g is None:
        eiweiss_ziel_g = aktuell["eiweiss_ziel_g"]
    if kohlenhydrate_ziel_g is None:
        kohlenhydrate_ziel_g = aktuell["kohlenhydrate_ziel_g"]
    if fett_ziel_g is None:
        fett_ziel_g = aktuell["fett_ziel_g"]
    if wasser_ziel_ml is None:
        wasser_ziel_ml = aktuell["wasser_ziel_ml"]

    verb = verbindung()
    verb.execute(
        """UPDATE tagesziele
           SET kcal_ziel = ?, eiweiss_ziel_g = ?, kohlenhydrate_ziel_g = ?, fett_ziel_g = ?, wasser_ziel_ml = ?
           WHERE id = 1""",
        (kcal_ziel, eiweiss_ziel_g, kohlenhydrate_ziel_g, fett_ziel_g, int(wasser_ziel_ml)),
    )
    verb.commit()
    verb.close()
    return holen()
