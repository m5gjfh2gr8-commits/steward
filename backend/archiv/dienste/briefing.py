"""
Morning Briefing

Setzt sich aus drei Teilen zusammen, die bewusst getrennt bleiben:
Termine, offene Todos, und die gefilterten News
Wird einmal pro Tag gebaut und danach aus briefing_zwischenspeicher geliefert
"""

import json

from app.datenbank import verbindung
from app.dienste import kalender, mail, nachrichten, todos
from app.zeit import heute_text, jetzt, jetzt_text


def zwischenspeicher_lesen(datum_text):
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM briefing_zwischenspeicher WHERE datum = ?", (datum_text,)).fetchone()
    verb.close()
    if zeile is None:
        return None
    return json.loads(zeile["inhalt_json"])


def zwischenspeicher_schreiben(datum_text, inhalt):
    verb = verbindung()
    verb.execute(
        "INSERT OR REPLACE INTO briefing_zwischenspeicher (datum, inhalt_json, erstellt_am) VALUES (?, ?, ?)",
        (datum_text, json.dumps(inhalt, ensure_ascii=False), jetzt_text()),
    )
    verb.commit()
    verb.close()


def heutige_todos():
    """Offene Todos, die heute oder früher fällig sind, plus alle ohne Datum"""
    alle = todos.liste_holen(nur_offen=True)
    heute = heute_text()

    relevante = []
    for eintrag in alle:
        faellig = eintrag["faellig_am"]
        if faellig is None or faellig == "":
            relevante.append(eintrag)
        elif faellig[:10] <= heute:
            relevante.append(eintrag)

    return relevante


def bauen(neu_laden=False):
    """
    Ausgabe: {"datum", "begruessung", "termine", "todos", "news", "hinweise"}
    Ohne neu_laden wird das Briefing von heute wiederverwendet
    """
    datum = heute_text()

    if not neu_laden:
        gespeichert = zwischenspeicher_lesen(datum)
        if gespeichert is not None:
            return gespeichert

    hinweise = []

    termine, kalender_fehler = kalender.termine_holen(tage=1)
    if kalender_fehler != "":
        hinweise.append(kalender_fehler)

    offene_todos = heutige_todos()

    try:
        newsletter = mail.newsletter_text_holen()
    except Exception as fehler:
        newsletter = ""
        hinweise.append("Newsletter nicht gelesen: " + str(fehler))

    try:
        meldungen = nachrichten.meldungen_holen(newsletter)
    except Exception as fehler:
        meldungen = []
        hinweise.append("News nicht geladen: " + str(fehler))

    ergebnis = {
        "datum": datum,
        "begruessung": begruessung_bauen(),
        "termine": termine,
        "todos": offene_todos,
        "news": meldungen,
        "hinweise": hinweise,
        "erstellt_am": jetzt_text(),
    }

    zwischenspeicher_schreiben(datum, ergebnis)
    return ergebnis


def begruessung_bauen():
    stunde = jetzt().hour
    if stunde < 11:
        return "Guten Morgen"
    if stunde < 18:
        return "Servus"
    return "Guten Abend"


def als_text(briefing):
    """Für die Vorlese-Funktion in der App - alles in einem Fliesstext"""
    zeilen = [briefing["begruessung"] + ", hier ist dein Briefing."]

    if len(briefing["termine"]) == 0:
        zeilen.append("Heute stehen keine Termine im Kalender.")
    else:
        zeilen.append("Termine heute:")
        for termin in briefing["termine"]:
            uhrzeit = termin["beginn"][11:16]
            if termin["ganztaegig"] or uhrzeit == "":
                zeilen.append(termin["titel"] + ", ganztaegig.")
            else:
                zeilen.append(uhrzeit + " Uhr, " + termin["titel"] + ".")

    if len(briefing["todos"]) > 0:
        zeilen.append("Offen: " + str(len(briefing["todos"])) + " Aufgaben.")
        for eintrag in briefing["todos"][:5]:
            zeilen.append(eintrag["inhalt"] + ".")

    if len(briefing["news"]) > 0:
        zeilen.append("Und die Nachrichten:")
        for meldung in briefing["news"]:
            zeilen.append(meldung["titel"] + ". " + meldung["zusammenfassung"])

    return " ".join(zeilen)
