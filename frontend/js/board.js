// ==========================================
// BOARD - Quadro de fichas e prancha de pedidos
// ==========================================

// ---------- Quadro de fichas: a criança escolhe o prêmio antes de começar ----------
const RewardPicker = {
    plan: null,

    init() {
        document.getElementById('reward-skip').addEventListener('click', () => this._pick(null));
    },

    open(plan) {
        this.plan = plan;
        const rewards = (App.settings && App.settings.rewards) || [];
        const grid = document.getElementById('reward-grid');
        grid.innerHTML = rewards.map((r, i) => `
            <button class="reward-card" data-reward="${i}">
                <span class="pic">${UI.pic(r.icon)}</span>${UI.esc(r.label)}
            </button>`).join('');
        grid.querySelectorAll('[data-reward]').forEach(b => b.addEventListener('click', () => this._pick(rewards[Number(b.dataset.reward)])));
        document.getElementById('reward-activity').innerHTML =
            `<span class="pic">${UI.pic(plan.icon)}</span> ${UI.esc(plan.name)}`;
        UI.showScreen('reward-screen');
    },

    _pick(reward) {
        Activity.begin(this.plan, false, reward);
    },
};

// ---------- Prancha de pedidos: a criança pede e o adulto vê ----------
const RequestBoard = {
    init() {
        document.getElementById('ask-btn').addEventListener('click', () => this.open());
        document.getElementById('ask-close').addEventListener('click', () => this.close());
        document.getElementById('ask-ok').addEventListener('click', () => this._after());
        document.getElementById('ask-modal').addEventListener('keydown', e => { if (e.key === 'Escape') this.close(); });
        document.addEventListener('screenchange', () => this.refreshButton());
    },

    get enabled() { return !!(App.profile && App.settings && App.settings.request_board !== false); },

    refreshButton() {
        const childMode = document.body.classList.contains('child-mode');
        document.getElementById('ask-btn').classList.toggle('hidden', !(childMode && this.enabled));
    },

    options() {
        const wanted = (App.settings && App.settings.requests) || [];
        return App.requestOptions.filter(o => wanted.includes(o.key));
    },

    open() {
        this.last = null;
        const grid = document.getElementById('ask-grid');
        grid.innerHTML = this.options().map(o => `
            <button class="ask-card" data-ask="${o.key}">
                <span class="pic">${UI.pic(o.icon)}</span>${UI.esc(o.label)}
            </button>`).join('');
        grid.querySelectorAll('[data-ask]').forEach(b => b.addEventListener('click', () => this.say(b.dataset.ask)));
        document.getElementById('ask-choose').classList.remove('hidden');
        document.getElementById('ask-said').classList.add('hidden');
        this.wasRunning = Activity.pauseTimer();
        UI.open('ask-modal');
    },

    async say(key) {
        const option = App.requestOptions.find(o => o.key === key);
        if (!option) return;
        this.last = option;
        document.getElementById('ask-said-pic').innerHTML = UI.pic(option.icon);
        document.getElementById('ask-said-text').textContent = option.phrase;
        document.getElementById('ask-choose').classList.add('hidden');
        document.getElementById('ask-said').classList.remove('hidden');
        document.getElementById('ask-ok').focus();
        // A criança tocou: aqui a voz é a própria comunicação dela
        SoundController.speak(option.phrase);
        try {
            await API.post('/requests', {
                profile_id: App.profile.id,
                key,
                context: Activity.inProgress() ? Activity.plan.name : null,
            });
        } catch (err) {
            UI.toast('O pedido não foi salvo: ' + err.message, 'error');
        }
    },

    close() {
        UI.close('ask-modal');
        if (this.wasRunning) Activity.resumeTimer();
        this.wasRunning = false;
    },

    /** Depois do OK: pausa e "acabou" abrem a pausa da atividade; ajuda mostra a dica. */
    _after() {
        const key = this.last && this.last.key;
        const inActivity = Activity.inProgress();
        if (inActivity && (key === 'pausa' || key === 'acabou')) {
            this.wasRunning = false;   // a pausa da atividade assume o timer
            UI.close('ask-modal');
            Activity.openPause();
            return;
        }
        this.close();
        if (inActivity && key === 'ajuda') Activity.showHint();
    },
};

RewardPicker.init();
RequestBoard.init();
