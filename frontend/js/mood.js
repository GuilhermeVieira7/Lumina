// ==========================================
// MOOD - "Como estou me sentindo?"
// ==========================================
// Ao entrar na área da criança (e quando ela quiser, pelo botão na tela
// inicial), ela toca no rosto que mostra como está. O Lumina fala a frase,
// acolhe a emoção e registra para os adultos verem no painel.

const Mood = {
    moment: 'entrada',
    chosen: null,

    init() {
        document.getElementById('mood-skip').addEventListener('click', () => Child.home());
        document.getElementById('mood-go').addEventListener('click', () => Child.home());
        document.getElementById('mood-help').addEventListener('click', () => {
            RequestBoard.open();
            RequestBoard.say('ajuda');
        });
        document.getElementById('mood-again').addEventListener('click', () => this._show('choose'));
    },

    get enabled() { return !!(App.settings && App.settings.mood_checkin !== false); },

    /** moment: "entrada" (ao abrir a área da criança) ou "livre" (botão na tela inicial). */
    open(moment = 'entrada') {
        this.moment = moment;
        this.chosen = null;
        const grid = document.getElementById('mood-grid');
        grid.innerHTML = App.moodOptions.map(m => `
            <button class="mood-card" data-mood="${m.key}" style="--mood:${m.color}">
                <span class="pic" aria-hidden="true">${UI.pic(m.icon, { alt: m.label })}</span>${UI.esc(m.label)}
            </button>`).join('');
        grid.querySelectorAll('[data-mood]').forEach(b => b.addEventListener('click', () => this.choose(b.dataset.mood)));
        document.getElementById('mood-skip').innerHTML = moment === 'entrada'
            ? '<span class="ico" aria-hidden="true">▶️</span> Agora não'
            : '<span class="ico" aria-hidden="true">🏠</span> Voltar';
        this._show('choose');
        UI.showScreen('mood-screen');
    },

    _show(step) {
        document.getElementById('mood-choose').classList.toggle('hidden', step !== 'choose');
        document.getElementById('mood-said').classList.toggle('hidden', step !== 'said');
    },

    async choose(key) {
        const mood = App.moodOptions.find(m => m.key === key);
        if (!mood) return;
        this.chosen = mood;
        const said = document.getElementById('mood-said');
        said.style.setProperty('--mood', mood.color);
        document.getElementById('mood-said-pic').innerHTML = UI.pic(mood.icon, { alt: mood.label });
        document.getElementById('mood-said-text').textContent = mood.phrase;
        document.getElementById('mood-said-note').textContent = mood.hard
            ? 'Tudo bem se sentir assim. Um adulto vai saber como você está.'
            : 'Que bom! Obrigado por contar.';
        document.getElementById('mood-help').classList.toggle('hidden', !(mood.hard && RequestBoard.enabled));
        this._show('said');
        document.getElementById('mood-go').focus();
        // Foi a criança que tocou: a voz é a comunicação dela, como na prancha de pedidos
        SoundController.speak(mood.phrase);
        try {
            await API.post('/moods', { profile_id: App.profile.id, mood: key, moment: this.moment });
        } catch (err) {
            UI.toast('Não foi possível salvar: ' + err.message, 'error');
        }
    },
};

Mood.init();
