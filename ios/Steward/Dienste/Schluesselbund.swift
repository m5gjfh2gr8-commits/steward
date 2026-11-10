import Foundation
import Security

// Kleiner Helfer für die Keychain
// Dort liegt der Steward-Key verschlüsselt, statt im Klartext in den UserDefaults

enum Schluesselbund {
    static let dienst: String = "at.lorenz.steward"

    static func speichern(_ wert: String, konto: String) {
        let suche: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: dienst,
            kSecAttrAccount as String: konto,
        ]

        // Alten Eintrag immer zuerst entfernen, dann neu anlegen - einfacher als Update
        SecItemDelete(suche as CFDictionary)

        if wert.isEmpty {
            return
        }

        var neuerEintrag: [String: Any] = suche
        neuerEintrag[kSecValueData as String] = Data(wert.utf8)
        // Nach dem ersten Entsperren lesbar, damit auch der Hintergrund-Blick an den Key kommt
        neuerEintrag[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock

        SecItemAdd(neuerEintrag as CFDictionary, nil)
    }

    static func lesen(konto: String) -> String {
        let suche: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: dienst,
            kSecAttrAccount as String: konto,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]

        var ergebnis: AnyObject?
        let status: OSStatus = SecItemCopyMatching(suche as CFDictionary, &ergebnis)

        if status != errSecSuccess {
            return ""
        }

        guard let daten = ergebnis as? Data else {
            return ""
        }

        return String(data: daten, encoding: .utf8) ?? ""
    }
}
