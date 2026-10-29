"""
Todos und Termine

Speichern/Lesen ist reine Datenbankarbeit, nur das Zerlegen von Freitext
("morgen um 3 Zahnarzt") braucht das Modell
"""

from app.datenbank import verbindung, zeilen_zu_dicts
from app.llm.auswahl import modell
from app.zeit import jetzt, jetzt_text, wochentag_deutsch

SYSTEM_ANWEISUNG = """Du zerlegst deutschsprachigen Freitext in genau ein Todo oder einen Termin.
Antworte ausschliesslich mit JSON, ohne Erklärung, in genau dieser Form:
{"inhalt": "kurzer Text", "faellig_am": "YYYY-MM-DDTHH:MM:SS oder null", "ist_termin": true/false}

Regeln:
- "inhalt" ist eine knappe Aufgabenbeschreibung ohne die Zeitangabe
- "faellig_am" ist lokale Zeit ohne Zeitzone, relative Angaben wie "morgen" oder "nächsten Montag" rechnest du aus
- wenn keine Uhrzeit genannt wird, nimm 09:00
- wenn gar kein Datum erkennbar ist, setze faellig_am auf null
- "ist_termin" ist true wenn eine konkrete Uhrzeit/ein Treffen gemeint ist, false bei einer reinen Aufgabe"""


def freitext_zerlegen(text):
    """
    Eingabe: Freitext oder Diktat aus der App
    Ausgabe: {"inhalt": ..., "faellig_am": ... oder None, "ist_termin": bool}
    """
    heute = jetzt()
    kontext = "Aktuelles Datum und Uhrzeit: " + heute.strftime("%Y-%m-%d %H:%M") + " (" + wochentag_deutsch(heute) + ")\n"
    kontext = kontext + "Eingabe: " + text

    ergebnis = modell().json_erzeugen(SYSTEM_ANWEISUNG, kontext, max_tokens=300)

    inhalt = ergebnis.get("inhalt", text)
    faellig = ergebnis.get("faellig_am")
    if faellig == "null":
        faellig = None

    ist_termin = ergebnis.get("ist_termin", False)

    return {"inhalt": inhalt, "faellig_am": faellig, "ist_termin": bool(ist_termin)}


def anlegen(inhalt, faellig_am=None, quelle="text"):
    verb = verbindung()
    zeiger = verb.execute(
        "INSERT INTO todos (inhalt, faellig_am, erledigt, quelle, erstellt_am) VALUES (?, ?, 0, ?, ?)",
        (inhalt, faellig_am, quelle, jetzt_text()),
    )
    neue_id = zeiger.lastrowid
    verb.commit()
    verb.close()
    return einzeln_holen(neue_id)


def einzeln_holen(todo_id):
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM todos WHERE id = ?", (todo_id,)).fetchone()
    verb.close()
    if zeile is None:
        return None
    return dict(zeile)


def liste_holen(nur_offen=True):
    verb = verbindung()
    if nur_offen:
        zeilen = verb.execute(
            "SELECT * FROM todos WHERE erledigt = 0 ORDER BY faellig_am IS NULL, faellig_am ASC, id ASC"
        ).fetchall()
    else:
        zeilen = verb.execute(
            "SELECT * FROM todos ORDER BY erledigt ASC, faellig_am IS NULL, faellig_am ASC, id ASC"
        ).fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def aendern(todo_id, inhalt=None, faellig_am=None, erledigt=None):
    vorhanden = einzeln_holen(todo_id)
    if vorhanden is None:
        return None

    if inhalt is None:
        inhalt = vorhanden["inhalt"]
    if faellig_am is None:
        faellig_am = vorhanden["faellig_am"]
    if erledigt is None:
        erledigt = vorhanden["erledigt"]

    verb = verbindung()
    verb.execute(
        "UPDATE todos SET inhalt = ?, faellig_am = ?, erledigt = ? WHERE id = ?",
        (inhalt, faellig_am, int(erledigt), todo_id),
    )
    verb.commit()
    verb.close()
    return einzeln_holen(todo_id)


def loeschen(todo_id):
    verb = verbindung()
    zeiger = verb.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    geloescht = zeiger.rowcount
    verb.commit()
    verb.close()
    return geloescht > 0
