"""
Steward Backend

Startet die REST-API für App und PC und den Planer, der die Module nach Zeitplan laufen lässt
Aufruf: uvicorn app.main:anwendung --host 0.0.0.0 --port 8000
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import datenbank, planer
from app.config import EINSTELLUNGEN
from app.dienste.kosten import BudgetErschoepft
from app.llm.basis import ModellFehler
from app.router import chat, module, profil, system, tasks, web


@asynccontextmanager
async def lebenslauf(app):
    datenbank.vorbereiten()
    planer.starten()
    yield
    planer.stoppen()


# Swagger ist im Betrieb aus, weil sie ohne Key das ganze Schema zeigt
if EINSTELLUNGEN.swagger_an:
    docs_pfad = "/docs"
    openapi_pfad = "/openapi.json"
else:
    docs_pfad = None
    openapi_pfad = None

anwendung = FastAPI(
    title="Steward",
    version="2.0",
    lifespan=lebenslauf,
    docs_url=docs_pfad,
    redoc_url=None,
    openapi_url=openapi_pfad,
)

anwendung.include_router(system.router)
anwendung.include_router(module.router)
anwendung.include_router(chat.router)
anwendung.include_router(tasks.router)
anwendung.include_router(profil.router)
anwendung.include_router(web.router)


# Ein nicht erreichbares Modell oder ein erschoepftes Budget ist kein Programmfehler,
# sondern ein Zustand, den die App anzeigen soll - deshalb eine lesbare Meldung
# statt "Internal Server Error"

@anwendung.exception_handler(ModellFehler)
async def modellfehler_behandeln(anfrage: Request, fehler: ModellFehler):
    return JSONResponse(status_code=503, content={"detail": "Modell nicht verfügbar: " + str(fehler)})


@anwendung.exception_handler(BudgetErschoepft)
async def budget_behandeln(anfrage: Request, fehler: BudgetErschoepft):
    return JSONResponse(status_code=429, content={"detail": str(fehler)})
