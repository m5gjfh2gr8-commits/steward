"""
Der Planer

Steward wartet nicht darauf, dass sich Module melden - er startet sie. Hier steht
die Uhr: pro Modul ein Cron-Eintrag aus seinem zeitplan, dazu die Möglichkeit,
einen Lauf von Hand anzustoßen

lauf_ausfuehren() ist die einzige Stelle, an der ein Modul aufgerufen wird. Egal ob
nach Zeitplan oder von Hand - es läuft immer durch dieselbe Umklammerung mit
Protokoll, Fehlerfang und Kostenzählung. Ein Modul, das sich aufhängt oder
abstürzt, darf Steward nicht mitnehmen
"""

import threading

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.bots import verzeichnis
from app.config import EINSTELLUNGEN
from app.dienste import berichte as berichte_dienst
from app.dienste import kosten
from app.zeit import zone

_planer = None

# verhindert, dass dasselbe Modul doppelt läuft (Zeitplan und Hand-Start gleichzeitig)
_sperren = {}
_sperren_schloss = threading.Lock()


def sperre_fuer(modul_name):
    with _sperren_schloss:
        if modul_name not in _sperren:
            _sperren[modul_name] = threading.Lock()
        return _sperren[modul_name]


def lauf_ausfuehren(modul_name, von_hand=False):
    """
    Führt ein Modul aus und protokolliert den Lauf
    Ausgabe: {"status": "ok"/"fehler"/"beschaeftigt"/"unbekannt", "meldung":..., "bericht":...}
    Wirft nie - Fehler landen im Protokoll und in der Rückgabe
    """
    modul = verzeichnis.nach_name(modul_name)
    if modul is None:
        return {"status": "unbekannt", "meldung": "Modul " + modul_name + " gibt es nicht", "bericht": None}

    sperre = sperre_fuer(modul_name)
    if not sperre.acquire(blocking=False):
        return {"status": "beschaeftigt", "meldung": "Modul läuft schon", "bericht": None}

    lauf_id = berichte_dienst.lauf_beginnen(modul_name)
    kosten.aktuelles_modul_setzen(modul_name)

    try:
        bericht = modul.lauf()
        gespeichert = berichte_dienst.bericht_speichern(modul_name, bericht)

        tokens_ein, tokens_aus = kosten.tokens_im_lauf()
        berichte_dienst.lauf_abschliessen(lauf_id, "ok", "", tokens_ein, tokens_aus)

        return {"status": "ok", "meldung": "", "bericht": gespeichert}

    except Exception as fehler:
        tokens_ein, tokens_aus = kosten.tokens_im_lauf()
        text = type(fehler).__name__ + ": " + str(fehler)
        berichte_dienst.lauf_abschliessen(lauf_id, "fehler", text, tokens_ein, tokens_aus)

        return {"status": "fehler", "meldung": text, "bericht": None}

    finally:
        kosten.aktuelles_modul_loeschen()
        sperre.release()


def _nach_zeitplan(modul_name):
    """Was APScheduler aufruft - absichtlich ohne Rückgabe, das Ergebnis steht im Protokoll"""
    lauf_ausfuehren(modul_name, von_hand=False)


def starten():
    """
    Baut den Planer auf und hängt für jedes Modul mit zeitplan einen Cron-Eintrag rein
    Ausgabe: Liste der eingeplanten Modulnamen
    """
    global _planer

    berichte_dienst.haengende_laeufe_aufraeumen()

    if not EINSTELLUNGEN.planer_an:
        return []

    if _planer is not None:
        return eingeplante_namen()

    _planer = BackgroundScheduler(timezone=zone())

    eingeplant = []
    for modul in verzeichnis.alle():
        if modul.zeitplan is None:
            continue

        _planer.add_job(
            _nach_zeitplan,
            trigger=CronTrigger(timezone=zone(), **modul.zeitplan),
            args=[modul.name],
            id=modul.name,
            name=modul.anzeigename,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=3600,
            replace_existing=True,
        )
        eingeplant.append(modul.name)

    _planer.start()
    return eingeplant


def stoppen():
    global _planer
    if _planer is None:
        return

    _planer.shutdown(wait=False)
    _planer = None


def laeuft():
    if _planer is None:
        return False
    return _planer.running


def eingeplante_namen():
    if _planer is None:
        return []

    namen = []
    for auftrag in _planer.get_jobs():
        namen.append(auftrag.id)
    return namen


def naechster_lauf(modul_name):
    """Ausgabe: ISO-Text des nächsten geplanten Laufs, None wenn nichts geplant ist"""
    if _planer is None:
        return None

    auftrag = _planer.get_job(modul_name)
    if auftrag is None:
        return None
    if auftrag.next_run_time is None:
        return None

    return auftrag.next_run_time.isoformat(timespec="seconds")
