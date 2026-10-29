"""
Das eine Eingabefeld der App

Lorenz tippt oder diktiert irgendwas rein, hier wird entschieden worum es geht:
eine Aufgabe/ein Termin, oder eine Frage an Steward

Kostet einen zusätzlichen kleinen Modellaufruf, dafür braucht die App keine
Auswahl-Buttons
"""

from app.bots import verzeichnis
from app.dienste import berichte as berichte_dienst
from app.dienste import todos
from app.llm.auswahl import modell

SYSTEM_EINORDNEN = """Du ordnest eine kurze deutschsprachige Eingabe einer von zwei Arten zu.
Antworte ausschliesslich mit JSON, ohne Erklaerung:
{"art": "aufgabe"}

Moegliche Werte fuer "art":
- "aufgabe": eine Aufgabe oder ein Termin, den er sich merken will
- "frage": alles andere, eine Frage oder Bitte um Auskunft"""


def einordnen(text):
    ergebnis = modell().json_erzeugen(SYSTEM_EINORDNEN, text, max_tokens=100)

    art = ergebnis.get("art", "frage")
    if art not in ["aufgabe", "frage"]:
        art = "frage"
    return art


def kontext_bauen():
    """Kurzer Überblick für den Frage-Fall, damit das Modell nicht ins Blaue antwortet"""
    offene = todos.liste_holen(nur_offen=True)

    text = "Offene Aufgaben: "
    if len(offene) == 0:
        text = text + "keine\n"
    else:
        namen = []
        for eintrag in offene[:10]:
            namen.append(eintrag["inhalt"])
        text = text + "; ".join(namen) + "\n"

    text = text + "Module und ihr letzter Stand:\n"
    for zustand in berichte_dienst.zustand_aller_module():
        zeile = "- " + zustand["anzeigename"] + " (" + zustand["zustand"] + ")"

        letzter = zustand["letzter_bericht"]
        if letzter is not None:
            zeile = zeile + ": " + letzter["titel"]
            if letzter["kurzfassung"] != "":
                zeile = zeile + " - " + letzter["kurzfassung"]

        text = text + zeile + "\n"

    return text


def frage_beantworten(text):
    system = "Du bist Steward, der persönliche Assistent von Lorenz. Antworte kurz, auf Deutsch, "
    system = system + "ohne Floskeln. Wenn du etwas nicht weißt, sag es statt zu raten."

    eingabe = "Aktueller Stand:\n" + kontext_bauen() + "\nFrage: " + text
    return modell().text_erzeugen(system, eingabe, max_tokens=500)


def verarbeiten(text):
    """
    Ausgabe: {"art":..., "antwort": Text für die App, "daten": das was angelegt wurde}
    Bei "aufgabe" steckt in daten das Todo, aus dem die App die lokale Erinnerung plant
    """
    art = einordnen(text)

    if art == "aufgabe":
        zerlegt = todos.freitext_zerlegen(text)
        angelegt = todos.anlegen(zerlegt["inhalt"], zerlegt["faellig_am"], "chat")

        antwort = "Gemerkt: " + angelegt["inhalt"]
        if angelegt["faellig_am"] is not None:
            antwort = antwort + " (" + angelegt["faellig_am"].replace("T", " ")[:16] + ")"

        return {"art": "aufgabe", "antwort": antwort, "daten": angelegt}

    return {"art": "frage", "antwort": frage_beantworten(text), "daten": None}
