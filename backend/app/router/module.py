"""
Modul-Endpunkte

Das ist die Schnittstelle, über die App und PC-Seite alles über die Module erfahren
Bewusst generisch: ein neues Modul taucht hier automatisch auf, sobald es im
Verzeichnis steht - die App muss dafür nicht neu gebaut werden
"""

from fastapi import APIRouter, Depends, HTTPException

from app import planer
from app.bots import verzeichnis
from app.dienste import berichte as berichte_dienst
from app.dienste import kosten
from app.modelle import GelesenAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/module", tags=["module"], dependencies=[Depends(api_key_pruefen)])


@router.get("")
def liste():
    """Alle Module mit Zustand, Ungelesen-Zähler und letztem Bericht"""
    gesammelt = []

    for zustand in berichte_dienst.zustand_aller_module():
        kopie = dict(zustand)
        kopie["naechster_lauf"] = planer.naechster_lauf(zustand["name"])
        gesammelt.append(kopie)

    return gesammelt


@router.get("/zustand")
def zustand():
    """Kurzüberblick für die Überwachung: wer lebt, wer nicht, was kostet es"""
    alle = berichte_dienst.zustand_aller_module()

    auffaellig = []
    for eintrag in alle:
        if eintrag["zustand"] in ["kaputt", "wackelig"]:
            auffaellig.append({"name": eintrag["name"], "zustand": eintrag["zustand"]})

    ungelesen_gesamt = 0
    for eintrag in alle:
        ungelesen_gesamt = ungelesen_gesamt + eintrag["ungelesen"]

    return {
        "planer_laeuft": planer.laeuft(),
        "anzahl_module": len(alle),
        "auffaellig": auffaellig,
        "ungelesen_gesamt": ungelesen_gesamt,
        "verbrauch_heute": kosten.verbrauch_heute(),
    }


def modul_oder_404(name):
    modul = verzeichnis.nach_name(name)
    if modul is None:
        raise HTTPException(status_code=404, detail="Modul " + name + " gibt es nicht")
    return modul


@router.get("/{name}")
def einzelnes(name: str):
    modul = modul_oder_404(name)
    zustand = berichte_dienst.zustand_von_modul(modul)
    zustand["naechster_lauf"] = planer.naechster_lauf(name)
    return zustand


@router.get("/{name}/berichte")
def berichte(name: str, anzahl: int = 20):
    modul_oder_404(name)

    if anzahl < 1:
        anzahl = 1
    if anzahl > 200:
        anzahl = 200

    return {
        "modul": name,
        "gelesen_bis": berichte_dienst.gelesen_holen(name),
        "berichte": berichte_dienst.berichte_von_modul(name, anzahl),
    }


@router.get("/{name}/laeufe")
def laeufe(name: str, anzahl: int = 20):
    modul_oder_404(name)
    return {"modul": name, "laeufe": berichte_dienst.laeufe_von_modul(name, anzahl)}


@router.post("/{name}/lauf")
def jetzt_laufen(name: str):
    """
    Startet das Modul sofort, unabhängig vom Zeitplan
    Läuft synchron - bei einem langen Modul kann die Antwort also dauern
    """
    modul_oder_404(name)
    ergebnis = planer.lauf_ausfuehren(name, von_hand=True)

    if ergebnis["status"] == "beschaeftigt":
        raise HTTPException(status_code=409, detail="Modul läuft gerade schon")

    return ergebnis


@router.post("/{name}/gelesen")
def gelesen(name: str, anfrage: GelesenAnfrage):
    modul_oder_404(name)
    gesetzt = berichte_dienst.gelesen_setzen(name, anfrage.zeitpunkt)
    return {"modul": name, "gelesen_bis": gesetzt, "ungelesen": berichte_dienst.anzahl_ungelesen(name)}
