"""Tests für das Tradingbot-Modul - liest nur die Statusdatei, kein Netz, kein Bot nötig"""

import json
from datetime import datetime, timedelta, timezone

import pytest

from app import planer
from app.bots import tradingbot, verzeichnis
from app.config import EINSTELLUNGEN
from app.dienste import berichte as berichte_dienst


def zeit_vor(minuten):
    zeitpunkt = datetime.now(timezone.utc) - timedelta(minutes=minuten)
    return zeitpunkt.strftime("%Y-%m-%dT%H:%M:%SZ")


def beispielstatus():
    """So sieht die Datei aus, die der Bot schreibt (bot/steward_status.py, Format 1)"""
    return {
        "format": 1,
        "erstellt": zeit_vor(5),
        "modus": "paper",
        "kapital_usd": 10000.0,
        "sleeve_wert_usd": 10240.5,
        "cash_usd": 3120.0,
        "investiert_usd": 6900.0,
        "gesamt_pct": 0.02405,
        "heute_pct": 0.003,
        "preise_ok": True,
        "pausiert": False,
        "pause_grund": "",
        "offene_positionen": [
            {"symbol": "ABC", "klasse": "stock", "stueck": 20, "einstieg": 13.0, "preis": 15.0,
             "preis_bekannt": True, "wert_usd": 300.0, "gewinn_usd": 40.0, "gewinn_pct": 0.1538,
             "stop": 11.76, "tranchen": 1, "tranchen_geplant": 3,
             "eroeffnet": "2026-11-18T15:00:00Z", "these": "Insider-Cluster + 8-K"},
            {"symbol": "XYZ", "klasse": "crypto", "stueck": 1250.5, "einstieg": 0.42, "preis": 0.42,
             "preis_bekannt": False, "wert_usd": 525.21, "gewinn_usd": 0.0, "gewinn_pct": 0.0,
             "stop": 0.0, "tranchen": 2, "tranchen_geplant": 3,
             "eroeffnet": "2026-11-17T06:00:00Z", "these": ""},
        ],
        "kandidaten": 3,
        "trades_heute": 2,
        "letzte_trades": [
            {"zeit": zeit_vor(30), "symbol": "ABC", "seite": "buy", "stueck": 20,
             "preis": 13.0, "grund": "tranche 1"},
            {"zeit": zeit_vor(60), "symbol": "OLD", "seite": "sell", "stueck": 5,
             "preis": 9.5, "grund": "trailing_stop"},
        ],
        "geschlossen": {"anzahl": 2, "gewinner": 1, "realisiert_usd": 15.0},
        "warnungen": [],
    }


@pytest.fixture
def statusdatei(tmp_path):
    """Legt eine Statusdatei an und biegt den Pfad dorthin um"""
    pfad = tmp_path / "steward_status.json"
    vorher = EINSTELLUNGEN.tradingbot_status_pfad
    EINSTELLUNGEN.tradingbot_status_pfad = str(pfad)

    def schreiben(status):
        pfad.write_text(json.dumps(status), encoding="utf-8")

    yield schreiben

    EINSTELLUNGEN.tradingbot_status_pfad = vorher


@pytest.fixture
def echter_tradingbot(testmodule):
    verzeichnis.MODULE.append(tradingbot.Tradingbot())
    yield
    verzeichnis.MODULE.pop()


def test_normaler_bericht(statusdatei):
    statusdatei(beispielstatus())

    bericht = tradingbot.Tradingbot().lauf()

    assert bericht.titel == "2 Trades heute"
    assert bericht.kurzfassung == "Sleeve +2,4 % · 2 offene Positionen"

    kennzahlen = {}
    for kennzahl in bericht.kennzahlen:
        kennzahlen[kennzahl["name"]] = kennzahl["wert"]
    assert kennzahlen["Sleeve-Wert"] == "10.240 $"
    assert kennzahlen["Heute"] == "+0,3 %"
    assert kennzahlen["Positionen"] == "2"

    titel = []
    for eintrag in bericht.eintraege:
        titel.append(eintrag["titel"])
    assert "ABC +15,4 %" in titel
    assert "Kauf ABC" in titel
    assert "Verkauf OLD" in titel
    assert "Bisher abgeschlossen: 2 Trades" in titel


