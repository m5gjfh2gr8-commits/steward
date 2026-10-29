"""
Wählt anhand der Konfiguration den passenden Modell-Client

Der Client wird einmal gebaut und danach wiederverwendet
Aufruf: from app.llm.auswahl import modell
"""

from app.config import EINSTELLUNGEN
from app.llm.basis import ModellFehler

_zwischenspeicher = {}


def modell():
    anbieter = EINSTELLUNGEN.llm_anbieter

    if anbieter in _zwischenspeicher:
        return _zwischenspeicher[anbieter]

    # Import erst hier, damit ein fehlendes Paket als ModellFehler ankommt und nicht
    # als unbehandelter Absturz mit "Internal Server Error"
    try:
        if anbieter == "claude":
            from app.llm.claude_client import ClaudeClient
            gebaut = ClaudeClient()
        elif anbieter == "ollama":
            from app.llm.ollama_client import OllamaClient
            gebaut = OllamaClient()
        else:
            raise ModellFehler("Unbekannter Wert für STEWARD_LLM: " + anbieter)
    except ModellFehler:
        raise
    except ImportError as fehler:
        raise ModellFehler("Paket für " + anbieter + " fehlt: " + str(fehler))
    except Exception as fehler:
        raise ModellFehler("Modell-Client lässt sich nicht aufbauen: " + str(fehler))

    _zwischenspeicher[anbieter] = gebaut
    return gebaut


def modell_ersetzen(ersatz):
    """Nur für Tests - setzt einen Fake-Client statt dem echten Modell ein"""
    _zwischenspeicher[EINSTELLUNGEN.llm_anbieter] = ersatz


def zwischenspeicher_leeren():
    _zwischenspeicher.clear()
