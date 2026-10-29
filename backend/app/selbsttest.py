"""
Selbsttest vor dem ersten echten Start

Prüft der Reihe nach alles, was beim Aufsetzen schiefgehen kann, und sagt bei jedem
Punkt OK oder was fehlt. Gedacht als erster Befehl nach der Installation am Server,
bevor der Dienst eingeschaltet wird

Aufruf:  python -m app.selbsttest
         python -m app.selbsttest --modell     (macht zusätzlich einen echten Modellaufruf)

Rückgabewert: 0 wenn alles passt, 1 wenn mindestens ein Punkt fehlgeschlagen ist
"""

import os
import sys

ergebnisse = []


def pruefen(name, funktion):
    """Führt eine Prüfung aus und merkt sich das Ergebnis"""
    try:
        meldung = funktion()
        ergebnisse.append((True, name, meldung))
    except Exception as fehler:
        ergebnisse.append((False, name, str(fehler)))


def python_version():
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10 oder neuer nötig, hier läuft " + sys.version.split()[0])
    return "Python " + sys.version.split()[0]


def api_key():
    from app.config import EINSTELLUNGEN

    if EINSTELLUNGEN.api_key == "":
        raise RuntimeError("STEWARD_API_KEY ist nicht gesetzt")
    if len(EINSTELLUNGEN.api_key) < 20:
        raise RuntimeError("STEWARD_API_KEY ist sehr kurz, lieber neu erzeugen: openssl rand -hex 32")

    return str(len(EINSTELLUNGEN.api_key)) + " Zeichen"


def zeitzone():
    from app.zeit import jetzt
    return jetzt().strftime("%Y-%m-%d %H:%M %Z")


def datenbank_schreibbar():
    from app import datenbank
    from app.config import EINSTELLUNGEN

    datenbank.vorbereiten()

    verb = datenbank.verbindung()
    modus = verb.execute("PRAGMA journal_mode").fetchone()[0]
    verb.close()

    if modus.lower() != "wal":
        raise RuntimeError("WAL liess sich nicht einschalten, Modus ist " + modus)

    return os.path.abspath(EINSTELLUNGEN.db_pfad) + " (WAL)"


def module_und_zeitplaene():
    from apscheduler.triggers.cron import CronTrigger

    from app.bots import verzeichnis
    from app.zeit import zone

    alle = verzeichnis.alle()
    if len(alle) == 0:
        raise RuntimeError("kein einziges Modul im Verzeichnis")

    beschreibung = []
    for modul in alle:
        if modul.zeitplan is None:
            beschreibung.append(modul.name + " (nur von Hand)")
            continue

        # baut den Cron-Eintrag testweise auf, damit ein Tippfehler im Zeitplan
        # jetzt auffaellt und nicht erst beim Start des Dienstes
        CronTrigger(timezone=zone(), **modul.zeitplan)
        beschreibung.append(modul.name)

    return str(len(alle)) + " Module: " + ", ".join(beschreibung)


def modell_client():
    from app.llm.auswahl import modell
    from app.config import EINSTELLUNGEN

    modell()
    return EINSTELLUNGEN.llm_anbieter + " / " + EINSTELLUNGEN.modellname_standard()


def modell_echter_aufruf():
    from app.llm.auswahl import modell

    antwort = modell().text_erzeugen(
        "Antworte mit genau einem Wort.",
        "Sag OK",
        max_tokens=10,
    )
    return "Antwort: " + antwort.strip()[:40]


def feeds():
    from app.config import feeds_laden

    geladen = feeds_laden()
    if len(geladen) == 0:
        return "keine Feeds eingetragen (noch kein Problem, erst fürs Tagesaktuell-Modul)"

    return str(len(geladen)) + " Feeds"


def modullauf_trocken():
    """Lässt das erste Modul ohne Modellbedarf einmal wirklich laufen"""
    from app import planer
    from app.bots import verzeichnis

    for modul in verzeichnis.alle():
        if modul.braucht_modell:
            continue

        ergebnis = planer.lauf_ausfuehren(modul.name, von_hand=True)
        if ergebnis["status"] != "ok":
            raise RuntimeError(modul.name + " scheiterte: " + ergebnis["meldung"])

        return modul.name + " gelaufen: " + ergebnis["bericht"]["titel"]

    return "kein Modul ohne Modellbedarf vorhanden, übersprungen"


def main():
    mit_modellaufruf = "--modell" in sys.argv

    print("Steward Selbsttest")
    print("")

    pruefen("Python-Version", python_version)
    pruefen("API-Key", api_key)
    pruefen("Zeitzone", zeitzone)
    pruefen("Datenbank", datenbank_schreibbar)
    pruefen("Module und Zeitpläne", module_und_zeitplaene)
    pruefen("Modell-Client", modell_client)
    pruefen("RSS-Feeds", feeds)
    pruefen("Testlauf eines Moduls", modullauf_trocken)

    if mit_modellaufruf:
        pruefen("Echter Modellaufruf", modell_echter_aufruf)

    fehler = 0
    for geklappt, name, meldung in ergebnisse:
        if geklappt:
            print("  OK      " + name + ": " + meldung)
        else:
            print("  FEHLER  " + name + ": " + meldung)
            fehler = fehler + 1

    print("")
    if fehler == 0:
        print("Alles in Ordnung. Dienst kann eingeschaltet werden.")
        if not mit_modellaufruf:
            print("Der Modellaufruf selbst wurde nicht getestet: python -m app.selbsttest --modell")
        return 0

    print(str(fehler) + " Punkt(e) offen. Erst beheben, dann den Dienst einschalten.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
