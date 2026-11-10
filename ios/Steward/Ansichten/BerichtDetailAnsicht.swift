import SwiftUI

// Ein Bericht: Titel, Kurzfassung, Kennzahlen als Kacheln, Einträge als Liste
// Diese eine Ansicht gilt für alle Module - auch für Module, die es heute noch nicht gibt

struct BerichtDetailAnsicht: View {
    let bericht: Bericht
    let modulName: String

    @ObservedObject private var vorlesen: Vorlesen = Vorlesen.geteilt

    private let spalten: [GridItem] = [
        GridItem(.flexible(), spacing: 10),
        GridItem(.flexible(), spacing: 10),
    ]

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 0) {
                kopf

                if bericht.kennzahlen.isEmpty == false {
                    AbschnittsTitel(text: "Kennzahlen")
                    LazyVGrid(columns: spalten, spacing: 10) {
                        ForEach(bericht.kennzahlen, id: \.self) { kennzahl in
                            KennzahlKachel(kennzahl: kennzahl)
                        }
                    }
                }

                if bericht.eintraege.isEmpty == false {
                    AbschnittsTitel(text: "Einträge")
                    eintragsliste
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 24)
        }
        .background(Color(.systemGroupedBackground))
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItemGroup(placement: .topBarTrailing) {
                Button {
                    vorlesen.umschalten(text: bericht.vorlesetext)
                } label: {
                    if vorlesen.laeuft {
                        Image(systemName: "stop.fill")
                    } else {
                        Image(systemName: "speaker.wave.2")
                    }
                }
                .accessibilityLabel("Vorlesen")

                ShareLink(item: teiltext) {
                    Image(systemName: "square.and.arrow.up")
                }
                .accessibilityLabel("Teilen")
            }
        }
        .onDisappear {
            vorlesen.stoppen()
        }
    }

    private var kopf: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(modulName + " · " + Zeitformat.mitTag(text: bericht.zeitpunkt))
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Text(bericht.titel)
                .font(.title.bold())
            if bericht.kurzfassung.isEmpty == false {
                Text(bericht.kurzfassung)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(.top, 8)
    }

    private var eintragsliste: some View {
        VStack(spacing: 0) {
            ForEach(0..<bericht.eintraege.count, id: \.self) { index in
                EintragZeile(eintrag: bericht.eintraege[index])

                if index < bericht.eintraege.count - 1 {
                    Divider()
                        .padding(.leading, 16)
                }
            }
        }
        .background(Color(.secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 20, style: .continuous))
    }

    // Was beim Teilen verschickt wird: der ganze Bericht als einfacher Text
    private var teiltext: String {
        var zeilen: [String] = []
        zeilen.append(bericht.titel)
        if bericht.kurzfassung.isEmpty == false {
            zeilen.append(bericht.kurzfassung)
        }
        for kennzahl in bericht.kennzahlen {
            zeilen.append(kennzahl.name + ": " + kennzahl.wert)
        }
        for eintrag in bericht.eintraege {
            var zeile: String = "• " + eintrag.titel
            let link: String = eintrag.link ?? ""
            if link.isEmpty == false {
                zeile = zeile + " – " + link
            }
            zeilen.append(zeile)
        }
        return zeilen.joined(separator: "\n")
    }
}

struct EintragZeile: View {
    let eintrag: Eintrag

    private var ziel: URL? {
        let text: String = eintrag.link ?? ""
        if text.isEmpty {
            return nil
        }
        return URL(string: text)
    }

    var body: some View {
        if let ziel = ziel {
            Link(destination: ziel) {
                inhalt(mitLink: ziel)
            }
            .buttonStyle(.plain)
        } else {
            inhalt(mitLink: nil)
        }
    }

    private func inhalt(mitLink link: URL?) -> some View {
        VStack(alignment: .leading, spacing: 2) {
            Text(eintrag.titel)
                .fontWeight(.semibold)
                .foregroundStyle(.primary)

            let text: String = eintrag.text ?? ""
            if text.isEmpty == false {
                Text(text)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            if let link = link {
                HStack(spacing: 4) {
                    Text(link.host() ?? "Link öffnen")
                    Image(systemName: "arrow.up.right")
                        .font(.caption2.weight(.bold))
                }
                .font(.footnote)
                .foregroundStyle(.tint)
                .padding(.top, 4)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .contentShape(Rectangle())
    }
}
