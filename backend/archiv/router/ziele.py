"""Endpunkte für die Tagesziele"""

from fastapi import APIRouter, Depends

from app.dienste import ziele
from app.modelle import ZieleAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/goals", tags=["goals"], dependencies=[Depends(api_key_pruefen)])


@router.get("")
def holen():
    return ziele.holen()


@router.post("")
def setzen(anfrage: ZieleAnfrage):
    return ziele.setzen(
        anfrage.kcal_ziel,
        anfrage.eiweiss_ziel_g,
        anfrage.kohlenhydrate_ziel_g,
        anfrage.fett_ziel_g,
        anfrage.wasser_ziel_ml,
    )
