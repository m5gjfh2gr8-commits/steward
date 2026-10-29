"""
PC-Zugang über den Browser

Ganz schlichte Seite, absichtlich ohne Design - die kommt dran wenn das Gerüst steht
Zweck fürs Erste: am PC sehen, was die Module gemacht haben, ohne die App zu brauchen

Der API-Key wird einmal in ein Formular eingegeben und landet in einem HttpOnly-Cookie.
So steht er nicht in der Adresszeile und damit nicht in der Browser-Historie
"""

import hmac
import html

from fastapi import APIRouter, Cookie, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app import planer
from app.config import EINSTELLUNGEN
from app.dienste import berichte as berichte_dienst
from app.dienste import kosten

router = APIRouter(tags=["web"], include_in_schema=False)

COOKIE_NAME = "steward_key"


def key_stimmt(key):
    if key is None:
        return False
    if EINSTELLUNGEN.api_key == "":
        return False
    return hmac.compare_digest(key, EINSTELLUNGEN.api_key)


def seite(inhalt, titel="Steward"):
    """Minimales Gerüst - ein bisschen Grundlayout, damit es am großen Bildschirm lesbar ist"""
    kopf = """<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>""" + html.escape(titel) + """</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 52rem; margin: 2rem auto; padding: 0 1rem;
         line-height: 1.5; color: #1a1a1a; background: #fafafa; }
  h1 { font-size: 1.4rem; }
  h2 { font-size: 1.1rem; margin-top: 2rem; }
  .karte { background: #fff; border: 1px solid #e0e0e0; border-radius: 8px; padding: 1rem; margin: 0.75rem 0; }
  .leise { color: #666; font-size: 0.875rem; }
  .ok { color: #1a7f37; } .wackelig { color: #9a6700; } .kaputt { color: #b42318; } .neu { color: #666; }
  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  td, th { text-align: left; padding: 0.3rem 0.6rem 0.3rem 0; }
  form { margin: 1rem 0; }
  input { padding: 0.4rem; font-size: 1rem; }
  button { padding: 0.4rem 0.8rem; font-size: 0.9rem; cursor: pointer; }
</style></head><body>
"""
    return HTMLResponse(kopf + inhalt + "</body></html>")


@router.get("/anmelden")
def anmelden_formular(fehler: str = ""):
    hinweis = ""
    if fehler != "":
        hinweis = '<p class="kaputt">' + html.escape(fehler) + "</p>"

    inhalt = """<h1>Steward</h1>
""" + hinweis + """
<form method="post" action="/anmelden">
  <input type="password" name="key" placeholder="API-Key" autofocus style="width: 22rem">
  <button type="submit">Anmelden</button>
</form>
<p class="leise">Derselbe Key wie in der Konfiguration am Server. Er wird in einem Cookie
auf diesem Rechner gespeichert, nicht in der Adresszeile.</p>"""

    return seite(inhalt, "Steward - Anmelden")


@router.post("/anmelden")
def anmelden(key: str = Form(default="")):
    if not key_stimmt(key):
        return RedirectResponse("/anmelden?fehler=Key+passt+nicht", status_code=303)

    antwort = RedirectResponse("/", status_code=303)
    antwort.set_cookie(
        COOKIE_NAME,
        key,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 365,
    )
    return antwort


@router.get("/abmelden")
def abmelden():
    antwort = RedirectResponse("/anmelden", status_code=303)
    antwort.delete_cookie(COOKIE_NAME)
    return antwort


@router.get("/")
def uebersicht(steward_key: str = Cookie(default=None)):
    if not key_stimmt(steward_key):
        return RedirectResponse("/anmelden", status_code=303)

    verbrauch = kosten.verbrauch_heute()

    if planer.laeuft():
        planer_text = "läuft"
    else:
        planer_text = "aus"

    teile = ["<h1>Steward</h1>"]
    teile.append('<p class="leise">Planer: ' + planer_text)
    teile.append(" · Tokens heute: " + str(verbrauch["tokens_gesamt"]))
    teile.append(" von " + str(verbrauch["budget_pro_tag"]))
    teile.append(' · <a href="/abmelden">abmelden</a></p>')

    for zustand in berichte_dienst.zustand_aller_module():
        teile.append(modul_karte(zustand))

    return seite("".join(teile))


def modul_karte(zustand):
    zeilen = ['<div class="karte">']
    zeilen.append("<h2>" + html.escape(zustand["anzeigename"]))
    zeilen.append(' <span class="' + zustand["zustand"] + '">(' + zustand["zustand"] + ")</span></h2>")

    if zustand["beschreibung"] != "":
        zeilen.append('<p class="leise">' + html.escape(zustand["beschreibung"]) + "</p>")

    hinweise = []
    if zustand["letzter_erfolg"] is None:
        hinweise.append("noch nie erfolgreich gelaufen")
    else:
        hinweise.append("letzter Erfolg: " + zustand["letzter_erfolg"].replace("T", " ")[:16])

    naechster = zustand.get("naechster_lauf")
    if naechster is None:
        naechster = planer.naechster_lauf(zustand["name"])
    if naechster is not None:
        hinweise.append("nächster Lauf: " + naechster.replace("T", " ")[:16])

    if zustand["fehler_in_folge"] > 0:
        hinweise.append(str(zustand["fehler_in_folge"]) + " Fehler in Folge")

    if zustand["ungelesen"] > 0:
        hinweise.append(str(zustand["ungelesen"]) + " ungelesen")

    zeilen.append('<p class="leise">' + html.escape(" · ".join(hinweise)) + "</p>")

    bericht = zustand["letzter_bericht"]
    if bericht is None:
        zeilen.append('<p class="leise">Noch kein Bericht.</p>')
    else:
        zeilen.append("<p><strong>" + html.escape(bericht["titel"]) + "</strong><br>")
        zeilen.append(html.escape(bericht["kurzfassung"]) + "</p>")

        if len(bericht["kennzahlen"]) > 0:
            zeilen.append("<table>")
            for kennzahl in bericht["kennzahlen"]:
                zeilen.append("<tr><th>" + html.escape(str(kennzahl["name"])) + "</th>")
                zeilen.append("<td>" + html.escape(str(kennzahl["wert"])) + "</td></tr>")
            zeilen.append("</table>")

        if len(bericht["eintraege"]) > 0:
            zeilen.append("<ul>")
            for eintrag in bericht["eintraege"]:
                stueck = html.escape(str(eintrag.get("titel", "")))
                text = str(eintrag.get("text", ""))
                if text != "":
                    stueck = stueck + ' <span class="leise">' + html.escape(text) + "</span>"

                link = str(eintrag.get("link", ""))
                if link != "":
                    stueck = stueck + ' <a href="' + html.escape(link) + '" rel="noreferrer">Quelle</a>'

                zeilen.append("<li>" + stueck + "</li>")
            zeilen.append("</ul>")

    zeilen.append("</div>")
    return "".join(zeilen)
