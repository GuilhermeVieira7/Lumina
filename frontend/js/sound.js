// ==========================================
// SOUND CONTROLLER - Sons curtos e voz sob demanda
// ==========================================
// Nada toca sozinho: sons só respondem a um toque da criança, e a voz
// dos elogios fica desligada até um adulto ligar (RNF03).

const SoundController = {
    audioContext: null,
    enabled: true,       // sons de acerto/erro
    voiceEnabled: false, // falar elogios automaticamente
    isLowStimulus: false,

    configure({ sound_enabled = true, voice_enabled = false, low_stimulus = false } = {}) {
        this.enabled = sound_enabled;
        this.voiceEnabled = voice_enabled;
        this.isLowStimulus = low_stimulus;
    },

    _getContext() {
        if (!this.audioContext) {
            try {
                this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            } catch (e) {
                this.enabled = false;
            }
        }
        return this.audioContext;
    },

    _playTone(frequency, duration, volume = 0.18) {
        if (!this.enabled) return;
        const ctx = this._getContext();
        if (!ctx) return;
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.type = 'sine';
        osc.frequency.value = frequency;
        gain.gain.setValueAtTime(this.isLowStimulus ? volume * 0.3 : volume, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + duration);
    },

    playCorrect() { this._playTone(587.33, 0.18); },
    playIncorrect() { this._playTone(329.63, 0.18, 0.12); },
    playFinish() {
        if (!this.enabled) return;
        [523.25, 659.25, 783.99].forEach((f, i) => setTimeout(() => this._playTone(f, 0.18), i * 160));
    },

    /** Ler um texto em voz alta (sempre que a criança toca no 🔊). */
    speak(text) {
        if (!('speechSynthesis' in window)) {
            UI.toast('Este navegador não tem leitura em voz alta.', 'error');
            return null;
        }
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'pt-BR';
        msg.rate = 0.85;
        msg.volume = this.isLowStimulus ? 0.6 : 0.9;
        const voice = window.speechSynthesis.getVoices().find(v => v.lang.startsWith('pt'));
        if (voice) msg.voice = voice;
        window.speechSynthesis.speak(msg);
        return msg;
    },

    /** Elogio falado: só se o adulto ligou a opção e sem Modo Baixo Estímulo. */
    praise(text) {
        if (this.voiceEnabled && !this.isLowStimulus) this.speak(text);
    },
};
