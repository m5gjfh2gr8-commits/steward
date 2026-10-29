"""Endpunkte für Todos und Termine"""

from fastapi import APIRouter, Depends, HTTPException

from app.dienste import todos
from app.modelle import FreitextAnfrage, TodoAenderung, TodoAnfrage
from app.sicherheit import api_key_pruefen

router = APIRouter(prefix="/tasks", tags=["tasks"], dependencies=[Depends(api_key_pruefen)])


@router.post("/parse")
def freitext_zerlegen(anfrage: FreitextAnfrage):
    """Freitext rein, strukturiertes Objekt raus - die App plant daraus selbst die lokale Erinnerung"""
    return todos.freitext_zerlegen(anfrage.text)


@router.get("")
def liste(nur_offen: bool = True):
    return todos.liste_holen(nur_offen)


@router.post("")
def anlegen(anfrage: TodoAnfrage):
    return todos.anlegen(anfrage.inhalt, anfrage.faellig_am, anfrage.quelle)


@router.patch("/{todo_id}")
def aendern(todo_id: int, anfrage: TodoAenderung):
    ergebnis = todos.aendern(todo_id, anfrage.inhalt, anfrage.faellig_am, anfrage.erledigt)
    if ergebnis is None:
        raise HTTPException(status_code=404, detail="Todo gibt es nicht")
    return ergebnis


@router.delete("/{todo_id}")
def loeschen(todo_id: int):
    if not todos.loeschen(todo_id):
        raise HTTPException(status_code=404, detail="Todo gibt es nicht")
    return {"gelöscht": True}
