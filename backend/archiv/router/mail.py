"""Endpunkt für die Mail-Anzeige"""

from fastapi import APIRouter, Depends

from app.dienste import mail
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/mail", tags=["mail"], dependencies=[Depends(api_key_pruefen)])


@router.get("/important")
def wichtige(neu_laden: bool = False):
    """
    Ohne neu_laden kommt der Stand von heute aus dem Zwischenspeicher zurück,
    es wird also nur einmal pro Tag wirklich per IMAP abgefragt und bewertet
    """
    return mail.wichtige_mails(neu_laden)
