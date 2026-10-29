"""
Der Modul-Vertrag

Ein Modul ist ein eigenständiger Baustein, der für sich funktioniert und an Steward
berichtet. Steward weiß nicht, was innen passiert - er kennt nur:
  name          interner Name, taucht in URLs und in der Datenbank auf
  anzeigename   was in der App steht
  zeitplan      wann das Modul laufen soll (Cron-Felder)
  lauf()        tut die Arbeit und gibt genau einen Bericht zurück

Alles andere (Planen, Protokollieren, Ausliefern) macht Steward
"""


class Bericht:
    """
    Das einzige, was ein Modul nach außen gibt

    Absichtlich immer dieselbe Form, damit App und PC-Seite jeden Bericht gleich
    darstellen können - ein neues Modul braucht dann keine Änderung an der App

    kennzahlen: [{"name": "Geprüfte Meldungen", "wert": "42"}]
    eintraege:  [{"titel": "...", "text": "...", "link": "..."}]
    """

    def __init__(self, titel, kurzfassung="", kennzahlen=None, eintraege=None):
        self.titel = titel
        self.kurzfassung = kurzfassung

        if kennzahlen is None:
            self.kennzahlen = []
        else:
            self.kennzahlen = kennzahlen

        if eintraege is None:
            self.eintraege = []
        else:
            self.eintraege = eintraege

    def kennzahl_dazu(self, name, wert):
        self.kennzahlen.append({"name": name, "wert": str(wert)})

    def eintrag_dazu(self, titel, text="", link=""):
        self.eintraege.append({"titel": titel, "text": text, "link": link})


class Modul:
    """
    Basisklasse für alle Module

    Ein neues Modul erbt davon, setzt die vier Felder und schreibt lauf()
    Danach wird es in app/bots/verzeichnis.py eingetragen - sonst nichts
    """

    name = "unbenannt"
    anzeigename = "Unbenannt"
    beschreibung = ""

    # Cron-Felder für APScheduler, z.B. {"hour": 6, "minute": 0} = täglich 6:00
    # {"day_of_week": "sun", "hour": 18} = sonntags 18:00
    # None = läuft nie von selbst, nur von Hand
    zeitplan = None

    # Sagt der Kostenbremse, ob hier Modellaufrufe zu erwarten sind
    braucht_modell = False

    def lauf(self):
        """
        Macht die Arbeit des Moduls
        Ausgabe: genau ein Bericht
        Fehler dürfen hier normal hochgeworfen werden, der Planer fängt sie
        """
        raise NotImplementedError
