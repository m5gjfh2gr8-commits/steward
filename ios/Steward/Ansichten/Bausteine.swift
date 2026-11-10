import SwiftUI

// Kleine Bausteine, die mehrere Bildschirme gemeinsam verwenden

// Hinweis-Leiste oben, wenn der Server nicht antwortet - die alten Daten bleiben darunter sichtbar
struct OfflineHinweis: View {
    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: "wifi.slash")
            Text("Steward nicht erreichbar – Tailscale an?")
        }
        .font(.subheadline)
        .foregroundStyle(.secondary)
        .padding(.horizontal, 14)
        .padding(.vertical, 8)
        .background(.regularMaterial, in: Capsule())
        .padding(.top, 4)
        .accessibilityElement(children: .combine)
    }
}

// Blauer Kreis mit Zahl, wie bei Mail oder Nachrichten
struct UngelesenZaehler: View {
    let anzahl: Int

    var body: some View {
        Text(String(anzahl))
            .font(.subheadline.weight(.semibold))
            .monospacedDigit()
            .foregroundStyle(.white)
            .padding(.horizontal, 7)
            .frame(minWidth: 22, minHeight: 22)
            .background(Capsule().fill(.tint))
            .accessibilityLabel(String(anzahl) + " neu")
    }
}

// Punkt + Wort für den Zustand eines Moduls
struct ZustandsAnzeige: View {
    let zustand: String

    private var farbe: Color {
        switch zustand {
        case "ok":
            return Color.green
        case "wackelig":
            return Color.orange
        case "kaputt":
            return Color.red
        default:
            return Color.secondary
        }
    }

    private var wort: String {
        switch zustand {
        case "ok":
            return "OK"
        case "wackelig":
            return "Fehler"
        case "kaputt":
            return "Mehrfach fehlgeschlagen"
        case "neu":
            return "Noch nicht gelaufen"
        default:
            return zustand
        }
    }

    var body: some View {
        HStack(spacing: 6) {
            Circle()
                .fill(farbe)
                .frame(width: 8, height: 8)
            Text(wort)
                .fontWeight(.medium)
                .foregroundStyle(farbe)
        }
    }
}

// Eine Kennzahl als Kachel im Bericht: Bezeichnung klein, Wert groß
struct KennzahlKachel: View {
    let kennzahl: Kennzahl

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(kennzahl.name)
                .font(.footnote)
                .foregroundStyle(.secondary)
                .lineLimit(1)
            Text(kennzahl.wert)
                .font(.title2.weight(.semibold))
                .monospacedDigit()
                .lineLimit(1)
                .minimumScaleFactor(0.6)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        .accessibilityElement(children: .combine)
    }
}

// Kleine graue Überschrift über einem Block, wie "KENNZAHLEN" in den iOS-Einstellungen
struct AbschnittsTitel: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.footnote)
            .foregroundStyle(.secondary)
            .padding(.horizontal, 16)
            .padding(.top, 24)
            .padding(.bottom, 8)
    }
}

// Ergebnis von "Verbindung testen" - grünes Häkchen oder rotes X
enum TestErgebnis {
    case keins
    case laeuft
    case ok(String)
    case fehler(String)
}

struct TestErgebnisAnzeige: View {
    let ergebnis: TestErgebnis

    var body: some View {
        switch ergebnis {
        case .keins:
            EmptyView()
        case .laeuft:
            HStack(spacing: 8) {
                ProgressView()
                Text("Teste Verbindung …")
                    .foregroundStyle(.secondary)
            }
            .font(.footnote)
        case .ok(let version):
            Label {
                Text("Verbindung steht · Server " + version)
                    .foregroundStyle(.secondary)
            } icon: {
                Image(systemName: "checkmark")
                    .fontWeight(.bold)
                    .foregroundStyle(.green)
            }
            .font(.footnote)
        case .fehler(let text):
            Label {
                Text("Keine Verbindung: " + text)
                    .foregroundStyle(.secondary)
            } icon: {
                Image(systemName: "xmark")
                    .fontWeight(.bold)
                    .foregroundStyle(.red)
            }
            .font(.footnote)
        }
    }
}

// Führt den Verbindungstest aus und liefert das Ergebnis für die Anzeige
func verbindungPruefen() async -> TestErgebnis {
    do {
        let version: String = try await ApiClient.geteilt.verbindungTesten()
        return TestErgebnis.ok(version)
    } catch {
        return TestErgebnis.fehler(error.localizedDescription)
    }
}
