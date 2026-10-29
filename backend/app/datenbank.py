"""
SQLite-Zugriff für Steward

Kein ORM, nur sqlite3 aus der Standardbibliothek
Aufruf: datenbank.vorbereiten() einmal beim Start, danach verbindung() pro Zugriff

WAL ist eingeschaltet, weil der Planer schreibt während die API liest - ohne WAL
würde ein laufendes Modul die App-Anfragen blockieren
"""

import os
import sqlite3

from app.config import EINSTELLUNGEN

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inhalt TEXT NOT NULL,
    faellig_am TEXT,
    erledigt INTEGER NOT NULL DEFAULT 0,
    quelle TEXT NOT NULL DEFAULT 'text',
    erstellt_am TEXT NOT NULL
);

-- Was ein Modul produziert hat
-- kennzahlen und eintraege liegen als JSON drin, damit die App jeden Bericht
-- gleich darstellen kann, egal von welchem Modul er kommt
CREATE TABLE IF NOT EXISTS berichte (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modul TEXT NOT NULL,
    zeitpunkt TEXT NOT NULL,
    titel TEXT NOT NULL,
    kurzfassung TEXT NOT NULL DEFAULT '',
    kennzahlen_json TEXT NOT NULL DEFAULT '[]',
    eintraege_json TEXT NOT NULL DEFAULT '[]'
);

CREATE INDEX IF NOT EXISTS idx_berichte_modul ON berichte (modul, zeitpunkt DESC);

-- Jeder Modul-Lauf, auch die gescheiterten
-- Das ist die Überwachung: wer lebt noch, wer scheitert, was hat es gekostet
CREATE TABLE IF NOT EXISTS modul_laeufe (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    modul TEXT NOT NULL,
    start TEXT NOT NULL,
    ende TEXT,
    status TEXT NOT NULL,
    meldung TEXT NOT NULL DEFAULT '',
    tokens_ein INTEGER NOT NULL DEFAULT 0,
    tokens_aus INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_laeufe_modul ON modul_laeufe (modul, start DESC);

-- Tagessummen der Token, pro Modul
-- Daraus kommt die Kostenbremse
CREATE TABLE IF NOT EXISTS kosten_log (
    datum TEXT NOT NULL,
    modul TEXT NOT NULL,
    tokens_ein INTEGER NOT NULL DEFAULT 0,
    tokens_aus INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (datum, modul)
);

-- Bis wohin ich die Berichte eines Moduls gelesen habe
-- Liegt am Server, damit Handy und PC denselben Stand sehen
CREATE TABLE IF NOT EXISTS gelesen_bis (
    modul TEXT PRIMARY KEY,
    zeitpunkt TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS interessen (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stichwort TEXT NOT NULL UNIQUE,
    aktiv INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS news_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meldung_hash TEXT NOT NULL,
    titel TEXT NOT NULL,
    zeitpunkt TEXT NOT NULL,
    bewertung TEXT NOT NULL
);
"""


def verbindung():
    ordner = os.path.dirname(os.path.abspath(EINSTELLUNGEN.db_pfad))
    if ordner != "" and not os.path.exists(ordner):
        os.makedirs(ordner, exist_ok=True)

    verb = sqlite3.connect(EINSTELLUNGEN.db_pfad, timeout=15)
    verb.row_factory = sqlite3.Row
    verb.execute("PRAGMA journal_mode = WAL")
    verb.execute("PRAGMA busy_timeout = 15000")
    verb.execute("PRAGMA foreign_keys = ON")
    return verb


def vorbereiten():
    """Legt alle Tabellen an falls sie fehlen"""
    verb = verbindung()
    verb.executescript(SCHEMA)
    verb.commit()
    verb.close()


def zeilen_zu_dicts(zeilen):
    ergebnis = []
    for zeile in zeilen:
        ergebnis.append(dict(zeile))
    return ergebnis
