"""
Gemeinsame Schnittstelle für alle Modelle

Jeder Client (Claude, Ollama) bietet dieselben Methoden an, damit der Rest vom
Backend nicht wissen muss, welches Modell gerade eingestellt ist

Jeder Aufruf geht durch die Kostenbremse: vorher wird das Budget geprüft,
nachher der Verbrauch gebucht
"""

import json


class ModellFehler(Exception):
    pass


class ModellBasis:
    def _aufruf(self, system_anweisung, benutzer_text, max_tokens, gross):
        """
        Macht den eigentlichen Aufruf
        Ausgabe: (antworttext, tokens_ein, tokens_aus)
        """
        raise NotImplementedError

    def text_erzeugen(self, system_anweisung, benutzer_text, max_tokens=1000, gross=False):
        from app.dienste import kosten

        kosten.budget_pruefen()
        antwort, tokens_ein, tokens_aus = self._aufruf(system_anweisung, benutzer_text, max_tokens, gross)
        kosten.verbrauch_buchen(tokens_ein, tokens_aus)
        return antwort

    def json_erzeugen(self, system_anweisung, benutzer_text, max_tokens=1000, gross=False):
        """
        Wie text_erzeugen, aber das Ergebnis wird als JSON geparst
        Ausgabe: geparstes dict oder list
        """
        antwort = self.text_erzeugen(system_anweisung, benutzer_text, max_tokens, gross)
        return json_aus_antwort(antwort)


def json_aus_antwort(antwort):
    """
    Modelle packen JSON gerne in einen ```json-Block oder schreiben einen Satz davor,
    deshalb wird hier der erste echte JSON-Block aus der Antwort herausgeschnitten
    """
    text = antwort.strip()

    if "```" in text:
        teile = text.split("```")
        for teil in teile:
            sauber = teil.strip()
            if sauber.startswith("json"):
                sauber = sauber[4:].strip()
            if sauber.startswith("{") or sauber.startswith("["):
                text = sauber
                break

    start_objekt = text.find("{")
    start_liste = text.find("[")

    if start_objekt == -1 and start_liste == -1:
        raise ModellFehler("Antwort enthält kein JSON: " + antwort[:200])

    if start_liste == -1:
        start = start_objekt
        ende = text.rfind("}")
    elif start_objekt == -1:
        start = start_liste
        ende = text.rfind("]")
    elif start_objekt < start_liste:
        start = start_objekt
        ende = text.rfind("}")
    else:
        start = start_liste
        ende = text.rfind("]")

    ausschnitt = text[start:ende + 1]

    try:
        return json.loads(ausschnitt)
    except json.JSONDecodeError as fehler:
        raise ModellFehler("JSON kaputt: " + str(fehler) + " / Antwort: " + antwort[:200])
