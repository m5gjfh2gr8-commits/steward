import SwiftUI

// Kleine Teile, die in mehreren Ansichten vorkommen

struct FortschrittsBalken: View {
    let titel: String
    let aktuell: Double
    let ziel: Double
    let einheit: String
    let farbe: Color

    private var anteil: Double {
        if ziel <= 0 {
            return 0
        }
        let roh = aktuell / ziel
        if roh > 1 {
            return 1
        }
        return roh
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack {
                Text(titel)
                    .font(.subheadline)
                Spacer()
                Text("\(Int(aktuell)) / \(Int(ziel)) \(einheit)")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            ProgressView(value: anteil)
                .tint(farbe)
        }
    }
}

struct LadeAnzeige: View {
    let text: String

    var body: some View {
        HStack(spacing: 8) {
            ProgressView()
            Text(text)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .center)
        .padding()
    }
}

struct FehlerKarte: View {
    let text: String

    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Image(systemName: "exclamationmark.triangle")
                .foregroundStyle(.orange)
            Text(text)
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
    }
}

struct NichtEingerichtetHinweis: View {
    var body: some View {
        ContentUnavailableView {
            Label("Noch nicht verbunden", systemImage: "network.slash")
        } description: {
            Text("Trag in den Einstellungen die Server-Adresse und den API-Key ein.")
        }
    }
}

// Macht aus "2026-09-14T15:30:00" ein "15:30"
func uhrzeitAusText(_ text: String) -> String {
    if text.count < 16 {
        return ""
    }
    let start = text.index(text.startIndex, offsetBy: 11)
    let ende = text.index(text.startIndex, offsetBy: 16)
    return String(text[start..<ende])
}

// Macht aus "2026-09-14T15:30:00" ein "14.09. 15:30"
func datumUndZeitAusText(_ text: String?) -> String {
    guard let text = text else {
        return ""
    }
    if text.count < 16 {
        return text
    }

    let jahrStart = text.index(text.startIndex, offsetBy: 0)
    let tagTeil = text.index(text.startIndex, offsetBy: 10)
    let datumsteil = String(text[jahrStart..<tagTeil])

    let teile = datumsteil.split(separator: "-")
    if teile.count != 3 {
        return text
    }

    return "\(teile[2]).\(teile[1]). " + uhrzeitAusText(text)
}
