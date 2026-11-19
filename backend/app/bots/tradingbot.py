"""
Modul: Tradingbot

Zeigt, was der Tradingbot gerade macht (Paper-Trading, eigenes Projekt am selben Server)
Der Bot schreibt alle 15 Minuten eine Statusdatei (data/steward_status.json),
dieses Modul liest sie nur - Steward greift nie in den Handel ein

Braucht kein Modell und keine Keys, kostet also nichts
"""

import json
import os

from app.bots.basis import Bericht, Modul
from app.config import EINSTELLUNGEN
from app.zeit import datum_aus_text, stunden_seit, zone

# ab wie vielen Minuten ohne neue Statusdatei der Bot als "meldet sich nicht" gilt
# der Bot schreibt alle 15 Minuten, 45 lässt Luft für zwei verpasste Runden
GRENZE_MINUTEN = 45

# wie viele Positionen und Trades höchstens im Bericht stehen
MAX_POSITIONEN = 20
MAX_TRADES = 5

# Wörter für die Gründe, die der Bot in die Orders schreibt
GRUENDE = {
    "stop_loss": "Stop-Loss",
    "trailing_stop": "Trailing-Stop",
    "thesis_broken": "These kaputt",
    "manual": "von Hand",
}


class Tradingbot(Modul):
    name = "tradingbot"
    anzeigename = "Tradingbot"
    beschreibung = "Paper-Trading: Sleeve-Wert, offene Positionen und Trades des Tradingbots"
    # täglich in der Früh (Krypto über Nacht) und rund um die US-Börse (15:30-22:00 bei uns)
    zeitplan = {"hour": "8,16,18,20,22", "minute": 20}
    symbol = "chart.line.uptrend.xyaxis"
    braucht_modell = False

    def lauf(self):
        status = statusdatei_lesen()
        return bericht_bauen(status)


def statusdatei_lesen():
    """
    Ausgabe: der Inhalt der Statusdatei als Dict
    Wirft einen Fehler, wenn die Datei fehlt oder zu alt ist - dann zeigt die App
    das Modul rot an und der Systemcheck merkt es
    """
    pfad = EINSTELLUNGEN.tradingbot_status_pfad

    if not os.path.exists(pfad):
        raise RuntimeError("Keine Statusdatei unter " + pfad + " - läuft der Tradingbot?")

    datei = open(pfad, "r", encoding="utf-8")
    inhalt = datei.read()
    datei.close()

    status = json.loads(inhalt)

    stunden = stunden_seit(status.get("erstellt"))
    if stunden is None:
        raise RuntimeError("Statusdatei ohne lesbaren Zeitstempel")

    minuten = int(stunden * 60)
    if minuten > GRENZE_MINUTEN:
        raise RuntimeError("Tradingbot meldet sich seit " + dauer_text(minuten) + " nicht mehr")

    return status


def bericht_bauen(status):
    """Eingabe: Dict aus der Statusdatei. Ausgabe: ein Bericht"""
    positionen = status.get("offene_positionen", [])
    warnungen = status.get("warnungen", [])
    trades_heute = status.get("trades_heute", 0)

    bericht = Bericht(titel=titel_waehlen(status, warnungen, trades_heute))
    bericht.kurzfassung = ("Sleeve " + prozent(status.get("gesamt_pct", 0)) + " · "
                           + anzahl_text(len(positionen), "offene Position", "offene Positionen"))

    bericht.kennzahl_dazu("Sleeve-Wert", geld(status.get("sleeve_wert_usd", 0), 0))
    bericht.kennzahl_dazu("Gesamt", prozent(status.get("gesamt_pct", 0)))
    if status.get("heute_pct") is None:
        bericht.kennzahl_dazu("Heute", "–")
    else:
        bericht.kennzahl_dazu("Heute", prozent(status.get("heute_pct")))
    bericht.kennzahl_dazu("Positionen", len(positionen))
    bericht.kennzahl_dazu("Cash", geld(status.get("cash_usd", 0), 0))
    bericht.kennzahl_dazu("Trades heute", trades_heute)

    # Wichtiges zuerst: Pause, fehlende Kurse, Warnungen
    if status.get("pausiert"):
        grund = status.get("pause_grund", "")
        if grund == "":
            grund = "kein Grund angegeben"
        bericht.eintrag_dazu(titel="Handel pausiert (Circuit Breaker)",
                             text=grund + ". Weiter geht es erst nach \"resume\" am Server.")

    if not status.get("preise_ok", True):
        bericht.eintrag_dazu(titel="Kurse gerade nicht abrufbar",
                             text="Die Positionen sind zum Einstiegspreis bewertet.")

    for warnung in warnungen:
        bericht.eintrag_dazu(titel="Warnung: " + warnung.get("typ", ""),
                             text=uhrzeit(warnung.get("zeit")) + " · " + warnung.get("text", ""))

    # offene Positionen
    if len(positionen) == 0:
        kandidaten = status.get("kandidaten", 0)
        bericht.eintrag_dazu(titel="Noch keine offenen Positionen",
                             text="Der Bot wartet auf passende Kandidaten ("
                                  + str(kandidaten) + " qualifiziert, warten auf das Timing).")

    for position in positionen[:MAX_POSITIONEN]:
        bericht.eintrag_dazu(titel=position_titel(position),
                             text=position_text(position),
                             link=position_link(position))

    # letzte Trades
    for trade in status.get("letzte_trades", [])[:MAX_TRADES]:
        bericht.eintrag_dazu(titel=trade_titel(trade), text=trade_text(trade))

    geschlossen = status.get("geschlossen", {})
    if geschlossen.get("anzahl", 0) > 0:
        bericht.eintrag_dazu(
            titel="Bisher abgeschlossen: " + anzahl_text(geschlossen["anzahl"], "Trade", "Trades"),
            text=str(geschlossen.get("gewinner", 0)) + " mit Gewinn · realisiert "
                 + geld(geschlossen.get("realisiert_usd", 0), 2, mit_vorzeichen=True))

    return bericht


