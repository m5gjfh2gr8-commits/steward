"""
News fürs Morning Briefing

Quellen: die RSS-Feeds aus config/feeds.json plus der Newsletter, der ohnehin
per Mail reinkommt. Gefiltert wird gegen das Interessensprofil und gegen das
bisherige Daumen-hoch/runter-Feedback - alles in genau einem Modellaufruf pro Tag
"""

import hashlib
import feedparser

from app.config import feeds_laden
from app.datenbank import verbindung, zeilen_zu_dicts
from app.llm.auswahl import modell
from app.zeit import jetzt, jetzt_text

SYSTEM_FILTERN = """Du wählst aus einer Liste von Schlagzeilen die wenigen aus, die eine bestimmte Person wirklich interessieren.
Antworte ausschliesslich mit JSON, ohne Erklärung:
{"meldungen": [{"nummer": 1, "titel": "kurzer eigener Titel", "zusammenfassung": "ein bis zwei Sätze"}]}

Regeln:
- höchstens 6 Meldungen, lieber weniger als zu viele
- nur was zu den Interessen passt, im Zweifel weglassen
- die Zusammenfassung ist ein bis zwei ganze Sätze auf Deutsch, kein Stichwortsalat
- keine Meldung doppelt, thematisch gleiche Meldungen zusammenfassen
- "nummer" ist die Nummer der Eingabe-Schlagzeile, auf die sich die Meldung hauptsächlich stuetzt"""

STANDARD_INTERESSEN = [
    "Künstliche Intelligenz",
    "Halbleiter und Chipindustrie",
    "Wirtschaft und Märkte",
    "Unternehmensführung und Startups",
    "Technik und Elektronik",
    "Oesterreich",
]


def meldung_hash(titel):
    return hashlib.sha1(titel.strip().lower().encode("utf-8")).hexdigest()[:16]


def interessen_holen(nur_aktive=True):
    verb = verbindung()
    if nur_aktive:
        zeilen = verb.execute("SELECT * FROM interessen WHERE aktiv = 1 ORDER BY id ASC").fetchall()
    else:
        zeilen = verb.execute("SELECT * FROM interessen ORDER BY id ASC").fetchall()
    verb.close()
    return zeilen_zu_dicts(zeilen)


def standard_interessen_anlegen():
    """Legt die Startliste an, falls noch gar keine Interessen gespeichert sind"""
    vorhandene = interessen_holen(nur_aktive=False)
    if len(vorhandene) > 0:
        return vorhandene

    verb = verbindung()
    for stichwort in STANDARD_INTERESSEN:
        verb.execute("INSERT OR IGNORE INTO interessen (stichwort, aktiv) VALUES (?, 1)", (stichwort,))
    verb.commit()
    verb.close()
    return interessen_holen(nur_aktive=False)


def interessen_setzen(stichwoerter):
    """Ersetzt die komplette Liste durch die übergebene"""
    verb = verbindung()
    verb.execute("DELETE FROM interessen")
    for stichwort in stichwoerter:
        sauber = stichwort.strip()
        if sauber != "":
            verb.execute("INSERT OR IGNORE INTO interessen (stichwort, aktiv) VALUES (?, 1)", (sauber,))
    verb.commit()
    verb.close()
    return interessen_holen(nur_aktive=False)


def feedback_speichern(titel, bewertung):
    verb = verbindung()
    verb.execute(
        "INSERT INTO news_feedback (meldung_hash, titel, zeitpunkt, bewertung) VALUES (?, ?, ?, ?)",
        (meldung_hash(titel), titel, jetzt_text(), bewertung),
    )
    verb.commit()
    verb.close()


def feedback_zusammenfassen(anzahl=15):
    """
    Ausgabe: (Liste zuletzt positiv bewerteter Titel, Liste zuletzt negativ bewerteter Titel)
    Geht nur in den Prompt, damit das Modell die Richtung mitbekommt
    """
    verb = verbindung()
    zeilen = verb.execute(
        "SELECT titel, bewertung FROM news_feedback ORDER BY id DESC LIMIT ?",
        (anzahl * 2,),
    ).fetchall()
    verb.close()

    gut = []
    schlecht = []
    for zeile in zeilen:
        if zeile["bewertung"] == "up" and len(gut) < anzahl:
            gut.append(zeile["titel"])
        elif zeile["bewertung"] == "down" and len(schlecht) < anzahl:
            schlecht.append(zeile["titel"])

    return gut, schlecht


