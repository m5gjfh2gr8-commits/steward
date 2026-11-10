import SwiftUI
import UIKit

// Die wählbaren Akzentfarben aus den Einstellungen
// Wo es geht Apples eigene Systemfarben - die passen sich automatisch an hell/dunkel
// und an "Kontrast erhöhen" an. Petrol und Graphit gibt es so nicht, die sind selbst gemischt

enum Akzentfarbe: String, CaseIterable, Identifiable {
    case blau
    case indigo
    case petrol
    case gruen
    case orange
    case rot
    case rosa
    case graphit

    var id: String {
        return rawValue
    }

    var name: String {
        switch self {
        case .blau:
            return "Blau"
        case .indigo:
            return "Indigo"
        case .petrol:
            return "Petrol"
        case .gruen:
            return "Grün"
        case .orange:
            return "Orange"
        case .rot:
            return "Rot"
        case .rosa:
            return "Rosa"
        case .graphit:
            return "Graphit"
        }
    }

    var farbe: Color {
        switch self {
        case .blau:
            return Color.blue
        case .indigo:
            return Color.indigo
        case .petrol:
            return Akzentfarbe.hellDunkel(hell: UIColor(red: 0.055, green: 0.486, blue: 0.525, alpha: 1.0),
                                          dunkel: UIColor(red: 0.251, green: 0.784, blue: 0.878, alpha: 1.0))
        case .gruen:
            return Color.green
        case .orange:
            return Color.orange
        case .rot:
            return Color.red
        case .rosa:
            return Color.pink
        case .graphit:
            return Akzentfarbe.hellDunkel(hell: UIColor(red: 0.227, green: 0.227, blue: 0.235, alpha: 1.0),
                                          dunkel: UIColor(red: 0.682, green: 0.682, blue: 0.698, alpha: 1.0))
        }
    }

    // Eine Farbe, die im Dunkelmodus automatisch auf den zweiten Ton wechselt
    private static func hellDunkel(hell: UIColor, dunkel: UIColor) -> Color {
        let gemischt: UIColor = UIColor { merkmale in
            if merkmale.userInterfaceStyle == .dark {
                return dunkel
            }
            return hell
        }
        return Color(uiColor: gemischt)
    }
}
