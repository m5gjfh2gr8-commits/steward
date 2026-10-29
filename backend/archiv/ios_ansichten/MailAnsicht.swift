import SwiftUI

// Kompakte Liste der wichtigen/interessanten Mails ueber alle Postfaecher
// Bewusst ohne vollen Mailtext und ohne Antwortfunktion - nur damit man weiss, dass was da ist

struct MailAnsicht: View {
    let uebersicht: MailUebersicht

    @State private var aktuelle: MailUebersicht?
    @State private var laedt = false

    private var anzuzeigen: MailUebersicht {
        if let aktuelle = aktuelle {
            return aktuelle
        }
        return uebersicht
    }

    var body: some View {
        List {
            if !anzuzeigen.fehler.isEmpty {
                Section("Probleme beim Abrufen") {
                    ForEach(anzuzeigen.fehler, id: \.self) { fehler in
                        FehlerKarte(text: fehler)
                    }
                }
            }

            Section("Wichtig") {
                let wichtige = anzuzeigen.mails.filter { $0.stufe == "wichtig" }
                if wichtige.isEmpty {
                    Text("Nichts Wichtiges")
                        .foregroundStyle(.secondary)
                }
                ForEach(wichtige) { mail in
                    MailZeile(mail: mail)
                }
            }

            Section("Interessant") {
                let interessante = anzuzeigen.mails.filter { $0.stufe == "interessant" }
                if interessante.isEmpty {
                    Text("Nichts dabei")
                        .foregroundStyle(.secondary)
                }
                ForEach(interessante) { mail in
                    MailZeile(mail: mail)
                }
            }

            Section {
                Button {
                    Task { await neuLaden() }
                } label: {
                    if laedt {
                        LadeAnzeige(text: "Postfaecher werden abgefragt")
                    } else {
                        Text("Jetzt neu abfragen")
                    }
                }
            } footer: {
                Text("Wird normal nur einmal pro Tag abgefragt, damit moeglichst wenig Modell-Aufrufe anfallen.")
            }
        }
        .navigationTitle("Mail")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func neuLaden() async {
        laedt = true
        do {
            aktuelle = try await ApiClient.geteilt.holen("/mail/important?neu_laden=true")
        } catch {
            // die alte Liste bleibt einfach stehen
        }
        laedt = false
    }
}

struct MailZeile: View {
    let mail: WichtigeMail

    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(mail.betreff)
                .font(.subheadline.weight(.medium))
                .lineLimit(2)

            Text(mail.absender)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)

            HStack(spacing: 6) {
                Text(mail.postfach)
                    .font(.caption2)
                    .padding(.horizontal, 6)
                    .padding(.vertical, 2)
                    .background(Color(.tertiarySystemFill))
                    .clipShape(Capsule())

                if !mail.grund.isEmpty {
                    Text(mail.grund)
                        .font(.caption2)
                        .foregroundStyle(.tertiary)
                        .lineLimit(1)
                }
            }
        }
    }
}
