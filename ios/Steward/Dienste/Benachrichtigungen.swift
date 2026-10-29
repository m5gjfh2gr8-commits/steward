import Foundation
import UserNotifications

// Lokale Erinnerungen - laufen komplett am iPhone, kein Server-Push
// Echte Push-Notifications wuerden das bezahlte Apple Developer Program brauchen,
// lokale gehen mit der kostenlosen Apple-ID ohne Probleme

class Benachrichtigungen {
    static let geteilt = Benachrichtigungen()

    func erlaubnisHolen() async -> Bool {
        do {
            return try await UNUserNotificationCenter.current().requestAuthorization(options: [.alert, .sound, .badge])
        } catch {
            return false
        }
    }

    // Plant eine Erinnerung zu einem Termin/Todo
    // Eingabe: Kennung (damit man sie spaeter wieder loeschen kann), Text, Zeitpunkt
    func terminErinnerungPlanen(kennung: String, text: String, zeitpunkt: Date) {
        if zeitpunkt <= Date() {
            return
        }

        let inhalt = UNMutableNotificationContent()
        inhalt.title = "Steward"
        inhalt.body = text
        inhalt.sound = .default

        let teile = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: zeitpunkt)
        let ausloeser = UNCalendarNotificationTrigger(dateMatching: teile, repeats: false)

        let anfrage = UNNotificationRequest(identifier: kennung, content: inhalt, trigger: ausloeser)
        UNUserNotificationCenter.current().add(anfrage)
    }

    func erinnerungLoeschen(kennung: String) {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: [kennung])
    }

    // Trink-Erinnerung: meldet sich alle X Stunden, wird bei jedem Eintrag neu gesetzt
    func trinkErinnerungPlanen(inStunden: Int) {
        trinkErinnerungLoeschen()

        let inhalt = UNMutableNotificationContent()
        inhalt.title = "Trinken nicht vergessen"
        inhalt.body = "Seit \(inStunden) Stunden nichts eingetragen"
        inhalt.sound = .default

        let sekunden = Double(inStunden) * 3600.0
        let ausloeser = UNTimeIntervalNotificationTrigger(timeInterval: sekunden, repeats: false)

        let anfrage = UNNotificationRequest(identifier: "trinken", content: inhalt, trigger: ausloeser)
        UNUserNotificationCenter.current().add(anfrage)
    }

    func trinkErinnerungLoeschen() {
        UNUserNotificationCenter.current().removePendingNotificationRequests(withIdentifiers: ["trinken"])
    }

    // Wandelt den ISO-Text vom Backend in ein Date um
    func zeitpunktAusText(_ text: String?) -> Date? {
        guard let text = text else {
            return nil
        }

        let mitZone = ISO8601DateFormatter()
        mitZone.formatOptions = [.withInternetDateTime]
        if let ergebnis = mitZone.date(from: text) {
            return ergebnis
        }

        // das Backend schickt manchmal ohne Zeitzone, dann als lokale Zeit lesen
        let ohneZone = DateFormatter()
        ohneZone.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        ohneZone.timeZone = TimeZone.current
        return ohneZone.date(from: text)
    }
}
