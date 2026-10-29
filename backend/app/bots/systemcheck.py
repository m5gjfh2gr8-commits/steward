"""
Modul: Systemcheck

Das Überwachungs-Modul. Schaut sich die Läufe aller anderen Module an und meldet,
wer seit zu langer Zeit nicht mehr durchgekommen ist oder wiederholt scheitert
Dazu ein Blick auf Plattenplatz und Datenbankgröße

Braucht kein Modell und kein Internet, kostet also nichts
"""

import os
import shutil

from app.bots.basis import Bericht, Modul
from app.config import EINSTELLUNGEN
from app.dienste import berichte as berichte_dienst
from app.dienste import kosten
from app.zeit import stunden_seit

# ab wie vielen Stunden ohne erfolgreichen Lauf ein Modul als auffällig gilt
GRENZE_STUNDEN = 36


class SystemCheck(Modul):
    name = "systemcheck"
    anzeigename = "Systemcheck"
    beschreibung = "Überwacht die anderen Module, den Plattenplatz und den Token-Verbrauch"
    zeitplan = {"hour": "*", "minute": 5}
    braucht_modell = False

    def lauf(self):
        bericht = Bericht(titel="Systemcheck")

        auffaellige = []

        for zustand in berichte_dienst.zustand_aller_module():
            if zustand["name"] == self.name:
                continue

            if zustand["letzter_erfolg"] is None:
                auffaellige.append(zustand["anzeigename"] + ": noch nie erfolgreich gelaufen")
            else:
                stunden = stunden_seit(zustand["letzter_erfolg"])
                if stunden is not None and stunden > GRENZE_STUNDEN:
                    auffaellige.append(zustand["anzeigename"] + ": letzter Erfolg vor " + str(int(stunden)) + " Stunden")

            # auch prüfen wenn es noch nie erfolgreich war - wiederholte Fehler sind das schärfere Signal
            if zustand["fehler_in_folge"] >= 3:
                auffaellige.append(zustand["anzeigename"] + ": " + str(zustand["fehler_in_folge"]) + " Fehler in Folge")

        platz = platzangabe()
        db_groesse = datenbankgroesse_mb()
        verbrauch = kosten.verbrauch_heute()

        bericht.kennzahl_dazu("Module auffällig", len(auffaellige))
        bericht.kennzahl_dazu("Platte frei", str(platz) + " GB")
        bericht.kennzahl_dazu("Datenbank", str(db_groesse) + " MB")
        bericht.kennzahl_dazu("Tokens heute", verbrauch["tokens_gesamt"])

        if len(auffaellige) == 0:
            bericht.kurzfassung = "Alles ruhig, alle Module laufen"
        else:
            bericht.kurzfassung = str(len(auffaellige)) + " Modul(e) brauchen einen Blick"
            for meldung in auffaellige:
                bericht.eintrag_dazu(titel=meldung)

        if platz is not None and platz < 2:
            bericht.eintrag_dazu(titel="Plattenplatz knapp", text="nur noch " + str(platz) + " GB frei")

        return bericht


def platzangabe():
    """Ausgabe: freier Plattenplatz in GB, gerundet, None wenn nicht ermittelbar"""
    try:
        ordner = os.path.dirname(os.path.abspath(EINSTELLUNGEN.db_pfad))
        if ordner == "":
            ordner = "."
        belegung = shutil.disk_usage(ordner)
    except OSError:
        return None

    return round(belegung.free / (1024 ** 3), 1)


def datenbankgroesse_mb():
    if not os.path.exists(EINSTELLUNGEN.db_pfad):
        return 0.0
    groesse = os.path.getsize(EINSTELLUNGEN.db_pfad)
    return round(groesse / (1024 ** 2), 2)
