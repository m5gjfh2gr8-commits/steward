import Foundation

// Die Gegenstuecke zu den JSON-Antworten vom Backend
// Der Decoder ist auf convertFromSnakeCase gestellt, aus "faellig_am" wird also faelligAm

struct Todo: Codable, Identifiable {
    let id: Int
    var inhalt: String
    var faelligAm: String?
    var erledigt: Int
    var quelle: String
    var erstelltAm: String

    var istErledigt: Bool {
        return erledigt == 1
    }
}

struct ZerlegterText: Codable {
    let inhalt: String
    let faelligAm: String?
    let istTermin: Bool
}

struct Termin: Codable, Identifiable {
    var id: String {
        return titel + beginn
    }

    let titel: String
    let beginn: String
    let ende: String
    let ganztaegig: Bool
    let ort: String
}

struct Meldung: Codable, Identifiable {
    var id: String {
        return titel
    }

    let titel: String
    let zusammenfassung: String
    let quelle: String
    let link: String
}

struct Briefing: Codable {
    let datum: String
    let begruessung: String
    let termine: [Termin]
    let todos: [Todo]
    let news: [Meldung]
    let hinweise: [String]
    let vorlesetext: String
}

struct WichtigeMail: Codable, Identifiable {
    var id: String {
        return postfach + absender + betreff
    }

    let postfach: String
    let absender: String
    let betreff: String
    let datum: String
    let stufe: String
    let grund: String
}

struct MailUebersicht: Codable {
    let datum: String
    let mails: [WichtigeMail]
    let anzahlWichtig: Int
    let anzahlInteressant: Int
    let fehler: [String]
}

struct EssenEintrag: Codable, Identifiable {
    let id: Int
    var beschreibung: String
    var mengeText: String?
    var kcal: Double
    var eiweissG: Double
    var kohlenhydrateG: Double
    var fettG: Double
    var quelle: String
    var bearbeitet: Int
}

struct Naehrwertsumme: Codable {
    let kcal: Double
    let eiweissG: Double
    let kohlenhydrateG: Double
    let fettG: Double
}

struct Tagesziele: Codable {
    var kcalZiel: Double
    var eiweissZielG: Double
    var kohlenhydrateZielG: Double
    var fettZielG: Double
    var wasserZielMl: Int
}

struct EssenTag: Codable {
    let datum: String
    let eintraege: [EssenEintrag]
    let summe: Naehrwertsumme
    let ziele: Tagesziele
}

struct VerlaufsTag: Codable, Identifiable {
    var id: String {
        return datum
    }

    let datum: String
    let kcal: Double
    let eiweissG: Double
    let kohlenhydrateG: Double
    let fettG: Double
}

struct Verlauf: Codable {
    let tage: Int
    let verlauf: [VerlaufsTag]
}

struct EssenAntwort: Codable {
    let eintraege: [EssenEintrag]
    let summeEingabe: Naehrwertsumme
}

struct WasserStand: Codable {
    let datum: String
    let summeMl: Int
    let letzterEintrag: String?
    let zielMl: Int
}

struct Interesse: Codable, Identifiable {
    let id: Int
    let stichwort: String
    let aktiv: Int
}

struct ChatAntwort: Codable {
    let art: String
    let antwort: String
}

struct ServerStatus: Codable {
    let zeit: String
    let llmAnbieter: String
    let llmModellStandard: String
    let kalenderEingerichtet: Bool
    let postfaecher: [String]
    let feeds: [String]
}

struct VertiefungsAntwort: Codable {
    let text: String
}
