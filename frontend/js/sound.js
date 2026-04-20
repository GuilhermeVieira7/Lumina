// ==========================================
// SOUND CONTROLLER - Web Audio API
// ==========================================

const SoundController = {
    audioContext: null,
    enabled: true,
    isLowStimulus: false,

    init(lowStimulus = false) {
        this.enabled = localStorage.getItem('tea_sound') !== 'false';
        this.isLowStimulus = lowStimulus;
    },

    setLowStimulus(isActive) {
        this.isLowStimulus = isActive;
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

    _playTone(frequency, duration, type = 'sine', volume = 0.3) {
        if (!this.enabled) return;
        const ctx = this._getContext();
        if (!ctx) return;

        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.frequency.value = frequency;
        
        // Em baixo estímulo sempre usa onda suave
        osc.type = this.isLowStimulus ? 'sine' : type;
        
        const finalVolume = this.isLowStimulus ? volume * 0.2 : volume;
        gain.gain.setValueAtTime(finalVolume, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + duration);
    },

    playCorrect() { 
        this._playTone(523.25, 0.2, 'square'); 
    },
    playIncorrect() { 
        this._playTone(196.0, 0.3, 'sawtooth', 0.2); 
    },
    playReward() {
        if (!this.enabled) return;
        setTimeout(() => this._playTone(523.25, 0.15, 'sine'), 0);
        setTimeout(() => this._playTone(659.25, 0.15, 'sine'), 150);
        setTimeout(() => this._playTone(783.99, 0.3, 'sine'), 300);
    },

    toggle() {
        this.enabled = !this.enabled;
        localStorage.setItem('tea_sound', this.enabled);
        return this.enabled;
    },
};
