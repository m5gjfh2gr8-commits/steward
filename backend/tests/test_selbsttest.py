"""Tests für den Selbsttest, der vor dem ersten Start am Server läuft"""

import pytest

from app import selbsttest
from app.config import EINSTELLUNGEN


def test_python_version_ist_ok():
    assert "Python" in selbsttest.python_version()


def test_api_key_wird_als_fehlend_erkannt():
    vorher = EINSTELLUNGEN.api_key
    EINSTELLUNGEN.api_key = ""
    try:
        with pytest.raises(RuntimeError):
            selbsttest.api_key()
    finally:
        EINSTELLUNGEN.api_key = vorher


def test_zu_kurzer_api_key_wird_beanstandet():
    vorher = EINSTELLUNGEN.api_key
    EINSTELLUNGEN.api_key = "kurz"
    try:
        with pytest.raises(RuntimeError):
            selbsttest.api_key()
    finally:
        EINSTELLUNGEN.api_key = vorher


def test_datenbank_pruefung_meldet_wal():
    assert "WAL" in selbsttest.datenbank_schreibbar()


def test_kaputter_zeitplan_faellt_auf():
    from app.bots import verzeichnis
    from app.bots.basis import Modul

    class FalscherZeitplan(Modul):
        name = "falsch"
        anzeigename = "Falsch"
        zeitplan = {"stunde": 6}        # richtig waere "hour"

    verzeichnis.MODULE.append(FalscherZeitplan())
    try:
        with pytest.raises(Exception):
            selbsttest.module_und_zeitplaene()
    finally:
        verzeichnis.MODULE.pop()


def test_zeitplaene_der_echten_module_sind_gueltig():
    beschreibung = selbsttest.module_und_zeitplaene()
    assert "Module" in beschreibung


def test_trockenlauf_nimmt_ein_modul_ohne_modell():
    meldung = selbsttest.modullauf_trocken()
    assert "gelaufen" in meldung
