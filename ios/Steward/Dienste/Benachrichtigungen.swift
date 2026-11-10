import BackgroundTasks
import Foundation
import UserNotifications

// Lokale Hinweise und der Zähler am App-Symbol
// Echte Push-Nachrichten bräuchten den bezahlten Apple-Developer-Account - deshalb schaut
// die App ab und zu im Hintergrund selbst nach. Wann genau, entscheidet iOS.

class Benachrichtigungen {
    static let geteilt: Benachrichtigungen = Benachrichtigungen()

    func erlaubnisHolen() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
        } catch {
            return false
        }
    }

    // Setzt den roten Zähler am App-Symbol (0 = verschwindet)
    func zaehlerSetzen(_ anzahl: Int) async {
        var wert: Int = anzahl
        if Einstellungen.geteilt.zaehlerAmSymbol == false {
            wert = 0
        }

        do {
            try await UNUserNotificationCenter.current().setBadgeCount(wert)
        } catch {
            // ohne Erlaubnis geht es halt nicht - kein Grund, die App zu stören
        }
    }

    func hinweisSchicken(titel: String, text: String) {
        let inhalt: UNMutableNotificationContent = UNMutableNotificationContent()
        inhalt.title = titel
        inhalt.body = text
        inhalt.sound = .default

        let anfrage: UNNotificationRequest = UNNotificationRequest(identifier: UUID().uuidString, content: inhalt, trigger: nil)
        UNUserNotificationCenter.current().add(anfrage)
    }
}

// Der Blick im Hintergrund: Ungelesen-Zahl holen, Zähler setzen, bei Bedarf einen Hinweis zeigen
enum Hintergrund {
    static let kennung: String = "at.lorenz.steward.aktualisieren"

    static func naechstenBlickPlanen() {
        let anfrage: BGAppRefreshTaskRequest = BGAppRefreshTaskRequest(identifier: kennung)
        // frühestens in 30 Minuten - iOS macht daraus oft deutlich mehr
        anfrage.earliestBeginDate = Date(timeIntervalSinceNow: 30 * 60)

        do {
            try BGTaskScheduler.shared.submit(anfrage)
        } catch {
            // passiert z.B. im Simulator oder wenn Hintergrund-Aktualisierung aus ist
        }
    }

    static func ausfuehren() async {
        // Gleich den nächsten Blick anmelden, sonst war es der letzte
        naechstenBlickPlanen()

        let ueberblick: ZustandUeberblick
        do {
            ueberblick = try await ApiClient.geteilt.holen("/module/zustand")
        } catch {
            return
        }

        await Benachrichtigungen.geteilt.zaehlerSetzen(ueberblick.ungelesenGesamt)

        let speicher: UserDefaults = UserDefaults.standard
        let bisherBekannt: Int = speicher.integer(forKey: "zuletztBekanntUngelesen")
        speicher.set(ueberblick.ungelesenGesamt, forKey: "zuletztBekanntUngelesen")

        if Einstellungen.geteilt.hintergrundHinweise == false {
            return
        }

        if ueberblick.ungelesenGesamt > bisherBekannt {
            let neu: Int = ueberblick.ungelesenGesamt - bisherBekannt
            var text: String = String(neu) + " neue Berichte"
            if neu == 1 {
                text = "1 neuer Bericht"
            }
            Benachrichtigungen.geteilt.hinweisSchicken(titel: "Steward", text: text)
        }

        if ueberblick.auffaellig.isEmpty == false {
            var namen: [String] = []
            for eintrag in ueberblick.auffaellig {
                namen.append(eintrag.name)
            }
            let bisherAuffaellig: String = speicher.string(forKey: "zuletztAuffaellig") ?? ""
            let jetztAuffaellig: String = namen.joined(separator: ", ")
            if jetztAuffaellig != bisherAuffaellig {
                Benachrichtigungen.geteilt.hinweisSchicken(titel: "Steward: Modul mit Fehler", text: jetztAuffaellig)
            }
            speicher.set(jetztAuffaellig, forKey: "zuletztAuffaellig")
        } else {
            speicher.set("", forKey: "zuletztAuffaellig")
        }
    }
}
