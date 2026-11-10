import Foundation

// Alles, was die App sich lokal merkt
// Der Steward-Key liegt in der Keychain (verschlüsselt), der Rest in den UserDefaults

class Einstellungen: ObservableObject {
    static let geteilt: Einstellungen = Einstellungen()

    private let speicher: UserDefaults = UserDefaults.standard

    @Published var serverAdresse: String {
        didSet {
            speicher.set(serverAdresse, forKey: "serverAdresse")
        }
    }

    @Published var apiKey: String {
        didSet {
            Schluesselbund.speichern(apiKey, konto: "stewardKey")
        }
    }

    @Published var einrichtungAbgeschlossen: Bool {
        didSet {
            speicher.set(einrichtungAbgeschlossen, forKey: "einrichtungAbgeschlossen")
        }
    }

    @Published var akzent: Akzentfarbe {
        didSet {
            speicher.set(akzent.rawValue, forKey: "akzent")
        }
    }

    // Kennung der Vorlese-Stimme, leer = Standardstimme
    @Published var vorleseStimme: String {
        didSet {
            speicher.set(vorleseStimme, forKey: "vorleseStimme")
        }
    }

    // 0.5 ist die normale Sprechgeschwindigkeit von iOS
    @Published var vorleseTempo: Double {
        didSet {
            speicher.set(vorleseTempo, forKey: "vorleseTempo")
        }
    }

    @Published var hintergrundHinweise: Bool {
        didSet {
            speicher.set(hintergrundHinweise, forKey: "hintergrundHinweise")
        }
    }

    @Published var zaehlerAmSymbol: Bool {
        didSet {
            speicher.set(zaehlerAmSymbol, forKey: "zaehlerAmSymbol")
        }
    }

    init() {
        serverAdresse = speicher.string(forKey: "serverAdresse") ?? ""
        einrichtungAbgeschlossen = speicher.bool(forKey: "einrichtungAbgeschlossen")

        let gespeicherteFarbe: String = speicher.string(forKey: "akzent") ?? ""
        akzent = Akzentfarbe(rawValue: gespeicherteFarbe) ?? Akzentfarbe.blau

        vorleseStimme = speicher.string(forKey: "vorleseStimme") ?? ""

        if speicher.object(forKey: "vorleseTempo") == nil {
            vorleseTempo = 0.5
        } else {
            vorleseTempo = speicher.double(forKey: "vorleseTempo")
        }

        hintergrundHinweise = speicher.bool(forKey: "hintergrundHinweise")

        // Standard: Zähler am App-Symbol an
        if speicher.object(forKey: "zaehlerAmSymbol") == nil {
            zaehlerAmSymbol = true
        } else {
            zaehlerAmSymbol = speicher.bool(forKey: "zaehlerAmSymbol")
        }

        // Alte App-Version hat den Key in den UserDefaults gespeichert - einmalig umziehen
        let alterKey: String = speicher.string(forKey: "apiKey") ?? ""
        if alterKey.isEmpty == false {
            Schluesselbund.speichern(alterKey, konto: "stewardKey")
            speicher.removeObject(forKey: "apiKey")
        }
        apiKey = Schluesselbund.lesen(konto: "stewardKey")
    }

    // Macht aus der Eingabe eine vollständige Adresse
    // "pesenhofer-server.tail1234.ts.net" wird zu "https://pesenhofer-server.tail1234.ts.net"
    func basisAdresse() -> String {
        var adresse: String = serverAdresse.trimmingCharacters(in: .whitespacesAndNewlines)

        if adresse.isEmpty {
            return ""
        }

        if adresse.hasPrefix("http://") == false && adresse.hasPrefix("https://") == false {
            adresse = "https://" + adresse
        }

        while adresse.hasSuffix("/") {
            adresse = String(adresse.dropLast())
        }

        return adresse
    }
}
