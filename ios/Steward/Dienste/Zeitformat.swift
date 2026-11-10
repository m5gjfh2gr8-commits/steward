import Foundation

// Zeitangaben vom Server lesen und so anzeigen, wie iOS es auch tut
// Der Server schickt ISO-Text, z.B. "2026-10-29T17:36:33+01:00"

enum Zeitformat {
    private static let mitZone: ISO8601DateFormatter = {
        let formatierer: ISO8601DateFormatter = ISO8601DateFormatter()
        formatierer.formatOptions = [.withInternetDateTime]
        return formatierer
    }()

    private static let mitZoneUndBruchteil: ISO8601DateFormatter = {
        let formatierer: ISO8601DateFormatter = ISO8601DateFormatter()
        formatierer.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return formatierer
    }()

    // Fälligkeiten von Todos kommen manchmal ohne Zeitzone - dann als lokale Zeit lesen
    private static let ohneZone: DateFormatter = {
        let formatierer: DateFormatter = DateFormatter()
        formatierer.locale = Locale(identifier: "en_US_POSIX")
        formatierer.dateFormat = "yyyy-MM-dd'T'HH:mm:ss"
        formatierer.timeZone = TimeZone.current
        return formatierer
    }()

    private static let ohneZoneKurz: DateFormatter = {
        let formatierer: DateFormatter = DateFormatter()
        formatierer.locale = Locale(identifier: "en_US_POSIX")
        formatierer.dateFormat = "yyyy-MM-dd'T'HH:mm"
        formatierer.timeZone = TimeZone.current
        return formatierer
    }()

    private static let nurDatum: DateFormatter = {
        let formatierer: DateFormatter = DateFormatter()
        formatierer.locale = Locale(identifier: "en_US_POSIX")
        formatierer.dateFormat = "yyyy-MM-dd"
        formatierer.timeZone = TimeZone.current
        return formatierer
    }()

    static func datum(aus text: String?) -> Date? {
        guard let text = text else {
            return nil
        }
        if let ergebnis = mitZone.date(from: text) {
            return ergebnis
        }
        if let ergebnis = mitZoneUndBruchteil.date(from: text) {
            return ergebnis
        }
        if let ergebnis = ohneZone.date(from: text) {
            return ergebnis
        }
        if let ergebnis = ohneZoneKurz.date(from: text) {
            return ergebnis
        }
        return nurDatum.date(from: text)
    }

    static func tagText(_ datum: Date) -> String {
        return nurDatum.string(from: datum)
    }

    static func uhrzeit(_ datum: Date) -> String {
        return datum.formatted(date: .omitted, time: .shortened)
    }

    // Für Listen, so knapp wie in Mail: "05:30", "Gestern", "So.", "12.10.26"
    static func knapp(_ datum: Date) -> String {
        let kalender: Calendar = Calendar.current

        if kalender.isDateInToday(datum) {
            return uhrzeit(datum)
        }
        if kalender.isDateInYesterday(datum) {
            return "Gestern"
        }

        let tageHer: Int = kalender.dateComponents([.day], from: kalender.startOfDay(for: datum), to: kalender.startOfDay(for: Date())).day ?? 99
        if tageHer < 7 {
            return datum.formatted(.dateTime.weekday(.abbreviated))
        }
        return datum.formatted(date: .numeric, time: .omitted)
    }

    // Mit Tag davor: "Heute, 05:30", "Morgen, 05:30", "12.10.26, 05:30"
    static func mitTag(_ datum: Date) -> String {
        let kalender: Calendar = Calendar.current
        let zeit: String = uhrzeit(datum)

        if kalender.isDateInToday(datum) {
            return "Heute, " + zeit
        }
        if kalender.isDateInYesterday(datum) {
            return "Gestern, " + zeit
        }
        if kalender.isDateInTomorrow(datum) {
            return "Morgen, " + zeit
        }
        return datum.formatted(date: .numeric, time: .omitted) + ", " + zeit
    }

    static func mitTag(text: String?) -> String {
        guard let datum = datum(aus: text) else {
            return "–"
        }
        return mitTag(datum)
    }
}
