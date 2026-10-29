"""Endpunkte für den Flüssigkeits-Counter"""

from fastapi import APIRouter, Depends, HTTPException

from app.dienste import wasser, ziele
from app.modelle import WasserAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/water", tags=["water"], dependencies=[Depends(api_key_pruefen)])


@router.post("/log")
def eintragen(anfrage: WasserAnfrage):
    if anfrage.menge_ml <= 0:
        raise HTTPException(status_code=400, detail="Menge muss größer als 0 sein")
    wasser.eintragen(anfrage.menge_ml)
    stand = wasser.heutiger_stand()
    stand["ziel_ml"] = ziele.holen()["wasser_ziel_ml"]
    return stand


@router.get("/today")
def heute():
    stand = wasser.heutiger_stand()
    stand["ziel_ml"] = ziele.holen()["wasser_ziel_ml"]
    return stand


@router.delete("/{eintrag_id}")
def loeschen(eintrag_id: int):
    if not wasser.loeschen(eintrag_id):
        raise HTTPException(status_code=404, detail="Eintrag gibt es nicht")
    return {"gelöscht": True}
