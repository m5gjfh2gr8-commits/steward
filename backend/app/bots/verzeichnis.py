"""
Verzeichnis aller Module

Hier und nur hier wird ein neues Modul eingetragen. Der Planer, die API und die App
holen sich die Liste von hier, es gibt also keine zweite Stelle zum Nachpflegen
"""

from app.bots import systemcheck

MODULE = [
    systemcheck.SystemCheck(),
]


def alle():
    return MODULE


def nach_name(name):
    for modul in MODULE:
        if modul.name == name:
            return modul
    return None


def namen():
    gesammelt = []
    for modul in MODULE:
        gesammelt.append(modul.name)
    return gesammelt
