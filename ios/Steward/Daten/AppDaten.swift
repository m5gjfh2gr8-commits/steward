import Foundation
import SwiftUI

// Was mehrere Bildschirme gemeinsam brauchen: die Modul-Liste, ob der Server
// erreichbar ist, und welcher Tab gerade offen ist

enum Bereich: Hashable {
    case module
    case todos
    case steward
    case kosten
    case einstellungen
}

@MainActor
class AppDaten: ObservableObject {
    @Published var module: [ModulZustand] = []
    @Published var laedt: Bool = false
    @Published var offline: Bool = false
    @Published var fehlertext: String = ""
    @Published var zuletztAktualisiert: Date?
    @Published var ausgewaehlterBereich: Bereich = Bereich.module

    func moduleLaden() async {
        laedt = true

        do {
            let neu: [ModulZustand] = try await ApiClient.geteilt.holen("/module")
            module = neu
            offline = false
            fehlertext = ""
            zuletztAktualisiert = Date()
            await Benachrichtigungen.geteilt.zaehlerSetzen(ungelesenGesamt)
            UserDefaults.standard.set(ungelesenGesamt, forKey: "zuletztBekanntUngelesen")
        } catch let fehler as ApiFehler {
            // Die zuletzt geladenen Module bleiben stehen, nur der Hinweis kommt dazu
            offline = fehler.istOffline
            fehlertext = fehler.localizedDescription
        } catch {
            fehlertext = error.localizedDescription
        }

        laedt = false
    }

    // Die Detailansicht meldet hier, wenn Berichte gelesen wurden
    func gelesenGemeldet() async {
        await moduleLaden()
    }

    func modul(mitName name: String) -> ModulZustand? {
        for modul in module {
            if modul.name == name {
                return modul
            }
        }
        return nil
    }

    var ungelesenGesamt: Int {
        var summe: Int = 0
        for modul in module {
            summe = summe + modul.ungelesen
        }
        return summe
    }

    var anzahlFehler: Int {
        var anzahl: Int = 0
        for modul in module {
            if modul.hatFehler {
                anzahl = anzahl + 1
            }
        }
        return anzahl
    }

    // Module mit Fehler zuerst, sonst die Reihenfolge vom Server
    var sortierteModule: [ModulZustand] {
        var mitFehler: [ModulZustand] = []
        var ohneFehler: [ModulZustand] = []
        for modul in module {
            if modul.hatFehler {
                mitFehler.append(modul)
            } else {
                ohneFehler.append(modul)
            }
        }
        return mitFehler + ohneFehler
    }

    // "Alles ruhig", "4 neue Berichte" oder "1 Fehler · 4 neue Berichte"
    var statuszeile: String {
        var teile: [String] = []

        if anzahlFehler == 1 {
            teile.append("1 Fehler")
        } else if anzahlFehler > 1 {
            teile.append(String(anzahlFehler) + " Fehler")
        }

        let neu: Int = ungelesenGesamt
        if neu == 1 {
            teile.append("1 neuer Bericht")
        } else if neu > 1 {
            teile.append(String(neu) + " neue Berichte")
        }

        if teile.isEmpty {
            return "Alles ruhig"
        }
        return teile.joined(separator: " · ")
    }

    func anzeigename(fuerModul name: String) -> String {
        if let gefunden = modul(mitName: name) {
            return gefunden.anzeigename
        }
        return name
    }
}
