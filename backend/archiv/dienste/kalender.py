"""
Kalender über CalDAV (iCloud)

Der Server holt sich die Termine direkt vom iCloud-Kalender, damit er auch arbeiten kann
wenn das Handy aus ist. Nötig dafür: Apple-ID plus app-spezifisches Passwort in der .env
Läuft komplett lesend, es wird nichts im Kalender geändert
"""

from datetime import timedelta

from app.config import EINSTELLUNGEN
from app.zeit import jetzt


def verbinden():
    """Ausgabe: Liste der Kalender-Objekte, leer wenn nichts eingerichtet oder erreichbar ist"""
    if not EINSTELLUNGEN.kalender_ist_eingerichtet():
        return []

    import caldav

    client = caldav.DAVClient(
        url=EINSTELLUNGEN.caldav_url,
        username=EINSTELLUNGEN.caldav_benutzer,
        password=EINSTELLUNGEN.caldav_passwort,
    )
    hauptkonto = client.principal()
    alle = hauptkonto.calendars()

    if EINSTELLUNGEN.caldav_kalender_name == "":
        return alle

    passende = []
    for kalender in alle:
        if kalender.name == EINSTELLUNGEN.caldav_kalender_name:
            passende.append(kalender)

    return passende


def termin_lesbar_machen(ereignis):
    """
    Eingabe: ein CalDAV-Ereignis
    Ausgabe: {"titel":..., "beginn":..., "ende":..., "ganztaegig":..., "ort":...}
    """
    daten = ereignis.icalendar_component

    titel = str(daten.get("summary", "Termin"))

    ort = daten.get("location")
    if ort is None:
        ort = ""
    else:
        ort = str(ort)

    beginn_roh = daten.get("dtstart")
    ende_roh = daten.get("dtend")

    beginn = ""
    ende = ""
    ganztaegig = False

    if beginn_roh is not None:
        wert = beginn_roh.dt
        if hasattr(wert, "hour"):
            beginn = wert.isoformat()
        else:
            beginn = wert.isoformat()
            ganztaegig = True

    if ende_roh is not None:
        ende = ende_roh.dt.isoformat()

    return {"titel": titel, "beginn": beginn, "ende": ende, "ganztaegig": ganztaegig, "ort": ort}


def termine_holen(tage=1):
    """
    Eingabe: wie viele Tage ab jetzt
    Ausgabe: (Liste lesbarer Termine sortiert nach Beginn, Fehlertext oder "")
    """
    try:
        kalender = verbinden()
    except Exception as fehler:
        return [], "Kalender nicht erreichbar: " + str(fehler)

    if len(kalender) == 0:
        return [], ""

    von = jetzt().replace(hour=0, minute=0, second=0, microsecond=0)
    bis = von + timedelta(days=tage)

    gesammelt = []
    for einzelner in kalender:
        try:
            ereignisse = einzelner.search(start=von, end=bis, event=True, expand=True)
        except Exception:
            continue

        for ereignis in ereignisse:
            try:
                gesammelt.append(termin_lesbar_machen(ereignis))
            except Exception:
                continue

    def nach_beginn(eintrag):
        return eintrag["beginn"]

    gesammelt.sort(key=nach_beginn)
    return gesammelt, ""
