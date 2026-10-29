"""
Token-Zählung und Kostenbremse

Zwei Grenzen:
  pro Lauf  - ein einzelnes Modul kann sich nicht in einer Schleife hochschaukeln
  pro Tag   - über alle Module zusammen, als letzte Reißleine

Wird eine Grenze erreicht, wird der nächste Modellaufruf abgelehnt statt still
teurer zu werden. Die Console von Anthropic hat auch ein Limit, aber das greift
erst am Monatsende und sagt nicht, welches Modul schuld war

Welches Modul gerade dran ist, steht in einer thread-lokalen Variable: der Planer
läuft in einem eigenen Thread, Anfragen aus der App in anderen - eine normale
globale Variable würde die Zuordnung vermischen
"""

import threading

from app.config import EINSTELLUNGEN
from app.datenbank import verbindung
from app.zeit import heute_text

_oertlich = threading.local()


class BudgetErschoepft(Exception):
    pass


def aktuelles_modul_setzen(name):
    _oertlich.modul = name
    _oertlich.tokens_ein_lauf = 0
    _oertlich.tokens_aus_lauf = 0


def aktuelles_modul():
    """Ausgabe: Name des Moduls, in dessen Lauf wir gerade sind, sonst direkt"""
    name = getattr(_oertlich, "modul", None)
    if name is None:
        return "direkt"
    return name


def tokens_im_lauf():
    """Ausgabe: (tokens_ein, tokens_aus) seit dem Beginn des aktuellen Laufs"""
    ein = getattr(_oertlich, "tokens_ein_lauf", 0)
    aus = getattr(_oertlich, "tokens_aus_lauf", 0)
    return ein, aus


def tokens_im_lauf_gesamt():
    ein, aus = tokens_im_lauf()
    return ein + aus


def aktuelles_modul_loeschen():
    _oertlich.modul = None
    _oertlich.tokens_ein_lauf = 0
    _oertlich.tokens_aus_lauf = 0


def budget_pruefen():
    """
    Wird vor jedem Modellaufruf aufgerufen
    Wirft BudgetErschoepft wenn eine der beiden Grenzen erreicht ist
    """
    if tokens_im_lauf_gesamt() >= EINSTELLUNGEN.tokenbudget_pro_lauf:
        raise BudgetErschoepft(
            "Token-Budget für diesen Lauf aufgebraucht ("
            + str(EINSTELLUNGEN.tokenbudget_pro_lauf) + ")"
        )

    verbraucht = verbrauch_heute()["tokens_gesamt"]
    if verbraucht >= EINSTELLUNGEN.tokenbudget_pro_tag:
        raise BudgetErschoepft(
            "Token-Budget für heute aufgebraucht ("
            + str(EINSTELLUNGEN.tokenbudget_pro_tag) + ")"
        )


def verbrauch_buchen(tokens_ein, tokens_aus):
    """Nach jedem Modellaufruf: schreibt die Tagessumme mit und zählt den Lauf mit"""
    modul = aktuelles_modul()
    datum = heute_text()

    verb = verbindung()
    verb.execute(
        """INSERT INTO kosten_log (datum, modul, tokens_ein, tokens_aus)
           VALUES (?, ?, ?, ?)
           ON CONFLICT (datum, modul) DO UPDATE SET
             tokens_ein = tokens_ein + ?,
             tokens_aus = tokens_aus + ?""",
        (datum, modul, tokens_ein, tokens_aus, tokens_ein, tokens_aus),
    )
    verb.commit()
    verb.close()

    ein_bisher, aus_bisher = tokens_im_lauf()
    _oertlich.tokens_ein_lauf = ein_bisher + tokens_ein
    _oertlich.tokens_aus_lauf = aus_bisher + tokens_aus


def verbrauch_heute():
    """
    Ausgabe: {"datum":..., "tokens_ein":..., "tokens_aus":..., "tokens_gesamt":...,
              "budget_pro_tag":..., "pro_modul": [{"modul":..., "tokens_ein":..., "tokens_aus":...}]}
    """
    datum = heute_text()

    verb = verbindung()
    zeilen = verb.execute(
        "SELECT modul, tokens_ein, tokens_aus FROM kosten_log WHERE datum = ? ORDER BY modul",
        (datum,),
    ).fetchall()
    verb.close()

    summe_ein = 0
    summe_aus = 0
    pro_modul = []

    for zeile in zeilen:
        summe_ein = summe_ein + zeile["tokens_ein"]
        summe_aus = summe_aus + zeile["tokens_aus"]
        pro_modul.append(dict(zeile))

    return {
        "datum": datum,
        "tokens_ein": summe_ein,
        "tokens_aus": summe_aus,
        "tokens_gesamt": summe_ein + summe_aus,
        "budget_pro_tag": EINSTELLUNGEN.tokenbudget_pro_tag,
        "pro_modul": pro_modul,
    }


def verlauf(tage=14):
    ab_datum = _tag_vor(tage)

    verb = verbindung()
    zeilen = verb.execute(
        """SELECT datum, SUM(tokens_ein) AS tokens_ein, SUM(tokens_aus) AS tokens_aus
           FROM kosten_log WHERE datum >= ?
           GROUP BY datum ORDER BY datum DESC""",
        (ab_datum,),
    ).fetchall()
    verb.close()

    ergebnis = []
    for zeile in zeilen:
        ergebnis.append(dict(zeile))
    return ergebnis


def _tag_vor(tage):
    from app.zeit import tag_vor_x_tagen_text
    return tag_vor_x_tagen_text(tage)
