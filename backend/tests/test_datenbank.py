"""Tests für das Datenbank-Grundgerüst"""

from app.datenbank import verbindung


def test_alle_tabellen_sind_da():
    verb = verbindung()
    zeilen = verb.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    verb.close()

    namen = []
    for zeile in zeilen:
        namen.append(zeile["name"])

    erwartet = ["todos", "berichte", "modul_laeufe", "kosten_log", "gelesen_bis", "interessen", "news_feedback"]
    for tabelle in erwartet:
        assert tabelle in namen


def test_wal_ist_eingeschaltet():
    # Ohne WAL wuerde ein schreibendes Modul die Anfragen aus der App blockieren
    verb = verbindung()
    modus = verb.execute("PRAGMA journal_mode").fetchone()[0]
    verb.close()

    assert modus.lower() == "wal"


def test_vorbereiten_ist_wiederholbar():
    from app import datenbank

    datenbank.vorbereiten()
    datenbank.vorbereiten()

    verb = verbindung()
    anzahl = verb.execute("SELECT COUNT(*) FROM todos").fetchone()[0]
    verb.close()

    assert anzahl == 0
