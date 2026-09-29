// ==========================================
// TIMER VISUAL - Disco que diminui conforme o tempo passa
// ==========================================
// Mostra "quanto falta" sem exigir que a criança leia números, como os
// timers visuais usados no ensino estruturado. Atualiza uma vez por
// segundo, sem animação contínua.

class VisualTimer {
    constructor(container, { onEnd, onTick } = {}) {
        this.container = container;
        this.onEnd = onEnd;
        this.onTick = onTick;
        this.total = 0;
        this.left = 0;
        this.running = false;
        this._interval = null;
        this._endsAt = 0;
    }

    start(ms) {
        this.stop();
        this.total = ms;
        this.left = ms;
        this.resume();
    }

    resume() {
        if (this.running || this.left <= 0) return;
        this.running = true;
        this._endsAt = Date.now() + this.left;
        this._interval = setInterval(() => this._tick(), 1000);
        this.render();
    }

    pause() {
        if (!this.running) return;
        this.left = Math.max(0, this._endsAt - Date.now());
        this.running = false;
        clearInterval(this._interval);
        this.render();
    }

    stop() {
        this.running = false;
        clearInterval(this._interval);
        this._interval = null;
    }

    _tick() {
        this.left = Math.max(0, this._endsAt - Date.now());
        this.render();
        if (this.onTick) this.onTick(this.left);
        if (this.left <= 0) {
            this.stop();
            if (this.onEnd) this.onEnd();
        }
    }

    static text(ms) {
        const seconds = Math.ceil(ms / 1000);
        if (seconds <= 0) return 'Acabou!';
        if (seconds < 60) return `Falta${seconds === 1 ? '' : 'm'} ${seconds} segundo${seconds === 1 ? '' : 's'}`;
        const minutes = Math.ceil(seconds / 60);
        return `Falta${minutes === 1 ? '' : 'm'} ${minutes} minuto${minutes === 1 ? '' : 's'}`;
    }

    /** SVG do disco: a parte colorida é o tempo que ainda falta. */
    static svg(fraction, { marks = true } = {}) {
        const f = Math.max(0, Math.min(1, fraction));
        const r = 44;
        let wedge = '';
        if (f >= 0.9999) {
            wedge = `<circle cx="50" cy="50" r="${r}" class="timer-left-fill"/>`;
        } else if (f > 0) {
            const angle = f * 2 * Math.PI;
            const x = 50 + r * Math.sin(angle);
            const y = 50 - r * Math.cos(angle);
            wedge = `<path class="timer-left-fill" d="M50 50 L50 ${50 - r} A${r} ${r} 0 ${f > 0.5 ? 1 : 0} 1 ${x.toFixed(2)} ${y.toFixed(2)} Z"/>`;
        }
        const ticks = marks ? Array.from({ length: 12 }, (_, i) => {
            const a = i * Math.PI / 6;
            const inner = i % 3 === 0 ? 38 : 41;
            return `<line x1="${(50 + inner * Math.sin(a)).toFixed(2)}" y1="${(50 - inner * Math.cos(a)).toFixed(2)}" x2="${(50 + 46 * Math.sin(a)).toFixed(2)}" y2="${(50 - 46 * Math.cos(a)).toFixed(2)}" class="timer-tick"/>`;
        }).join('') : '';
        return `<svg viewBox="0 0 100 100" aria-hidden="true" focusable="false">
            <circle cx="50" cy="50" r="48" class="timer-face"/>
            ${wedge}${ticks}
            <circle cx="50" cy="50" r="5" class="timer-knob"/>
        </svg>`;
    }

    render() {
        if (!this.container) return;
        const fraction = this.total ? this.left / this.total : 0;
        this.container.innerHTML = VisualTimer.svg(fraction, { marks: this.container.dataset.marks !== 'false' });
        this.container.setAttribute('role', 'img');
        this.container.setAttribute('aria-label', `Timer: ${VisualTimer.text(this.left)}`);
    }
}

// ---------- Tela do timer (área da criança) ----------
const TimerScreen = {
    timer: null,
    routineItem: null,
    CHOICES: [1, 2, 5, 10, 15],

    init() {
        this.timer = new VisualTimer(document.getElementById('timer-disc'), {
            onEnd: () => this._done(),
            onTick: left => this._updateText(left),
        });
        document.getElementById('timer-picker').innerHTML = this.CHOICES.map(m => `
            <button class="timer-choice" data-minutes="${m}" aria-label="${m} minuto${m > 1 ? 's' : ''}">
                <span class="mini-disc">${VisualTimer.svg(m / 15, { marks: false })}</span>
                <b>${m}</b><small>min</small>
            </button>`).join('');
        document.querySelectorAll('[data-minutes]').forEach(b => b.addEventListener('click', () => this._begin(Number(b.dataset.minutes))));
        document.getElementById('timer-pause').addEventListener('click', () => this.togglePause());
        document.getElementById('timer-again').addEventListener('click', () => {
            this.timer.stop();
            this._show('pick');
        });
        document.getElementById('timer-finish').addEventListener('click', () => this._markDone());
        document.addEventListener('screenchange', e => { if (e.detail !== 'timer-screen') this.timer.stop(); });
    },

    /** Abre o timer; com uma etapa da rotina que tem duração, já começa a contar. */
    open(routineItem = null) {
        this.routineItem = routineItem;
        UI.showScreen('timer-screen');
        const what = document.getElementById('timer-what');
        what.innerHTML = routineItem
            ? `<span class="pic">${UI.pic(routineItem.icon)}</span><span>${UI.esc(routineItem.label)}</span>`
            : '';
        what.classList.toggle('hidden', !routineItem);
        document.getElementById('timer-done').classList.add('hidden');
        if (routineItem && routineItem.duration) {
            this._begin(routineItem.duration);
        } else {
            this.timer.stop();
            this._show('pick');
        }
    },

    _show(mode) {
        document.getElementById('timer-picker').classList.toggle('hidden', mode !== 'pick');
        document.getElementById('timer-pick-label').classList.toggle('hidden', mode !== 'pick');
        document.getElementById('timer-running').classList.toggle('hidden', mode === 'pick');
        document.getElementById('timer-pause').classList.toggle('hidden', mode !== 'run');
        document.getElementById('timer-done').classList.toggle('hidden', mode !== 'done');
        document.getElementById('timer-finish').classList.toggle('hidden', !(mode === 'done' && this.routineItem && !this.routineItem.done_today));
    },

    _begin(minutes) {
        this._show('run');
        this.timer.start(minutes * 60000);
        this._updateText(this.timer.left);
        this._setPauseLabel();
    },

    togglePause() {
        if (this.timer.running) this.timer.pause(); else this.timer.resume();
        this._setPauseLabel();
    },

    _setPauseLabel() {
        document.getElementById('timer-pause').innerHTML = this.timer.running
            ? '<span class="ico" aria-hidden="true">⏸️</span> Pausar'
            : '<span class="ico" aria-hidden="true">▶️</span> Continuar';
    },

    _updateText(left) {
        document.getElementById('timer-left').textContent = VisualTimer.text(left);
    },

    _done() {
        this._updateText(0);
        this._show('done');
        SoundController.playFinish();
    },

    async _markDone() {
        if (!this.routineItem) return;
        try {
            await API.post(`/routine/${this.routineItem.id}/toggle`);
            SoundController.playCorrect();
            Child.showRoutine();
        } catch (err) {
            UI.toast(err.message, 'error');
        }
    },
};

TimerScreen.init();
