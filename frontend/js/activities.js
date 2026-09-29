// ==========================================
// ACTIVITY - Execução de uma atividade em modo de foco
// ==========================================
// Sistema de trabalho do ensino estruturado (TEACCH): a criança vê quantas
// etapas são, em qual está e onde termina. Uma instrução por tela.

const Activity = {
    plan: null,
    practice: false,
    questions: [],
    index: 0,
    correct: 0,
    incorrect: 0,
    attempts: 1,
    responses: [],
    sessionStart: 0,
    questionStart: 0,
    locked: false,

    PRAISE: ['Muito bem!', 'Isso mesmo!', 'Você conseguiu!', 'Boa!', 'Perfeito!'],
    RETRY: ['Tente de novo', 'Quase! Mais uma vez', 'Vamos tentar outra?'],

    init() {
        document.getElementById('activity-pause').addEventListener('click', () => UI.open('pause-modal'));
        document.getElementById('pause-continue').addEventListener('click', () => UI.close('pause-modal'));
        document.getElementById('pause-stop').addEventListener('click', () => {
            UI.close('pause-modal');
            window.speechSynthesis?.cancel();
            Child.home();
        });
        document.getElementById('finish-continue').addEventListener('click', () => Child.home());
    },

    async start(plan, practice) {
        this.plan = plan;
        this.practice = practice;
        let data;
        try {
            data = await API.get(`/activities/${plan.activity_type}/questions?level=${plan.level}`);
        } catch (err) {
            UI.toast(err.message, 'error');
            return;
        }
        const count = plan.question_count || 5;
        this.questions = this._shuffle([...data.questions]).slice(0, count);
        if (!this.questions.length) {
            UI.toast('Esta atividade ainda não tem questões', 'error');
            return;
        }
        this.index = 0;
        this.correct = 0;
        this.incorrect = 0;
        this.responses = [];
        this.sessionStart = Date.now();

        document.getElementById('activity-icon').textContent = plan.icon;
        document.getElementById('activity-title').textContent = practice ? `${plan.name} · treino` : plan.name;
        document.getElementById('activity-level').textContent = `Nível ${plan.level}`;
        UI.showScreen('activity-screen');
        this._render();
    },

    _renderSteps() {
        const total = this.questions.length;
        const dots = this.questions.map((_, i) => {
            const cls = i < this.index ? 'done' : i === this.index ? 'current' : '';
            return `<span class="dot ${cls}">${i < this.index ? '✓' : i + 1}</span>`;
        }).join('');
        document.getElementById('activity-steps').innerHTML = dots + '<span class="dot finish">🏁</span>';
        document.getElementById('activity-steps-caption').textContent =
            this.index === total - 1 ? `Etapa ${total} de ${total}: é a última!` : `Etapa ${this.index + 1} de ${total}`;
    },

    _clockSvg(time) {
        const [h, m] = time.split(':').map(Number);
        const minAngle = m * 6;
        const hourAngle = (h % 12) * 30 + m * 0.5;
        const hand = (angle, len, width, color) => {
            const rad = (angle - 90) * Math.PI / 180;
            return `<line x1="50" y1="50" x2="${50 + len * Math.cos(rad)}" y2="${50 + len * Math.sin(rad)}" stroke="${color}" stroke-width="${width}" stroke-linecap="round"/>`;
        };
        const marks = Array.from({ length: 12 }, (_, i) => {
            const rad = (i * 30 - 90) * Math.PI / 180;
            return `<text x="${50 + 38 * Math.cos(rad)}" y="${50 + 38 * Math.sin(rad) + 3.5}" font-size="9" font-weight="700" text-anchor="middle" fill="currentColor">${i === 0 ? 12 : i}</text>`;
        }).join('');
        return `<svg viewBox="0 0 100 100" role="img" aria-label="Relógio marcando ${h} horas e ${m} minutos">
            <circle cx="50" cy="50" r="47" fill="var(--card)" stroke="currentColor" stroke-width="3"/>
            ${marks}${hand(hourAngle, 22, 5, '#4d74c9')}${hand(minAngle, 34, 3, '#e8a655')}
            <circle cx="50" cy="50" r="3" fill="currentColor"/></svg>`;
    },

    _render() {
        if (this.index >= this.questions.length) {
            this._finish();
            return;
        }
        this.attempts = 1;
        this.locked = false;
        this.questionStart = Date.now();
        this._renderSteps();
        this._setMascot('idle', '');

        const q = this.questions[this.index];
        let text = q.question;
        let visual = q.visual || q.sequence || '';
        // Relógio: mostrar o relógio desenhado em vez de escrever a resposta na pergunta
        const isClock = this.plan.activity_type === 'clock' && /^\d{2}:\d{2}$/.test(q.correct) && text.startsWith('Que horas são?');
        if (isClock) {
            text = 'Que horas são?';
            visual = this._clockSvg(q.correct);
        } else {
            visual = UI.esc(visual);
        }

        document.getElementById('activity-question').innerHTML = `
            <div class="question-text">
                <span id="question-label">${UI.esc(text)}</span>
                <button class="speak-btn" id="speak-btn" aria-label="Ouvir a pergunta">🔊</button>
            </div>
            ${visual ? `<div class="question-visual">${visual}</div>` : ''}
            ${q.reference && !q.visual ? `<div class="question-reference">${this._optionHtml(q, q.reference, true)}</div>` : ''}`;
        document.getElementById('speak-btn').addEventListener('click', () => SoundController.speak(text));

        const options = document.getElementById('activity-options');
        options.innerHTML = '';
        this._shuffle([...q.options]).forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            if (q.type !== 'color' && String(opt).length > 3) btn.classList.add('text-option');
            btn.innerHTML = this._optionHtml(q, opt);
            if (q.type === 'color') btn.setAttribute('aria-label', UI.COLOR_NAMES[opt] || 'cor');
            btn.dataset.value = opt;
            btn.addEventListener('click', () => this._answer(btn, opt, q));
            options.appendChild(btn);
        });
    },

    _optionHtml(q, value, reference = false) {
        if (q.type === 'color') {
            return `<span class="swatch" style="background:${UI.esc(value)}${reference ? ';display:inline-block' : ''}" aria-hidden="true"></span>`;
        }
        return UI.esc(value);
    },

    _answer(btn, selected, q) {
        if (this.locked) return;
        const isCorrect = selected === q.correct;
        if (isCorrect) {
            this.locked = true;
            this.responses.push({
                question_index: this.index,
                is_correct: this.attempts === 1,
                response_time: Date.now() - this.questionStart,
                attempts: this.attempts,
            });
            if (this.attempts === 1) this.correct++;
            btn.classList.add('correct');
            document.querySelectorAll('.option-btn').forEach(b => { b.disabled = true; });
            const msg = this.PRAISE[Math.floor(Math.random() * this.PRAISE.length)];
            this._setMascot('happy', msg, 'good');
            SoundController.playCorrect();
            SoundController.praise(msg);
            setTimeout(() => { this.index++; this._render(); }, 1400);
        } else {
            this.incorrect++;
            this.attempts++;
            btn.classList.add('try-again');
            btn.disabled = true;
            const msg = this.RETRY[Math.floor(Math.random() * this.RETRY.length)];
            this._setMascot('sad', msg, 'retry');
            SoundController.playIncorrect();
            // Ensino sem erro (ABA): depois de 2 erros, a resposta certa ganha uma dica visual
            if (this.attempts > 2) {
                const right = [...document.querySelectorAll('.option-btn')].find(b => b.dataset.value === q.correct);
                right?.classList.add('hint');
                this._setMascot('idle', 'Olha a dica 👀', 'retry');
            }
        }
    },

    _setMascot(mood, text, cls = '') {
        document.getElementById('mascot').src = `/img/mascot/fox_${mood}.png`;
        const bubble = document.getElementById('mascot-bubble');
        bubble.textContent = text;
        bubble.className = `bubble ${cls}`;
    },

    async _finish() {
        const total = this.questions.length;
        const firstTry = this.correct;
        const accuracy = total ? (firstTry / total) * 100 : 0;
        const stars = accuracy >= 90 ? 3 : accuracy >= 70 ? 2 : accuracy >= 50 ? 1 : 0;
        let medals = [];

        try {
            await API.post('/sessions', {
                profile_id: App.profile.id,
                activity_type: this.plan.activity_type,
                level: this.plan.level,
                total_questions: total,
                correct: firstTry,
                incorrect: total - firstTry,
                total_time: Date.now() - this.sessionStart,
                is_practice: this.practice,
                responses: this.responses,
            });
            if (!this.practice) {
                const check = await API.post(`/achievements/check/${App.profile.id}`);
                medals = check.newly_unlocked || [];
            }
        } catch (err) {
            UI.toast('Não foi possível salvar a sessão: ' + err.message, 'error');
        }

        document.getElementById('finish-message').textContent =
            `Você fez as ${total} etapas e acertou ${firstTry} de primeira.`;
        document.getElementById('finish-stars').innerHTML =
            [0, 1, 2].map(i => `<span class="${i < stars ? '' : 'off'}" aria-hidden="true">⭐</span>`).join('') +
            `<span class="sr-only">${stars} de 3 estrelas</span>`;
        const medalBox = document.getElementById('finish-medal');
        medalBox.classList.toggle('hidden', !medals.length);
        medalBox.innerHTML = medals.map(m => `${m.icon} Nova medalha: ${UI.esc(m.name)}!`).join('<br>');
        SoundController.playFinish();
        UI.showScreen('finish-screen');
    },

    _shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    },
};

Activity.init();
