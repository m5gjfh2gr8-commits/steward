import AVFoundation
import Foundation

// Briefing anhoeren statt lesen, mit der Stimme die am iPhone eh dabei ist

class Vorlesen: ObservableObject {
    static let geteilt = Vorlesen()

    @Published var laeuft = false

    private let sprecher = AVSpeechSynthesizer()

    func starten(text: String) {
        if sprecher.isSpeaking {
            stoppen()
            return
        }

        do {
            try AVAudioSession.sharedInstance().setCategory(.playback, mode: .spokenAudio)
            try AVAudioSession.sharedInstance().setActive(true)
        } catch {
            return
        }

        let aeusserung = AVSpeechUtterance(string: text)
        aeusserung.voice = AVSpeechSynthesisVoice(language: "de-DE")
        aeusserung.rate = 0.5

        sprecher.speak(aeusserung)
        laeuft = true
    }

    func stoppen() {
        sprecher.stopSpeaking(at: .immediate)
        laeuft = false
    }
}
