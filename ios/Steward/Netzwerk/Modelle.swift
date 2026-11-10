import Foundation

// Die Gegenstücke zu den JSON-Antworten vom Backend
// Der Decoder steht auf convertFromSnakeCase: aus "letzter_lauf" wird letzterLauf
// Felder, die die App nicht braucht, werden beim Lesen einfach ignoriert

struct Gesundheit: Codable {
    let status: String
    let zeit: String
    let version: String?
}

// --- Module und Berichte ---

struct Kennzahl: Codable, Hashable {
    let name: String
    let wert: String
}

struct Eintrag: Codable, Hashable {
    let titel: String
    let text: String?
    let link: String?
}

struct Bericht: Codable, Identifiable, Hashable {
    let id: Int
    let modul: String
    let zeitpunkt: String
    let titel: String
    let kurzfassung: String
    let kennzahlen: [Kennzahl]
    let eintraege: [Eintrag]

    var datum: Date? {
        return Zeitformat.datum(aus: zeitpunkt)
    }

    // Der Text, der beim Vorlesen gesprochen wird
    var vorlesetext: String {
        var teile: [String] = [titel]

        if kurzfassung.isEmpty == false {
            teile.append(kurzfassung)
        }
        for kennzahl in kennzahlen {
            teile.append(kennzahl.name + ": " + kennzahl.wert)
        }
        for eintrag in eintraege {
            var satz: String = eintrag.titel
            let text: String = eintrag.text ?? ""
            if text.isEmpty == false {
                satz = satz + ". " + text
            }
            teile.append(satz)
        }

        return teile.joined(separator: ". ")
    }
}

struct Lauf: Codable, Hashable {
    let id: Int
    let start: String
    let ende: String?
    let status: String
    let meldung: String?
}

struct ModulZustand: Codable, Identifiable {
    let name: String
    let anzeigename: String
    let beschreibung: String
    let symbol: String?
    let zustand: String
    let letzterLauf: Lauf?
    let letzterErfolg: String?
    let fehlerInFolge: Int
    let ungelesen: Int
    let letzterBericht: Bericht?
    let naechsterLauf: String?

    var id: String {
        return name
    }

    // "wackelig" = letzter Lauf gescheitert, "kaputt" = mehrmals hintereinander
    var hatFehler: Bool {
        if zustand == "wackelig" {
            return true
        }
        if zustand == "kaputt" {
            return true
        }
        return false
    }

    var symbolName: String {
        return symbol ?? "square.grid.2x2"
    }

    // Die graue zweite Zeile in der Modul-Liste
    var unterzeile: String {
        if hatFehler {
            if let lauf = letzterLauf, let start = Zeitformat.datum(aus: lauf.start) {
                return "Lauf fehlgeschlagen um " + Zeitformat.uhrzeit(start)
            }
            return "Letzter Lauf fehlgeschlagen"
        }

        guard let bericht = letzterBericht else {
            return "Noch kein Bericht"
        }
        if bericht.kurzfassung.isEmpty {
            return bericht.titel
        }
        return bericht.kurzfassung
    }
}

// Zur Navigation in ein Modul (nur der Name, die Daten holt die Detailansicht selbst)
struct ModulZiel: Hashable {
    let name: String
}

struct BerichteAntwort: Codable {
    let modul: String
    let gelesenBis: String?
    let berichte: [Bericht]
}

struct GelesenAnfrage: Encodable {
    let zeitpunkt: String?
}

struct AuffaelligesModul: Codable {
    let name: String
    let zustand: String
}

struct ZustandUeberblick: Codable {
    let planerLaeuft: Bool
    let anzahlModule: Int
    let auffaellig: [AuffaelligesModul]
    let ungelesenGesamt: Int
}

// --- Kosten ---

struct ModulVerbrauch: Codable, Identifiable {
    let modul: String
    let tokensEin: Int
    let tokensAus: Int

    var id: String {
        return modul
    }

    var tokensGesamt: Int {
        return tokensEin + tokensAus
    }
}

struct Verbrauch: Codable {
    let datum: String
    let tokensEin: Int
    let tokensAus: Int
    let tokensGesamt: Int
    let budgetProTag: Int
    let proModul: [ModulVerbrauch]
}

struct VerlaufTag: Codable {
    let datum: String
    let tokensEin: Int?
    let tokensAus: Int?
}

struct KostenAntwort: Codable {
    let heute: Verbrauch
    let verlauf: [VerlaufTag]
}

// --- Todos und Chat ---

struct Todo: Codable, Identifiable {
    let id: Int
    var inhalt: String
    var faelligAm: String?
    var erledigt: Int
    var quelle: String
    var erstelltAm: String

    var istErledigt: Bool {
        return erledigt == 1
    }
}

struct ChatAntwort: Codable {
    let art: String
    let antwort: String
}
