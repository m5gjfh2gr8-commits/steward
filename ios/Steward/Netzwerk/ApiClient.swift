import Foundation

// Sprechen mit dem Backend am Heimserver
// Server-Adresse und API-Key kommen aus den Einstellungen, erreichbar ist der Server
// nur wenn Tailscale am iPhone aktiv ist

enum ApiFehler: LocalizedError {
    case keineAdresse
    case ungueltigeAdresse
    case falscherKey
    case serverFehler(Int, String)
    case antwortUnlesbar

    var errorDescription: String? {
        switch self {
        case .keineAdresse:
            return "Keine Server-Adresse in den Einstellungen hinterlegt"
        case .ungueltigeAdresse:
            return "Die Server-Adresse schaut nicht wie eine URL aus"
        case .falscherKey:
            return "Der API-Key passt nicht zum Server"
        case .serverFehler(let code, let text):
            return "Server meldet Fehler \(code): \(text)"
        case .antwortUnlesbar:
            return "Antwort vom Server war nicht lesbar"
        }
    }
}

class ApiClient {
    static let geteilt = ApiClient()

    private let dekoder: JSONDecoder
    private let enkoder: JSONEncoder

    init() {
        dekoder = JSONDecoder()
        dekoder.keyDecodingStrategy = .convertFromSnakeCase

        enkoder = JSONEncoder()
        enkoder.keyEncodingStrategy = .convertToSnakeCase
    }

    private func anfrageBauen(pfad: String, methode: String) throws -> URLRequest {
        let adresse = Einstellungen.geteilt.serverAdresse
        if adresse.isEmpty {
            throw ApiFehler.keineAdresse
        }

        var basis = adresse
        if basis.hasSuffix("/") {
            basis = String(basis.dropLast())
        }
        let vollerPfad = basis + pfad

        guard let url = URL(string: vollerPfad) else {
            throw ApiFehler.ungueltigeAdresse
        }

        var anfrage = URLRequest(url: url)
        anfrage.httpMethod = methode
        anfrage.setValue(Einstellungen.geteilt.apiKey, forHTTPHeaderField: "X-API-Key")
        anfrage.setValue("application/json", forHTTPHeaderField: "Content-Type")
        anfrage.timeoutInterval = 120
        return anfrage
    }

    private func antwortPruefen(daten: Data, antwort: URLResponse) throws {
        guard let http = antwort as? HTTPURLResponse else {
            throw ApiFehler.antwortUnlesbar
        }

        if http.statusCode == 401 {
            throw ApiFehler.falscherKey
        }

        if http.statusCode >= 400 {
            let text = String(data: daten, encoding: .utf8) ?? ""
            throw ApiFehler.serverFehler(http.statusCode, text)
        }
    }

    // Holt etwas vom Server
    func holen<T: Decodable>(_ pfad: String) async throws -> T {
        let anfrage = try anfrageBauen(pfad: pfad, methode: "GET")
        let (daten, antwort) = try await URLSession.shared.data(for: anfrage)
        try antwortPruefen(daten: daten, antwort: antwort)

        do {
            return try dekoder.decode(T.self, from: daten)
        } catch {
            throw ApiFehler.antwortUnlesbar
        }
    }

    // Schickt etwas hin und liest die Antwort
    func schicken<Eingabe: Encodable, Ausgabe: Decodable>(_ pfad: String, methode: String = "POST", koerper: Eingabe) async throws -> Ausgabe {
        var anfrage = try anfrageBauen(pfad: pfad, methode: methode)
        anfrage.httpBody = try enkoder.encode(koerper)

        let (daten, antwort) = try await URLSession.shared.data(for: anfrage)
        try antwortPruefen(daten: daten, antwort: antwort)

        do {
            return try dekoder.decode(Ausgabe.self, from: daten)
        } catch {
            throw ApiFehler.antwortUnlesbar
        }
    }

    // Schickt etwas hin, ohne dass die Antwort interessiert
    func schickenOhneAntwort<Eingabe: Encodable>(_ pfad: String, methode: String = "POST", koerper: Eingabe) async throws {
        var anfrage = try anfrageBauen(pfad: pfad, methode: methode)
        anfrage.httpBody = try enkoder.encode(koerper)

        let (daten, antwort) = try await URLSession.shared.data(for: anfrage)
        try antwortPruefen(daten: daten, antwort: antwort)
    }

    func loeschen(_ pfad: String) async throws {
        let anfrage = try anfrageBauen(pfad: pfad, methode: "DELETE")
        let (daten, antwort) = try await URLSession.shared.data(for: anfrage)
        try antwortPruefen(daten: daten, antwort: antwort)
    }
}

// Kleine Hilfsstrukturen fuer die Anfragen, damit nicht ueberall Dictionaries herumfliegen

struct FreitextAnfrage: Encodable {
    let text: String
}

struct TodoAnfrage: Encodable {
    let inhalt: String
    let faelligAm: String?
    let quelle: String
}

struct TodoAenderung: Encodable {
    var inhalt: String?
    var faelligAm: String?
    var erledigt: Bool?
}

struct EssenAenderung: Encodable {
    var beschreibung: String?
    var mengeText: String?
    var kcal: Double?
    var eiweissG: Double?
    var kohlenhydrateG: Double?
    var fettG: Double?
}

struct WasserAnfrage: Encodable {
    let mengeMl: Int
}

struct ZieleAnfrage: Encodable {
    var kcalZiel: Double?
    var eiweissZielG: Double?
    var kohlenhydrateZielG: Double?
    var fettZielG: Double?
    var wasserZielMl: Int?
}

struct InteressenAnfrage: Encodable {
    let stichwoerter: [String]
}

struct FeedbackAnfrage: Encodable {
    let titel: String
    let bewertung: String
}

struct VertiefenAnfrage: Encodable {
    let titel: String
    let zusammenfassung: String
}
