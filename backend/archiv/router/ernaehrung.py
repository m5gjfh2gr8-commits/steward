"""Endpunkte für den Kalorien-/Makro-Tracker"""

from fastapi import APIRouter, Depends, HTTPException

from app.dienste import ernaehrung, ziele
from app.modelle import ErnaehrungAenderung, FreitextAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/food", tags=["food"], dependencies=[Depends(api_key_pruefen)])


@router.post("/log")
def eintragen(anfrage: FreitextAnfrage):
    eintraege = ernaehrung.eintragen(anfrage.text)
    return {"eintraege": eintraege, "summe_eingabe": ernaehrung.summe_bilden(eintraege)}


@router.get("/today")
def heute():
    stand = ernaehrung.heutiger_stand()
    stand["ziele"] = ziele.holen()
    return stand


@router.get("/history")
def verlauf(tage: int = 30):
    return {"tage": tage, "verlauf": ernaehrung.verlauf(tage)}


@router.patch("/{eintrag_id}")
def aendern(eintrag_id: int, anfrage: ErnaehrungAenderung):
    ergebnis = ernaehrung.aendern(
        eintrag_id,
        anfrage.beschreibung,
        anfrage.menge_text,
        anfrage.kcal,
        anfrage.eiweiss_g,
        anfrage.kohlenhydrate_g,
        anfrage.fett_g,
    )
    if ergebnis is None:
        raise HTTPException(status_code=404, detail="Eintrag gibt es nicht")
    return ergebnis


@router.delete("/{eintrag_id}")
def loeschen(eintrag_id: int):
    if not ernaehrung.loeschen(eintrag_id):
        raise HTTPException(status_code=404, detail="Eintrag gibt es nicht")
    return {"gelöscht": True}
