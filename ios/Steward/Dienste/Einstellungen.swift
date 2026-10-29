import Foundation

// Server-Adresse, API-Key und die lokalen Schalter
// Liegt in UserDefaults - reicht, weil der Server nur ueber Tailscale erreichbar ist
// und das iPhone selbst durch Code/FaceID gesperrt ist

class Einstellungen: ObservableObject {
    static let geteilt = Einstellungen()

    @Published var serverAdresse: String {
        didSet {
            UserDefaults.standard.set(serverAdresse, forKey: "serverAdresse")
        }
    }

    @Published var apiKey: String {
        didSet {
            UserDefaults.standard.set(apiKey, forKey: "apiKey")
        }
    }

    @Published var trinkErinnerungAn: Bool {
        didSet {
            UserDefaults.standard.set(trinkErinnerungAn, forKey: "trinkErinnerungAn")
        }
    }

    @Published var trinkErinnerungStunden: Int {
        didSet {
            UserDefaults.standard.set(trinkErinnerungStunden, forKey: "trinkErinnerungStunden")
        }
    }

    init() {
        serverAdresse = UserDefaults.standard.string(forKey: "serverAdresse") ?? ""
        apiKey = UserDefaults.standard.string(forKey: "apiKey") ?? ""
        trinkErinnerungAn = UserDefaults.standard.bool(forKey: "trinkErinnerungAn")

        let gespeicherteStunden = UserDefaults.standard.integer(forKey: "trinkErinnerungStunden")
        if gespeicherteStunden == 0 {
            trinkErinnerungStunden = 3
        } else {
            trinkErinnerungStunden = gespeicherteStunden
        }
    }

    var istEingerichtet: Bool {
        if serverAdresse.isEmpty {
            return false
        }
        if apiKey.isEmpty {
            return false
        }
        return true
    }
}