def titel_waehlen(status, warnungen, trades_heute):
    """Die Überschrift sagt, was seit dem letzten Mal los war"""
    if status.get("pausiert"):
        return "Handel pausiert"
    if len(warnungen) > 0:
        return anzahl_text(len(warnungen), "Warnung", "Warnungen")
    if trades_heute > 0:
        return anzahl_text(trades_heute, "Trade heute", "Trades heute")
    return "Alles ruhig"


def position_titel(position):
    return position.get("symbol", "?") + " " + prozent(position.get("gewinn_pct", 0))


def position_text(position):
    teile = []
    teile.append(zahl(position.get("stueck", 0), 4) + " Stk")
    teile.append("Einstieg " + kurs(position.get("einstieg", 0)))

    if position.get("preis_bekannt", True):
        teile.append("jetzt " + kurs(position.get("preis", 0)))
    else:
        teile.append("aktueller Kurs fehlt")

    if position.get("stop", 0) > 0:
        teile.append("Stop " + kurs(position.get("stop", 0)))

    teile.append("Tranche " + str(position.get("tranchen", 0)) + "/" + str(position.get("tranchen_geplant", 0)))

    text = " · ".join(teile)
    these = position.get("these", "")
    if these != "":
        text = text + "\n" + these
    return text


def position_link(position):
    """Aktien führen zur Kursseite, bei Krypto gibt es keinen eindeutigen Link"""
    if position.get("klasse") == "stock":
        return "https://finance.yahoo.com/quote/" + position.get("symbol", "")
    return ""


def trade_titel(trade):
    if trade.get("seite") == "buy":
        art = "Kauf"
    else:
        art = "Verkauf"
    return art + " " + trade.get("symbol", "?")


def trade_text(trade):
    grund = trade.get("grund", "")
    grund = GRUENDE.get(grund, grund)

    text = zahl(trade.get("stueck", 0), 4) + " Stk zu " + kurs(trade.get("preis", 0))
    if grund != "":
        text = text + " · " + grund
    return text + " · " + uhrzeit(trade.get("zeit"))


# ---------- Zahlen auf Österreichisch: 10.240,50 ----------

def zahl(wert, stellen):
    """Zahl mit Tausenderpunkt und Komma, unnötige Nullen hinten weg (bei Stückzahlen)"""
    text = deutsch(wert, stellen)
    if "," in text:
        text = text.rstrip("0").rstrip(",")
    return text


def deutsch(wert, stellen):
    """Eingabe: Zahl, Nachkommastellen. Ausgabe: z.B. 10.240,50"""
    englisch = format(float(wert), ",." + str(stellen) + "f")    # 10,240.50
    return englisch.replace(",", "_").replace(".", ",").replace("_", ".")


def geld(wert, stellen, mit_vorzeichen=False):
    text = deutsch(wert, stellen) + " $"
    if mit_vorzeichen and float(wert) > 0:
        text = "+" + text
    return text


def kurs(wert):
    """Kurse unter 1 $ (Krypto, Pennystocks) brauchen mehr Stellen"""
    if abs(float(wert)) < 1:
        return deutsch(wert, 4) + " $"
    return deutsch(wert, 2) + " $"


def prozent(anteil):
    """Eingabe: 0.024. Ausgabe: +2,4 %"""
    wert = float(anteil) * 100
    text = deutsch(wert, 1) + " %"
    if wert > 0:
        text = "+" + text
    return text


def anzahl_text(anzahl, einzahl, mehrzahl):
    if anzahl == 1:
        return "1 " + einzahl
    return str(anzahl) + " " + mehrzahl


def uhrzeit(zeitpunkt_text):
    """UTC-Zeitstempel vom Bot in lokale Zeit, z.B. 19.11. 15:32"""
    wert = datum_aus_text(zeitpunkt_text)
    if wert is None:
        return ""
    lokal = wert.astimezone(zone())
    return lokal.strftime("%d.%m. %H:%M")


def dauer_text(minuten):
    if minuten < 120:
        return str(minuten) + " Minuten"
    return str(minuten // 60) + " Stunden"
