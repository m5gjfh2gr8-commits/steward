import Charts
import SwiftUI

// Token-Verbrauch: heute mit Balken zum Tagesdeckel, die letzten 14 Tage als Diagramm,
// darunter wer heute wie viel verbraucht hat

struct KostenAnsicht: View {
    @EnvironmentObject var daten: AppDaten
    @EnvironmentObject var einstellungen: Einstellungen

    @State private var kosten: KostenAntwort?
    @State private var laedt: Bool = true
    @State private var fehlertext: String = ""

    // Ein Balken im Diagramm
    struct Tagessumme: Identifiable {
        let tag: Date
        let tokens: Int

        var id: Date {
            return tag
        }
    }

    var body: some View {
        NavigationStack {
            List {
                if let kosten = kosten {
                    Section {
                        heuteBlock(kosten.heute)
                    }

                    Section("Letzte 14 Tage") {
                        Chart(tagessummen(kosten.verlauf)) { eintrag in
                            BarMark(
                                x: .value("Tag", eintrag.tag, unit: .day),
                                y: .value("Tokens", eintrag.tokens)
                            )
                            .foregroundStyle(einstellungen.akzent.farbe)
                            .cornerRadius(3)
                        }
                        .chartXAxis {
                            AxisMarks(values: .stride(by: .day, count: 3)) { _ in
                                AxisValueLabel(format: .dateTime.day().month(.defaultDigits))
                            }
                        }
                        .frame(height: 180)
                        .padding(.vertical, 8)
                    }

                    Section("Heute nach Modul") {
                        if kosten.heute.proModul.isEmpty {
                            Text("Heute noch nichts verbraucht")
                                .foregroundStyle(.secondary)
                        }
                        ForEach(kosten.heute.proModul) { eintrag in
                            LabeledContent(daten.anzeigename(fuerModul: eintrag.modul)) {
                                Text(eintrag.tokensGesamt.formatted())
                                    .monospacedDigit()
                            }
                        }
                    }
                }
            }
            .listStyle(.insetGrouped)
            .navigationTitle("Kosten")
            .overlay {
                if kosten == nil {
                    if laedt {
                        ProgressView()
                    } else {
                        ContentUnavailableView {
                            Label("Keine Verbindung", systemImage: "wifi.slash")
                        } description: {
                            Text(fehlertext)
                        }
                    }
                }
            }
            .refreshable {
                await laden()
            }
            .task {
                await laden()
            }
        }
    }

    private func heuteBlock(_ heute: Verbrauch) -> some View {
        let anteil: Double = anteilVomLimit(heute)

        return VStack(alignment: .leading, spacing: 6) {
            Text("Heute")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            HStack(alignment: .firstTextBaseline, spacing: 6) {
                Text(heute.tokensGesamt.formatted())
                    .font(.system(size: 40, weight: .bold))
                    .monospacedDigit()
                Text("Tokens")
                    .foregroundStyle(.secondary)
            }

            ProgressView(value: anteil)
                .tint(anteil > 0.8 ? Color.orange : einstellungen.akzent.farbe)

            Text(String(Int((anteil * 100).rounded())) + " % vom Tageslimit (" + heute.budgetProTag.formatted() + ")")
                .font(.footnote)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 6)
    }

    private func anteilVomLimit(_ heute: Verbrauch) -> Double {
        if heute.budgetProTag <= 0 {
            return 0.0
        }
        let anteil: Double = Double(heute.tokensGesamt) / Double(heute.budgetProTag)
        if anteil > 1.0 {
            return 1.0
        }
        return anteil
    }

    // Der Server schickt nur Tage mit Verbrauch - die leeren Tage werden hier mit 0 aufgefüllt
    private func tagessummen(_ verlauf: [VerlaufTag]) -> [Tagessumme] {
        var nachTag: [String: Int] = [:]
        for tag in verlauf {
            nachTag[tag.datum] = (tag.tokensEin ?? 0) + (tag.tokensAus ?? 0)
        }

        let kalender: Calendar = Calendar.current
        let heute: Date = kalender.startOfDay(for: Date())
        var ergebnis: [Tagessumme] = []

        var abstand: Int = 13
        while abstand >= 0 {
            if let tag = kalender.date(byAdding: .day, value: -abstand, to: heute) {
                let schluessel: String = Zeitformat.tagText(tag)
                ergebnis.append(Tagessumme(tag: tag, tokens: nachTag[schluessel] ?? 0))
            }
            abstand = abstand - 1
        }

        return ergebnis
    }

    private func laden() async {
        laedt = true
        do {
            kosten = try await ApiClient.geteilt.holen("/kosten?tage=14")
            fehlertext = ""
        } catch {
            fehlertext = error.localizedDescription
        }
        laedt = false
    }
}
