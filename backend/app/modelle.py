"""
Pydantic-Modelle für die Anfragen

Nur für das, was reinkommt - die Antworten gehen als normale Dicts raus,
damit die Dienste ihre Datenbankzeilen nicht extra umbauen müssen
"""

from typing import Optional

from pydantic import BaseModel


class FreitextAnfrage(BaseModel):
    text: str


class TodoAnfrage(BaseModel):
    inhalt: str
    faellig_am: Optional[str] = None
    quelle: str = "text"


class TodoAenderung(BaseModel):
    inhalt: Optional[str] = None
    faellig_am: Optional[str] = None
    erledigt: Optional[bool] = None


class InteressenAnfrage(BaseModel):
    stichwoerter: list[str]


class FeedbackAnfrage(BaseModel):
    titel: str
    bewertung: str


class VertiefenAnfrage(BaseModel):
    titel: str
    zusammenfassung: str = ""


class GelesenAnfrage(BaseModel):
    zeitpunkt: Optional[str] = None
