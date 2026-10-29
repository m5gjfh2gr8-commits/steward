"""
Mail-Triage über mehrere Postfächer

Bewusst nur 1x täglich: das Ergebnis landet in mail_zwischenspeicher und wird bis zum
nächsten Tag wiederverwendet, damit nicht bei jedem App-Start ein Modellaufruf fällig wird
Die Mails selbst werden nicht gespeichert, nur Absender/Betreff und die Bewertung

Gelesen wird mit BODY.PEEK, die Mails bleiben im Postfach also ungelesen
"""

import email
import imaplib
import json
from email.header import decode_header

from app.config import EINSTELLUNGEN, postfaecher_laden
from app.datenbank import verbindung
from app.llm.auswahl import modell
from app.zeit import heute_text, jetzt, jetzt_text

SYSTEM_BEWERTEN = """Du sortierst E-Mails für einen HTL-Schüler, der ein Startup mitführt.
Antworte ausschliesslich mit JSON, ohne Erklärung:
{"bewertungen": [{"nummer": 1, "stufe": "wichtig", "grund": "kurzer Halbsatz"}]}

"stufe" ist genau einer dieser Werte:
- "wichtig": verlangt eine Reaktion oder hat eine Frist (Schule, Behörde, Rechnung, Startup, echte Person)
- "interessant": lesenswert aber ohne Handlungsbedarf (Newsletter zu seinen Themen, Projekt-Updates)
- "egal": Werbung, Massenmail, automatische Benachrichtigung ohne Inhalt

Gib für jede Mail genau eine Bewertung zurück, die Nummer muss zur Eingabe passen."""


def kopfzeile_dekodieren(rohwert):
    """IMAP liefert Betreff/Absender oft base64- oder quoted-printable-kodiert"""
    if rohwert is None:
        return ""

    ergebnis = ""
    for teil, kodierung in decode_header(rohwert):
        if isinstance(teil, bytes):
            if kodierung is None:
                kodierung = "utf-8"
            try:
                ergebnis = ergebnis + teil.decode(kodierung, errors="replace")
            except LookupError:
                ergebnis = ergebnis + teil.decode("utf-8", errors="replace")
        else:
            ergebnis = ergebnis + teil

    return ergebnis.strip()


def textanfang_holen(nachricht, zeichen=400):
    """Nimmt den Anfang des Klartext-Teils, HTML-Mails werden übersprungen"""
    if not nachricht.is_multipart():
        inhalt = nachricht.get_payload(decode=True)
        if inhalt is None:
            return ""
        return inhalt.decode("utf-8", errors="replace")[:zeichen]

    for teil in nachricht.walk():
        if teil.get_content_type() == "text/plain":
            inhalt = teil.get_payload(decode=True)
            if inhalt is not None:
                return inhalt.decode("utf-8", errors="replace")[:zeichen]

    return ""


def imap_datum_seit(tage=2):
    """IMAP will das Datum im Format 01-Jan-2026"""
    from datetime import timedelta
    tag = jetzt() - timedelta(days=tage)
    return tag.strftime("%d-%b-%Y")


def postfach_abfragen(postfach, tage=2):
    """
    Eingabe: Postfach-Dict aus config/postfächer.json
    Ausgabe: Liste von {"postfach", "absender", "betreff", "datum", "anfang"}
    """
    gefundene = []

    server = imaplib.IMAP4_SSL(postfach["server"], postfach.get("port", 993))
    try:
        server.login(postfach["benutzer"], postfach["passwort"])
        server.select(postfach.get("ordner", "INBOX"), readonly=True)

        status, antwort = server.search(None, "(UNSEEN SINCE " + imap_datum_seit(tage) + ")")
        if status != "OK":
            return gefundene

        nummern = antwort[0].split()

        # bei sehr vollen Postfächern nicht alles durchgehen, sonst wird der Prompt riesig
        if len(nummern) > 25:
            nummern = nummern[-25:]

        for nummer in nummern:
            status, rohdaten = server.fetch(nummer, "(BODY.PEEK[])")
            if status != "OK":
                continue
            if rohdaten[0] is None:
                continue

            nachricht = email.message_from_bytes(rohdaten[0][1])
            gefundene.append({
                "postfach": postfach["name"],
                "absender": kopfzeile_dekodieren(nachricht.get("From")),
                "betreff": kopfzeile_dekodieren(nachricht.get("Subject")),
                "datum": kopfzeile_dekodieren(nachricht.get("Date")),
                "anfang": textanfang_holen(nachricht),
            })
    finally:
        try:
            server.logout()
        except Exception:
            pass

    return gefundene


def alle_postfaecher_abfragen(tage=2):
    """Ausgabe: (Liste aller Mails, Liste von Fehlermeldungen pro Postfach)"""
    alle = []
    fehler = []

    for postfach in postfaecher_laden():
        try:
            alle.extend(postfach_abfragen(postfach, tage))
        except Exception as problem:
            fehler.append(postfach.get("name", "unbekannt") + ": " + str(problem))

    return alle, fehler