def feed_einlesen(feed):
    """
    Eingabe: {"name":..., "url":...}
    Ausgabe: Liste von {"quelle", "titel", "beschreibung", "link"}
    """
    gefunden = []

    try:
        geparst = feedparser.parse(feed["url"])
    except Exception:
        return gefunden

    for eintrag in geparst.entries[:20]:
        titel = getattr(eintrag, "title", "")
        if titel.strip() == "":
            continue

        beschreibung = getattr(eintrag, "summary", "")
        link = getattr(eintrag, "link", "")

        gefunden.append({
            "quelle": feed["name"],
            "titel": titel.strip(),
            "beschreibung": beschreibung.strip()[:300],
            "link": link,
        })

    return gefunden


def alle_feeds_einlesen():
    alle = []
    for feed in feeds_laden():
        alle.extend(feed_einlesen(feed))
    return alle


def schon_bewertet_filtern(schlagzeilen):
    """Meldungen die schon mal einen Daumen runter bekommen haben fliegen gleich raus"""
    verb = verbindung()
    zeilen = verb.execute("SELECT meldung_hash FROM news_feedback WHERE bewertung = 'down'").fetchall()
    verb.close()

    schlechte = set()
    for zeile in zeilen:
        schlechte.add(zeile["meldung_hash"])

    uebrig = []
    for schlagzeile in schlagzeilen:
        if meldung_hash(schlagzeile["titel"]) not in schlechte:
            uebrig.append(schlagzeile)

    return uebrig


def prompt_bauen(schlagzeilen, newsletter_text):
    interessen = interessen_holen()

    stichwoerter = []
    for eintrag in interessen:
        stichwoerter.append(eintrag["stichwort"])

    gut, schlecht = feedback_zusammenfassen()

    text = "Interessen: " + ", ".join(stichwoerter) + "\n\n"

    if len(gut) > 0:
        text = text + "Hat früher gefallen: " + " | ".join(gut) + "\n"
    if len(schlecht) > 0:
        text = text + "Hat früher NICHT gefallen: " + " | ".join(schlecht) + "\n"

    text = text + "\nSchlagzeilen von heute:\n"

    nummer = 1
    for schlagzeile in schlagzeilen:
        text = text + str(nummer) + ". [" + schlagzeile["quelle"] + "] " + schlagzeile["titel"]
        if schlagzeile["beschreibung"] != "":
            text = text + " - " + schlagzeile["beschreibung"][:150]
        text = text + "\n"
        nummer = nummer + 1

    if newsletter_text.strip() != "":
        text = text + "\nAusserdem der heutige Newsletter im Volltext:\n" + newsletter_text[:4000]

    return text


def meldungen_holen(newsletter_text=""):
    """
    Kompletter News-Teil: Feeds einlesen, vorfiltern, ein Modellaufruf
    Ausgabe: Liste von {"titel", "zusammenfassung", "quelle", "link"}
    """
    standard_interessen_anlegen()

    schlagzeilen = alle_feeds_einlesen()
    schlagzeilen = schon_bewertet_filtern(schlagzeilen)

    if len(schlagzeilen) == 0 and newsletter_text.strip() == "":
        return []

    # nicht alles ins Modell kippen, sonst wird der Prompt unnötig teuer
    if len(schlagzeilen) > 60:
        schlagzeilen = schlagzeilen[:60]

    eingabe = prompt_bauen(schlagzeilen, newsletter_text)
    ergebnis = modell().json_erzeugen(SYSTEM_FILTERN, eingabe, max_tokens=1200)

    fertig = []
    for meldung in ergebnis.get("meldungen", []):
        nummer = int(meldung.get("nummer", 0))

        quelle = "Newsletter"
        link = ""
        if 1 <= nummer <= len(schlagzeilen):
            quelle = schlagzeilen[nummer - 1]["quelle"]
            link = schlagzeilen[nummer - 1]["link"]

        fertig.append({
            "titel": meldung.get("titel", ""),
            "zusammenfassung": meldung.get("zusammenfassung", ""),
            "quelle": quelle,
            "link": link,
        })

    return fertig


def vertiefen(titel, zusammenfassung):
    """Wenn Lorenz im Chat zu einer Meldung nachfragt - läuft bewusst am größeren Modell"""
    system = "Du erklärst eine Nachrichtenmeldung ausführlicher, sachlich und auf Deutsch. "
    system = system + "Wenn du etwas nicht sicher weisst, sag das dazu statt zu raten. Höchstens 200 Wörter."
    eingabe = "Meldung: " + titel + "\n" + zusammenfassung

    heute = jetzt().date().isoformat()
    eingabe = eingabe + "\n(Heutiges Datum: " + heute + ")"

    return modell().text_erzeugen(system, eingabe, max_tokens=600, gross=True)
