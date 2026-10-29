"""Status-Endpunkte, damit App und PC den Verbindungs- und Gesundheitszustand sehen"""

from fastapi import APIRouter, Depends

from app import planer
from app.bots import verzeichnis
from app.config import EINSTELLUNGEN, feeds_laden
from app.dienste import kosten
from app.sicherheit import api_key_pruefen
from app.zeit import jetzt_text

router = APIRouter(tags=["system"])


@router.get("/health")
def gesundheit():
    """Ohne API-Key erreichbar, sagt nur dass der Server läuft"""
    return {"status": "ok", "zeit": jetzt_text()}


@router.get("/status", dependencies=[Depends(api_key_pruefen)])
def status():
    """Was ist eingerichtet und was fehlt noch - praktisch beim Aufsetzen"""
    feeds = []
    for feed in feeds_laden():
        feeds.append(feed.get("name", "unbenannt"))

    return {
        "zeit": jetzt_text(),
        "llm_anbieter": EINSTELLUNGEN.llm_anbieter,
        "llm_modell_standard": EINSTELLUNGEN.modellname_standard(),
        "module": verzeichnis.namen(),
        "planer_laeuft": planer.laeuft(),
        "eingeplant": planer.eingeplante_namen(),
        "feeds": feeds,
        "verbrauch_heute": kosten.verbrauch_heute(),
    }


@router.get("/kosten", dependencies=[Depends(api_key_pruefen)])
def kostenuebersicht(tage: int = 14):
    return {"heute": kosten.verbrauch_heute(), "verlauf": kosten.verlauf(tage)}
