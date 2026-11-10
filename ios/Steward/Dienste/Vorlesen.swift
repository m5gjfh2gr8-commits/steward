import AVFoundation
import Foundation

// Berichte anhören statt lesen, mit den Stimmen, die am iPhone eh dabei sind
// Stimme und Tempo kommen aus den Einstellungen

class Vorlesen: NSObject, ObservableObject, AVSpeechSynthesizerDelegate {
    static let geteilt: Vorlesen = Vorlesen()

    @Published var laeuft: Bool = false

    private let sprecher: AVSpeechSynthesizer = AVSpeechSynthesizer()

    override init() {
        super.init()
        sprecher.delegate = self
    }

    // Startet das Vorlesen - läuft schon etwas, wird stattdessen gestoppt
    func umschalten(text: String) {
        if sprecher.isSpeaking {
            stoppen()
            return
        }
        starten(text: text)
    }

    func starten(text: String) {
        if text.isEmpty {
            return
        }

        do {
            let sitzung: AVAudioSession = AVAudioSession.sharedInstance()
            try sitzung.setCategory(.playback, mode: .spokenAudio, options: [.duckOthers])
            try sitzung.setActive(true)
        } catch {
            return
        }

        let aeusserung: AVSpeechUtterance = AVSpeechUtterance(string: text)
        aeusserung.voice = Vorlesen.gewaehlteStimme()
        aeusserung.rate = Float(Einstellungen.geteilt.vorleseTempo)

        sprecher.speak(aeusserung)
        laeuft = true
    }

    func stoppen() {
        sprecher.stopSpeaking(at: .immediate)
        laeuft = false
    }

    // Alle deutschen Stimmen am Gerät, für die Auswahl in den Einstellungen
    static func deutscheStimmen() -> [AVSpeechSynthesisVoice] {
        var gefunden: [AVSpeechSynthesisVoice] = []
        for stimme in AVSpeechSynthesisVoice.speechVoices() {
            if stimme.language.hasPrefix("de") {
                gefunden.append(stimme)
            }
        }
        return gefunden
    }

    private static func gewaehlteStimme() -> AVSpeechSynthesisVoice? {
        let kennung: String = Einstellungen.geteilt.vorleseStimme
        if kennung.isEmpty == false {
            if let stimme = AVSpeechSynthesisVoice(identifier: kennung) {
                return stimme
            }
        }
        return AVSpeechSynthesisVoice(language: "de-DE")
    }

    // Wird vom System aufgerufen, wenn der Text zu Ende gesprochen ist
    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didFinish utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.laeuft = false
        }
    }

    func speechSynthesizer(_ synthesizer: AVSpeechSynthesizer, didCancel utterance: AVSpeechUtterance) {
        DispatchQueue.main.async {
            self.laeuft = false
        }
    }
}
