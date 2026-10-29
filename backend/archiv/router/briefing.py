"""Endpunkt fürs Morning Briefing"""

from fastapi import APIRouter, Depends

from app.dienste import briefing
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/briefing", tags=["briefing"], dependencies=[Depends(api_key_pruefen)])


@router.get("/morning")
def morgen(neu_laden: bool = False):
    ergebnis = briefing.bauen(neu_laden)
    ergebnis["vorlesetext"] = briefing.als_text(ergebnis)
    return ergebnis
