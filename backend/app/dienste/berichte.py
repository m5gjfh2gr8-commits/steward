"""
Berichte und Modul-Läufe

Hier liegt alles, was Steward über seine Module weiß. Die Module selbst greifen
nicht auf diese Tabellen zu - sie geben nur einen Bericht zurück, gespeichert wird
er vom Planer
"""

import json

from app.bots import verzeichnis
from app.datenbank import verbindung, zeilen_zu_dicts
from app.zeit import jetzt_text


def bericht_speichern(modul_name, bericht):
    """
    Eingabe: Modulname, ein Bericht-Objekt aus app.bots.basis
    Ausgabe: die gespeicherte Zeile als dict
    """
    verb = verbindung()
    zeiger = verb.execute(
        """INSERT INTO berichte (modul, zeitpunkt, titel, kurzfassung, kennzahlen_json, eintraege_json)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (
            modul_name,
            jetzt_text(),
            bericht.titel,
            bericht.kurzfassung,
            json.dumps(bericht.kennzahlen, ensure_ascii=False),
            json.dumps(bericht.eintraege, ensure_ascii=False),
        ),
    )
    neue_id = zeiger.lastrowid
    verb.commit()
    verb.close()
    return bericht_holen(neue_id)


def zeile_zu_bericht(zeile):
    """Macht aus der Datenbankzeile die Form, die App und PC-Seite erwarten"""
    fertig = dict(zeile)
    fertig["kennzahlen"] = json.loads(fertig.pop("kennzahlen_json"))
    fertig["eintraege"] = json.loads(fertig.pop("eintraege_json"))
    return fertig


def bericht_holen(bericht_id):
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM berichte WHERE id = ?", (bericht_id,)).fetchone()
    verb.close()
    if zeile is None:
        return None
    return zeile_zu_bericht(zeile)


def berichte_von_modul(modul_name, anzahl=20):
    verb = verbindung()
    zeilen = verb.execute(
        "SELECT * FROM berichte WHERE modul = ? ORDER BY zeitpunkt DESC, id DESC LIMIT ?",
        (modul_name, anzahl),
    ).fetchall()
    verb.close()

    ergebnis = []
    for zeile in zeilen:
        ergebnis.append(zeile_zu_bericht(zeile))
    return ergebnis


def letzter_bericht(modul_name):
    gefunden = berichte_von_modul(modul_name, anzahl=1)
    if len(gefunden) == 0:
        return None
    return gefunden[0]


# --- Läufe ---

def lauf_beginnen(modul_name):
    verb = verbindung()
    zeiger = verb.execute(
        "INSERT INTO modul_laeufe (modul, start, status) VALUES (?, ?, 'laeuft')",
        (modul_name, jetzt_text()),
    )
    neue_id = zeiger.lastrowid
    verb.commit()
    verb.close()
    return neue_id


def lauf_abschliessen(lauf_id, status, meldung="", tokens_ein=0, tokens_aus=0):
    verb = verbindung()
    verb.execute(
        """UPDATE modul_laeufe
           SET ende = ?, status = ?, meldung = ?, tokens_ein = ?, tokens_aus = ?
           WHERE id = ?""",
        (jetzt_text(), status, meldung[:1000], tokens_ein, tokens_aus, lauf_id),
    )
    verb.commit()
    verb.close()


def laeufe_von_modul(modul_name, anzahl=20):
    verb = verbindung()
    zeilen = verb.execute(
        "SELECT * FROM modul_laeufe WHERE modul = ? ORDER BY start DESC, id DESC LIMIT ?",
        (modul_name, anzahl),
    ).fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def haengende_laeufe_aufraeumen():
    """
    Wird beim Start aufgerufen: Läufe, die noch auf "laeuft" stehen, können nur von
    einem abgewürgten Prozess stammen (Stromausfall, Neustart mitten im Lauf)
    """
    verb = verbindung()
    zeiger = verb.execute(
        "UPDATE modul_laeufe SET status = 'abgebrochen', ende = ?, meldung = ? WHERE status = 'laeuft'",
        (jetzt_text(), "Server wurde während des Laufs beendet"),
    )
    anzahl = zeiger.rowcount
    verb.commit()
    verb.close()
    return anzahl


def fehler_in_folge(modul_name):
    """Wie viele Läufe seit dem letzten Erfolg schiefgegangen sind"""
    letzte = laeufe_von_modul(modul_name, anzahl=10)

    gezaehlt = 0
    for lauf in letzte:
        if lauf["status"] == "ok":
            return gezaehlt
        if lauf["status"] == "laeuft":
            continue
        gezaehlt = gezaehlt + 1

    return gezaehlt


def letzter_erfolg(modul_name):
    verb = verbindung()
    zeile = verb.execute(
        "SELECT ende FROM modul_laeufe WHERE modul = ? AND status = 'ok' ORDER BY start DESC LIMIT 1",
        (modul_name,),
    ).fetchone()
    verb.close()

    if zeile is None:
        return None
    return zeile["ende"]


# --- Gelesen-Markierung ---

def gelesen_setzen(modul_name, zeitpunkt=None):
    if zeitpunkt is None:
        zeitpunkt = jetzt_text()

    verb = verbindung()
    verb.execute(
        "INSERT OR REPLACE INTO gelesen_bis (modul, zeitpunkt) VALUES (?, ?)",
        (modul_name, zeitpunkt),
    )
    verb.commit()
    verb.close()
    return zeitpunkt


def gelesen_holen(modul_name):
    verb = verbindung()
    zeile = verb.execute("SELECT zeitpunkt FROM gelesen_bis WHERE modul = ?", (modul_name,)).fetchone()
    verb.close()

    if zeile is None:
        return None
    return zeile["zeitpunkt"]


def anzahl_ungelesen(modul_name):
    grenze = gelesen_holen(modul_name)

    verb = verbindung()
    if grenze is None:
        zeile = verb.execute(
            "SELECT COUNT(*) AS anzahl FROM berichte WHERE modul = ?",
            (modul_name,),
        ).fetchone()
    else:
        zeile = verb.execute(
            "SELECT COUNT(*) AS anzahl FROM berichte WHERE modul = ? AND zeitpunkt > ?",
            (modul_name, grenze),
        ).fetchone()
    verb.close()

    return zeile["anzahl"]


# --- Zustand, das ist die Überwachung ---

def zustand_von_modul(modul):
    """
    Eingabe: ein Modul-Objekt aus dem Verzeichnis
    Ausgabe: alles, was App und Systemcheck über das Modul wissen müssen
    """
    laeufe = laeufe_von_modul(modul.name, anzahl=1)

    letzter_lauf = None
    if len(laeufe) > 0:
        letzter_lauf = laeufe[0]

    erfolg = letzter_erfolg(modul.name)
    fehler = fehler_in_folge(modul.name)

    if erfolg is None and fehler == 0:
        zustand = "neu"
    elif fehler >= 3:
        zustand = "kaputt"
    elif fehler > 0:
        zustand = "wackelig"
    else:
        zustand = "ok"

    return {
        "name": modul.name,
        "anzeigename": modul.anzeigename,
        "beschreibung": modul.beschreibung,
        "zeitplan": modul.zeitplan,
        "braucht_modell": modul.braucht_modell,
        "zustand": zustand,
        "letzter_lauf": letzter_lauf,
        "letzter_erfolg": erfolg,
        "fehler_in_folge": fehler,
        "ungelesen": anzahl_ungelesen(modul.name),
        "letzter_bericht": letzter_bericht(modul.name),
    }


def zustand_aller_module():
    gesammelt = []
    for modul in verzeichnis.alle():
        gesammelt.append(zustand_von_modul(modul))
    return gesammelt