def mails_bewerten(mails):
    """
    Ein einziger Modellaufruf für alle Mails zusammen
    Ausgabe: gleiche Liste, jeder Eintrag zusätzlich mit "stufe" und "grund"
    """
    if len(mails) == 0:
        return []

    zeilen = []
    nummer = 1
    for mail in mails:
        block = "Nummer " + str(nummer) + "\n"
        block = block + "Postfach: " + mail["postfach"] + "\n"
        block = block + "Von: " + mail["absender"] + "\n"
        block = block + "Betreff: " + mail["betreff"] + "\n"
        block = block + "Anfang: " + mail["anfang"].replace("\n", " ")[:250]
        zeilen.append(block)
        nummer = nummer + 1

    eingabe = "\n\n".join(zeilen)
    ergebnis = modell().json_erzeugen(SYSTEM_BEWERTEN, eingabe, max_tokens=1500)

    bewertungen = ergebnis.get("bewertungen", [])

    # Bewertungen nach Nummer zuordnen, fehlende Nummern werden zu "egal"
    nach_nummer = {}
    for bewertung in bewertungen:
        nach_nummer[int(bewertung.get("nummer", 0))] = bewertung

    fertig = []
    nummer = 1
    for mail in mails:
        kopie = dict(mail)
        kopie.pop("anfang", None)

        if nummer in nach_nummer:
            kopie["stufe"] = nach_nummer[nummer].get("stufe", "egal")
            kopie["grund"] = nach_nummer[nummer].get("grund", "")
        else:
            kopie["stufe"] = "egal"
            kopie["grund"] = ""

        fertig.append(kopie)
        nummer = nummer + 1

    return fertig


def zwischenspeicher_lesen(datum_text):
    verb = verbindung()
    zeile = verb.execute("SELECT * FROM mail_zwischenspeicher WHERE datum = ?", (datum_text,)).fetchone()
    verb.close()
    if zeile is None:
        return None
    return json.loads(zeile["inhalt_json"])


def zwischenspeicher_schreiben(datum_text, inhalt):
    verb = verbindung()
    verb.execute(
        "INSERT OR REPLACE INTO mail_zwischenspeicher (datum, inhalt_json, erstellt_am) VALUES (?, ?, ?)",
        (datum_text, json.dumps(inhalt, ensure_ascii=False), jetzt_text()),
    )
    verb.commit()
    verb.close()


def wichtige_mails(neu_laden=False):
    """
    Ausgabe: {"datum":..., "mails": [...], "anzahl_wichtig":..., "anzahl_interessant":..., "fehler": [...]}
    Ohne neu_laden wird der Stand von heute wiederverwendet
    """
    datum = heute_text()

    if not neu_laden:
        gespeichert = zwischenspeicher_lesen(datum)
        if gespeichert is not None:
            return gespeichert

    rohe_mails, fehler = alle_postfaecher_abfragen()
    bewertet = mails_bewerten(rohe_mails)

    relevante = []
    anzahl_wichtig = 0
    anzahl_interessant = 0

    for mail in bewertet:
        if mail["stufe"] == "wichtig":
            anzahl_wichtig = anzahl_wichtig + 1
            relevante.append(mail)
        elif mail["stufe"] == "interessant":
            anzahl_interessant = anzahl_interessant + 1
            relevante.append(mail)

    ergebnis = {
        "datum": datum,
        "abgefragt_am": jetzt_text(),
        "mails": relevante,
        "anzahl_wichtig": anzahl_wichtig,
        "anzahl_interessant": anzahl_interessant,
        "anzahl_gesamt_geprueft": len(bewertet),
        "fehler": fehler,
    }

    zwischenspeicher_schreiben(datum, ergebnis)
    return ergebnis


def newsletter_text_holen():
    """
    Sucht im ersten konfigurierten Postfach die heutige Newsletter-Mail
    Ausgabe: Klartext des Newsletters oder leerer String
    """
    if EINSTELLUNGEN.newsletter_absender == "":
        return ""

    postfaecher = postfaecher_laden()
    if len(postfaecher) == 0:
        return ""

    for postfach in postfaecher:
        try:
            server = imaplib.IMAP4_SSL(postfach["server"], postfach.get("port", 993))
            server.login(postfach["benutzer"], postfach["passwort"])
            server.select(postfach.get("ordner", "INBOX"), readonly=True)

            suche = '(FROM "' + EINSTELLUNGEN.newsletter_absender + '" SINCE ' + imap_datum_seit(1) + ')'
            status, antwort = server.search(None, suche)

            if status == "OK" and len(antwort[0].split()) > 0:
                letzte = antwort[0].split()[-1]
                status, rohdaten = server.fetch(letzte, "(BODY.PEEK[])")
                server.logout()

                if status == "OK" and rohdaten[0] is not None:
                    nachricht = email.message_from_bytes(rohdaten[0][1])
                    return textanfang_holen(nachricht, zeichen=6000)

            server.logout()
        except Exception:
            continue

    return ""
