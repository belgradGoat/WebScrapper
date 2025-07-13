// Simple sound system for the game
class SoundManager {
    constructor() {
        this.enabled = true;
        this.sounds = {};
        this.context = null;
        
        // Try to initialize Web Audio API
        try {
            this.context = new (window.AudioContext || window.webkitAudioContext)();
        } catch (e) {
            console.log('Web Audio API not supported');
        }
    }
    
    // Generate simple beep sounds using Web Audio API
    beep(frequency = 440, duration = 200, type = 'sine') {
        if (!this.enabled || !this.context) return;
        
        const oscillator = this.context.createOscillator();
        const gainNode = this.context.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(this.context.destination);
        
        oscillator.frequency.setValueAtTime(frequency, this.context.currentTime);
        oscillator.type = type;
        
        gainNode.gain.setValueAtTime(0.3, this.context.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, this.context.currentTime + duration / 1000);
        
        oscillator.start(this.context.currentTime);
        oscillator.stop(this.context.currentTime + duration / 1000);
    }
    
    playSuccess() {
        this.beep(523, 100); // C5
        setTimeout(() => this.beep(659, 100), 100); // E5
        setTimeout(() => this.beep(784, 200), 200); // G5
    }
    
    playError() {
        this.beep(220, 300, 'sawtooth'); // Low A
    }
    
    playWarning() {
        this.beep(330, 150); // E4
        setTimeout(() => this.beep(330, 150), 200);
    }
    
    playInteraction() {
        this.beep(440, 50); // A4
    }
    
    playComplete() {
        // Victory fanfare
        const notes = [523, 659, 784, 1047]; // C-E-G-C octave
        notes.forEach((note, i) => {
            setTimeout(() => this.beep(note, 150), i * 100);
        });
    }
    
    toggle() {
        this.enabled = !this.enabled;
        return this.enabled;
    }
}

// Global sound manager
const soundManager = new SoundManager();
