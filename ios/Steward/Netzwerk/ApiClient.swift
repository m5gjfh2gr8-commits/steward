import Foundation

// Sprechen mit dem Steward-Backend am Heimserver
// Adresse und Key kommen aus den Einstellungen; erreichbar ist der Server nur,
// wenn Tailscale am iPhone aktiv ist

enum ApiFehler: LocalizedError {
    case keineAdresse
    case ungueltigeAdresse
    case nichtErreichbar
    case falscherKey
    case serverFehler(Int, String)
    case antwortUnlesbar

    var errorDescription: String? {
        switch self {
        case .keineAdresse:
            return "Keine Server-Adresse eingetragen"
        case .ungueltigeAdresse:
            return "Die Server-Adresse sieht nicht wie eine Adresse aus"
        case .nichtErreichbar:
            return "Server antwortet nicht. Ist Tailscale an?"
        case .falscherKey:
            return "Der Steward-Key passt nicht zum Server"
        case .serverFehler(let code, let text):
            return text + " (Fehler " + String(code) + ")"
        case .antwortUnlesbar:
            return "Antwort vom Server war nicht lesbar"
        }
    }

    // Unterscheidet "Server weg" von "Server meldet einen Fehler" - für den Offline-Hinweis
    var istOffline: Bool {
        switch self {
        case .nichtErreichbar:
            return true
        default:
            return false
        }
    }
}

// Für POST-Anfragen ohne Inhalt
struct LeererKoerper: Encodable {
}

class ApiClient {
    static let geteilt: ApiClient = ApiClient()

    private let dekoder: JSONDecoder
    private let enkoder: JSONEncoder
    private let sitzung: URLSession

    init() {
        dekoder = JSONDecoder()
        dekoder.keyDecodingStrategy = .convertFromSnakeCase

        enkoder = JSONEncoder()
        enkoder.keyEncodingStrategy = .convertToSnakeCase

        let konfiguration: URLSessionConfiguration = URLSessionConfiguration.default
        konfiguration.timeoutIntervalForRequest = 20
        // Modul-Läufe und Antworten vom Modell können dauern
        konfiguration.timeoutIntervalForResource = 180
        sitzung = URLSession(configuration: konfiguration)
    }

    private func anfrageBauen(pfad: String, methode: String, langsam: Bool) throws -> URLRequest {
        let basis: String = Einstellungen.geteilt.basisAdresse()
        if basis.isEmpty {
            throw ApiFehler.keineAdresse
        }

        guard let url = URL(string: basis + pfad) else {
            throw ApiFehler.ungueltigeAdresse
        }

        var anfrage: URLRequest = URLRequest(url: url)
        anfrage.httpMethod = methode
        anfrage.setValue(Einstellungen.geteilt.apiKey, forHTTPHeaderField: "X-API-Key")
        anfrage.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if langsam {
            anfrage.timeoutInterval = 180
        } else {
            anfrage.timeoutInterval = 20
        }
        return anfrage
    }

    // Schickt die Anfrage ab und übersetzt Netzwerkfehler in ApiFehler
    private func ausfuehren(_ anfrage: URLRequest) async throws -> Data {
        let ergebnis: (Data, URLResponse)

        do {
            ergebnis = try await sitzung.data(for: anfrage)
        } catch {
            throw ApiFehler.nichtErreichbar
        }

        let daten: Data = ergebnis.0
        let antwort: URLResponse = ergebnis.1

        guard let http = antwort as? HTTPURLResponse else {
            throw ApiFehler.antwortUnlesbar
        }

        if http.statusCode == 401 {
            throw ApiFehler.falscherKey
        }

        if http.statusCode >= 400 {
            throw ApiFehler.serverFehler(http.statusCode, ApiClient.fehlertextLesen(daten))
        }

        return daten
    }

    // FastAPI schickt Fehler als {"detail": "..."}
    private static func fehlertextLesen(_ daten: Data) -> String {
        if let objekt = try? JSONSerialization.jsonObject(with: daten) as? [String: Any] {
            if let detail = objekt["detail"] as? String {
                return detail
            }
        }
        return String(data: daten, encoding: .utf8) ?? "Unbekannter Fehler"
    }

    private func lesen<T: Decodable>(_ daten: Data) throws -> T {
        do {
            return try dekoder.decode(T.self, from: daten)
        } catch {
            throw ApiFehler.antwortUnlesbar
        }
    }

    // Holt etwas vom Server
    func holen<T: Decodable>(_ pfad: String) async throws -> T {
        let anfrage: URLRequest = try anfrageBauen(pfad: pfad, methode: "GET", langsam: false)
        let daten: Data = try await ausfuehren(anfrage)
        return try lesen(daten)
    }

    // Schickt etwas hin und liest die Antwort
    func schicken<Eingabe: Encodable, Ausgabe: Decodable>(_ pfad: String, methode: String = "POST", koerper: Eingabe, langsam: Bool = false) async throws -> Ausgabe {
        var anfrage: URLRequest = try anfrageBauen(pfad: pfad, methode: methode, langsam: langsam)
        anfrage.httpBody = try enkoder.encode(koerper)
        let daten: Data = try await ausfuehren(anfrage)
        return try lesen(daten)
    }

    // Schickt etwas hin, die Antwort interessiert nicht
    func schickenOhneAntwort<Eingabe: Encodable>(_ pfad: String, methode: String = "POST", koerper: Eingabe, langsam: Bool = false) async throws {
        var anfrage: URLRequest = try anfrageBauen(pfad: pfad, methode: methode, langsam: langsam)
        anfrage.httpBody = try enkoder.encode(koerper)
        _ = try await ausfuehren(anfrage)
    }

    func loeschen(_ pfad: String) async throws {
        let anfrage: URLRequest = try anfrageBauen(pfad: pfad, methode: "DELETE", langsam: false)
        _ = try await ausfuehren(anfrage)
    }

    // Prüft Erreichbarkeit UND Key: /health geht ohne Key, /module/zustand nur mit
    // Ausgabe: die Server-Version
    func verbindungTesten() async throws -> String {
        let gesundheit: Gesundheit = try await holen("/health")
        let _: ZustandUeberblick = try await holen("/module/zustand")
        return gesundheit.version ?? "?"
    }
}

// Was an den Server geschickt wird

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
