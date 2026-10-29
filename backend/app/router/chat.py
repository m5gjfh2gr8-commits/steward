"""Das eine Eingabefeld der App"""

from fastapi import APIRouter, Depends

from app.dienste import chat
from app.modelle import FreitextAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(api_key_pruefen)])


@router.post("")
def verarbeiten(anfrage: FreitextAnfrage):
    return chat.verarbeiten(anfrage.text)
