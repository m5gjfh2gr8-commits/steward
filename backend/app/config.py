"""
Konfiguration für das Steward-Backend

Liest alles aus der .env-Datei bzw. den Umgebungsvariablen
Am Server kommt die Datei nicht aus dem Projektordner, sondern aus
/etc/steward/steward.env (per EnvironmentFile in der systemd-Unit)

Aufruf: from app.config import EINSTELLUNGEN
"""

import json
import os

from dotenv import load_dotenv

load_dotenv()


def text_aus_umgebung(name, standard=""):
    wert = os.environ.get(name)
    if wert is None:
        return standard
    return wert.strip()


def zahl_aus_umgebung(name, standard):
    rohwert = text_aus_umgebung(name)
    if rohwert == "":
        return standard
    try:
        return int(rohwert)
    except ValueError:
        return standard


def schalter_aus_umgebung(name, standard=False):
    rohwert = text_aus_umgebung(name).lower()
    if rohwert == "":
        return standard
    if rohwert in ["1", "true", "ja", "yes", "an"]:
        return True
    return False


class Einstellungen:
    def __init__(self):
        self.api_key = text_aus_umgebung("STEWARD_API_KEY")
        self.llm_anbieter = text_aus_umgebung("STEWARD_LLM", "claude").lower()

        self.anthropic_api_key = text_aus_umgebung("ANTHROPIC_API_KEY")
        self.claude_modell_standard = text_aus_umgebung("CLAUDE_MODELL_STANDARD", "claude-haiku-4-5-20251001")
        self.claude_modell_gross = text_aus_umgebung("CLAUDE_MODELL_GROSS", "claude-sonnet-5")

        self.ollama_url = text_aus_umgebung("OLLAMA_URL", "http://localhost:11434")
        self.ollama_modell = text_aus_umgebung("OLLAMA_MODELL", "llama3.1:8b")

        self.db_pfad = text_aus_umgebung("STEWARD_DB_PFAD", "steward.db")
        self.zeitzone = text_aus_umgebung("STEWARD_ZEITZONE", "Europe/Vienna")

        # Kostenbremse: harte Obergrenze pro Tag über alle Module zusammen
        # Wird sie erreicht, werden weitere Modellaufrufe abgelehnt statt still teurer zu werden
        self.tokenbudget_pro_tag = zahl_aus_umgebung("STEWARD_TOKENBUDGET_PRO_TAG", 2000000)
        self.tokenbudget_pro_lauf = zahl_aus_umgebung("STEWARD_TOKENBUDGET_PRO_LAUF", 200000)

        # Planer abdrehbar, praktisch zum Entwickeln
        self.planer_an = schalter_aus_umgebung("STEWARD_PLANER_AN", True)

        # Swagger-Oberfläche: im Betrieb aus, beim Entwickeln an
        self.swagger_an = schalter_aus_umgebung("STEWARD_SWAGGER_AN", False)

        self.config_ordner = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")

    def modellname_standard(self):
        if self.llm_anbieter == "claude":
            return self.claude_modell_standard
        return self.ollama_modell


EINSTELLUNGEN = Einstellungen()


def json_datei_laden(dateiname, standard):
    """
    Lädt eine JSON-Datei aus dem config-Ordner
    Eingabe: Dateiname ohne Pfad, Rückfallwert falls die Datei fehlt
    Ausgabe: geparstes JSON oder der Rückfallwert
    """
    pfad = os.path.join(EINSTELLUNGEN.config_ordner, dateiname)
    if not os.path.exists(pfad):
        return standard

    datei = open(pfad, "r", encoding="utf-8")
    inhalt = datei.read()
    datei.close()

    if inhalt.strip() == "":
        return standard
    return json.loads(inhalt)


def feeds_laden():
    """Ausgabe: Liste von Feed-Dicts, z.B. [{"name": "ORF", "url": "https://rss.orf.at/news.xml"}]"""
    return json_datei_laden("feeds.json", [])
