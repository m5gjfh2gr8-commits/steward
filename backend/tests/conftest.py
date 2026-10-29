"""
Gemeinsame Vorbereitung für alle Tests

Jeder Test bekommt eine frische SQLite-Datei im temporären Ordner, einen Fake statt
dem echten Modell und ein Modul-Verzeichnis, das nur Testmodule enthält - damit die
Tests ohne API-Key, ohne Internet und ohne laufenden Planer durchlaufen
"""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["STEWARD_API_KEY"] = "test-key"
os.environ["STEWARD_LLM"] = "claude"
os.environ["ANTHROPIC_API_KEY"] = "nicht-echt"
os.environ["STEWARD_PLANER_AN"] = "false"

from app import datenbank                    # noqa: E402
from app.bots import verzeichnis             # noqa: E402
from app.bots.basis import Bericht, Modul    # noqa: E402
from app.config import EINSTELLUNGEN         # noqa: E402
from app.llm import auswahl                  # noqa: E402
from app.llm.basis import ModellBasis        # noqa: E402


class FakeModell(ModellBasis):
    """Gibt vorher festgelegte Antworten zurück, in der Reihenfolge wie sie gebraucht werden"""

    def __init__(self):
        self.antworten = []
        self.aufrufe = []
        self.tokens_pro_aufruf = (100, 50)

    def antwort_vormerken(self, text):
        self.antworten.append(text)

    def _aufruf(self, system_anweisung, benutzer_text, max_tokens, gross):
        self.aufrufe.append({"system": system_anweisung, "text": benutzer_text, "gross": gross})

        if len(self.antworten) == 0:
            antwort = "{}"
        else:
            antwort = self.antworten.pop(0)

        ein, aus = self.tokens_pro_aufruf
        return antwort, ein, aus


class TestModul(Modul):
    """Einfaches Modul, das immer einen festen Bericht liefert"""

    name = "testmodul"
    anzeigename = "Testmodul"
    beschreibung = "Nur für die Tests"
    zeitplan = {"hour": 6}
    braucht_modell = False

    def lauf(self):
        bericht = Bericht(titel="Testbericht", kurzfassung="alles gut")
        bericht.kennzahl_dazu("Zahl", 7)
        bericht.eintrag_dazu(titel="Ein Eintrag", text="mit Text", link="https://example.at")
        return bericht


class KaputtesModul(Modul):
    name = "kaputt"
    anzeigename = "Kaputtes Modul"
    zeitplan = None

    def lauf(self):
        raise RuntimeError("geht schief")


class ModellModul(Modul):
    """Modul, das das Modell benutzt - für die Tests der Kostenzählung"""

    name = "modellmodul"
    anzeigename = "Modellmodul"
    zeitplan = None
    braucht_modell = True

    def lauf(self):
        from app.llm.auswahl import modell
        antwort = modell().text_erzeugen("System", "Frage", max_tokens=100)
        return Bericht(titel="Modellbericht", kurzfassung=antwort)


@pytest.fixture
def fake_modell():
    modell = FakeModell()
    auswahl.modell_ersetzen(modell)
    yield modell
    auswahl.zwischenspeicher_leeren()


@pytest.fixture(autouse=True)
def frische_datenbank(tmp_path):
    EINSTELLUNGEN.db_pfad = str(tmp_path / "test.db")
    datenbank.vorbereiten()
    yield
    EINSTELLUNGEN.db_pfad = "steward.db"


@pytest.fixture(autouse=True)
def testmodule():
    """Ersetzt das echte Verzeichnis durch Testmodule und stellt es danach wieder her"""
    vorher = list(verzeichnis.MODULE)

    verzeichnis.MODULE.clear()
    verzeichnis.MODULE.extend([TestModul(), KaputtesModul(), ModellModul()])

    yield verzeichnis.MODULE

    verzeichnis.MODULE.clear()
    verzeichnis.MODULE.extend(vorher)


@pytest.fixture(autouse=True)
def budget_zuruecksetzen():
    """Die Grenzen hochsetzen, damit nicht ein Test den nächsten beeinflusst"""
    vorher_tag = EINSTELLUNGEN.tokenbudget_pro_tag
    vorher_lauf = EINSTELLUNGEN.tokenbudget_pro_lauf

    EINSTELLUNGEN.tokenbudget_pro_tag = 2000000
    EINSTELLUNGEN.tokenbudget_pro_lauf = 200000

    yield

    EINSTELLUNGEN.tokenbudget_pro_tag = vorher_tag
    EINSTELLUNGEN.tokenbudget_pro_lauf = vorher_lauf


@pytest.fixture
def klient():
    from fastapi.testclient import TestClient
    from app.main import anwendung

    with TestClient(anwendung) as verbindung:
        yield verbindung


@pytest.fixture
def kopf():
    return {"X-API-Key": "test-key"}
