"""Endpunkte fürs Interessensprofil und das News-Feedback"""

from fastapi import APIRouter, Depends, HTTPException

from app.dienste import nachrichten
from app.modelle import FeedbackAnfrage, InteressenAnfrage, VertiefenAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(tags=["profil"], dependencies=[Depends(api_key_pruefen)])


@router.get("/profile/interests")
def interessen_holen():
    nachrichten.standard_interessen_anlegen()
    return nachrichten.interessen_holen(nur_aktive=False)


@router.post("/profile/interests")
def interessen_setzen(anfrage: InteressenAnfrage):
    return nachrichten.interessen_setzen(anfrage.stichwoerter)


@router.post("/news/feedback")
def feedback(anfrage: FeedbackAnfrage):
    if anfrage.bewertung not in ["up", "down"]:
        raise HTTPException(status_code=400, detail="bewertung muss up oder down sein")
    nachrichten.feedback_speichern(anfrage.titel, anfrage.bewertung)
    return {"gespeichert": True}


@router.post("/news/vertiefen")
def vertiefen(anfrage: VertiefenAnfrage):
    """Wenn im Chat zu einer Meldung nachgefragt wird"""
    return {"text": nachrichten.vertiefen(anfrage.titel, anfrage.zusammenfassung)}
