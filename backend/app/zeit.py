"""
Zeit-Helfer

Alles was gespeichert wird ist ISO-Text in lokaler Zeit (Europe/Vienna), damit
"heute" in der Datenbank auch wirklich der Tag ist, den Lorenz meint
"""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config import EINSTELLUNGEN


def zone():
    return ZoneInfo(EINSTELLUNGEN.zeitzone)


def jetzt():
    return datetime.now(zone())


def jetzt_text():
    return jetzt().isoformat(timespec="seconds")


def heute_text():
    return jetzt().date().isoformat()


def tag_vor_x_tagen_text(tage):
    tag = jetzt().date() - timedelta(days=tage)
    return tag.isoformat()


def datum_aus_text(text):
    """
    Eingabe: ISO-Text, mit oder ohne Zeitzone
    Ausgabe: datetime mit Zeitzone, None wenn der Text nicht lesbar ist
    """
    if text is None:
        return None
    if text.strip() == "":
        return None

    sauber = text.strip().replace("Z", "+00:00")
    try:
        wert = datetime.fromisoformat(sauber)
    except ValueError:
        return None

    if wert.tzinfo is None:
        return wert.replace(tzinfo=zone())
    return wert


def stunden_seit(zeitpunkt_text):
    """
    Eingabe: ISO-Text
    Ausgabe: Stunden seit damals als Zahl, None wenn der Text nicht lesbar ist
    """
    wert = datum_aus_text(zeitpunkt_text)
    if wert is None:
        return None

    unterschied = jetzt() - wert
    return unterschied.total_seconds() / 3600.0


def wochentag_deutsch(zeitpunkt):
    namen = ["Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag"]
    return namen[zeitpunkt.weekday()]