def test_position_details(statusdatei):
    statusdatei(beispielstatus())
    bericht = tradingbot.Tradingbot().lauf()

    abc = bericht.eintraege[0]
    assert abc["text"].startswith("20 Stk · Einstieg 13,00 $ · jetzt 15,00 $ · Stop 11,76 $ · Tranche 1/3")
    assert abc["link"] == "https://finance.yahoo.com/quote/ABC"

    xyz = bericht.eintraege[1]
    assert "1.250,5 Stk" in xyz["text"]
    assert "Einstieg 0,4200 $" in xyz["text"]
    assert "aktueller Kurs fehlt" in xyz["text"]
    assert xyz["link"] == ""


def test_verkaufsgrund_auf_deutsch(statusdatei):
    statusdatei(beispielstatus())
    bericht = tradingbot.Tradingbot().lauf()

    for eintrag in bericht.eintraege:
        if eintrag["titel"] == "Verkauf OLD":
            assert "Trailing-Stop" in eintrag["text"]


def test_pause_steht_ganz_oben(statusdatei):
    status = beispielstatus()
    status["pausiert"] = True
    status["pause_grund"] = "Tagesverlust ueber 8 %"
    statusdatei(status)

    bericht = tradingbot.Tradingbot().lauf()

    assert bericht.titel == "Handel pausiert"
    assert bericht.eintraege[0]["titel"] == "Handel pausiert (Circuit Breaker)"
    assert "Tagesverlust" in bericht.eintraege[0]["text"]


def test_warnungen_im_titel(statusdatei):
    status = beispielstatus()
    status["warnungen"] = [{"zeit": zeit_vor(10), "stufe": "warning", "typ": "feed",
                            "text": "Alpaca-Clock nicht abrufbar"}]
    statusdatei(status)

    bericht = tradingbot.Tradingbot().lauf()

    assert bericht.titel == "1 Warnung"
    assert bericht.eintraege[0]["titel"] == "Warnung: feed"


def test_ohne_positionen(statusdatei):
    status = beispielstatus()
    status["offene_positionen"] = []
    status["trades_heute"] = 0
    status["letzte_trades"] = []
    status["geschlossen"] = {"anzahl": 0, "gewinner": 0, "realisiert_usd": 0}
    status["heute_pct"] = None
    statusdatei(status)

    bericht = tradingbot.Tradingbot().lauf()

    assert bericht.titel == "Alles ruhig"
    assert bericht.kurzfassung == "Sleeve +2,4 % · 0 offene Positionen"
    assert bericht.eintraege[0]["titel"] == "Noch keine offenen Positionen"
    assert "3 qualifiziert" in bericht.eintraege[0]["text"]


def test_fehlende_datei_ist_ein_fehler(statusdatei):
    with pytest.raises(RuntimeError) as fehler:
        tradingbot.Tradingbot().lauf()
    assert "läuft der Tradingbot" in str(fehler.value)


def test_alte_datei_ist_ein_fehler(statusdatei):
    status = beispielstatus()
    status["erstellt"] = zeit_vor(90)
    statusdatei(status)

    with pytest.raises(RuntimeError) as fehler:
        tradingbot.Tradingbot().lauf()
    assert "meldet sich seit 90 Minuten nicht mehr" in str(fehler.value)


def test_laeuft_ueber_den_planer(statusdatei, echter_tradingbot):
    statusdatei(beispielstatus())

    ergebnis = planer.lauf_ausfuehren("tradingbot")

    assert ergebnis["status"] == "ok"
    bericht = berichte_dienst.letzter_bericht("tradingbot")
    assert bericht["titel"] == "2 Trades heute"

    from app.dienste import kosten
    assert kosten.verbrauch_heute()["tokens_gesamt"] == 0


def test_fehler_landet_im_protokoll(statusdatei, echter_tradingbot):
    ergebnis = planer.lauf_ausfuehren("tradingbot")
    assert ergebnis["status"] != "ok"


def test_ist_im_verzeichnis_eingetragen():
    # die Tests tauschen das Verzeichnis gegen Testmodule, darum im Quelltext nachsehen
    import inspect
    assert "tradingbot.Tradingbot()" in inspect.getsource(verzeichnis)


def test_zahlenformat():
    assert tradingbot.deutsch(10240.5, 2) == "10.240,50"
    assert tradingbot.prozent(-0.0123) == "-1,2 %"
    assert tradingbot.prozent(0) == "0,0 %"
    assert tradingbot.zahl(20.0, 4) == "20"
    assert tradingbot.kurs(0.00123) == "0,0012 $"
