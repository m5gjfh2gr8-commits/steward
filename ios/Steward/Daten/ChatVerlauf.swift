import Foundation

// Der Verlauf im Steward-Tab
// Der Server merkt sich keine Gespräche - die App speichert die letzten Nachrichten selbst

struct ChatNachricht: Codable, Identifiable {
    let id: UUID
    let vonMir: Bool
    let text: String
    // "frage", "aufgabe" oder "fehler" (nur bei Antworten von Steward)
    let art: String
    let zeit: Date
}

@MainActor
class ChatVerlauf: ObservableObject {
    @Published var nachrichten: [ChatNachricht] = []
    @Published var wartet: Bool = false

    private let schluessel: String = "chatVerlauf"
    private let hoechstens: Int = 100

    init() {
        if let daten = UserDefaults.standard.data(forKey: schluessel) {
            if let gelesen = try? JSONDecoder().decode([ChatNachricht].self, from: daten) {
                nachrichten = gelesen
            }
        }
    }

    func senden(_ text: String) async {
        let sauber: String = text.trimmingCharacters(in: .whitespacesAndNewlines)
        if sauber.isEmpty {
            return
        }

        anhaengen(ChatNachricht(id: UUID(), vonMir: true, text: sauber, art: "frage", zeit: Date()))
        wartet = true

        do {
            let antwort: ChatAntwort = try await ApiClient.geteilt.schicken("/chat", koerper: FreitextAnfrage(text: sauber), langsam: true)
            anhaengen(ChatNachricht(id: UUID(), vonMir: false, text: antwort.antwort, art: antwort.art, zeit: Date()))
        } catch {
            let meldung: String = "Steward kann gerade nicht antworten: " + error.localizedDescription
            anhaengen(ChatNachricht(id: UUID(), vonMir: false, text: meldung, art: "fehler", zeit: Date()))
        }

        wartet = false
    }

    func leeren() {
        nachrichten = []
        speichern()
    }

    private func anhaengen(_ nachricht: ChatNachricht) {
        nachrichten.append(nachricht)

        // Nur die letzten 100 aufheben, ältere fallen raus
        while nachrichten.count > hoechstens {
            nachrichten.removeFirst()
        }
        speichern()
    }

    private func speichern() {
        if let daten = try? JSONEncoder().encode(nachrichten) {
            UserDefaults.standard.set(daten, forKey: schluessel)
        }
    }
}
