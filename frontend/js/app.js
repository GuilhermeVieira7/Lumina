// ==========================================
// APP - Estado da sessão e tela de escolha
// ==========================================

const App = {
    user: null,
    profiles: [],
    profile: null,
    settings: null,
    activities: {},   // metadados das atividades (nome, ícone, área)
    requestOptions: [], // pedidos possíveis da prancha
    rewardOptions: [],  // prêmios sugeridos para o quadro de fichas

    async init() {
        ThemeController.init();
        this._wire();
        await Pictos.load();

        const host = window.location.hostname;
        if (host === 'localhost' || host === '127.0.0.1') {
            document.getElementById('demo-hint').classList.remove('hidden');
        }

        if (API.token) {
            try {
                await this.loadSession();
                return;
            } catch {
                API.clearToken();
            }
        }
        UI.showScreen('login-screen');
    },

    _wire() {
        document.querySelectorAll('[data-go]').forEach(b => b.addEventListener('click', () => UI.showScreen(b.dataset.go)));
        document.querySelectorAll('[data-child-home]').forEach(b => b.addEventListener('click', () => Child.home()));
        document.getElementById('enter-child').addEventListener('click', () => this.enterChild());
        document.getElementById('enter-adult').addEventListener('click', () => this.enterAdult());
        document.getElementById('logout-btn').addEventListener('click', () => AuthController.logout());
        document.getElementById('child-exit').addEventListener('click', () => this.leaveChild());
        document.getElementById('new-profile-form').addEventListener('submit', e => this.createProfile(e));
        document.querySelectorAll('.modal').forEach(m => m.addEventListener('keydown', e => {
            if (e.key === 'Escape' && !['password-modal', 'pause-modal', 'ask-modal'].includes(m.id)) UI.close(m.id);
        }));
    },

    async loadSession() {
        this.user = await API.get('/auth/me');
        const [list, options] = await Promise.all([API.get('/activities'), API.get('/requests/options')]);
        this.activities = Object.fromEntries(list.map(a => [a.type, a]));
        this.requestOptions = options.requests;
        this.rewardOptions = options.rewards;
        await this.loadProfiles();

        if (!this.profiles.length && this.user.role !== 'therapist') {
            UI.showScreen('select-screen');
            this.openNewProfile(true);
            return;
        }
        UI.showScreen('select-screen');
    },

    async loadProfiles() {
        this.profiles = await API.get('/profiles');
        const savedId = Number(localStorage.getItem('tea_profile_id'));
        const chosen = this.profiles.find(p => p.id === savedId) || this.profiles[0] || null;
        if (chosen) await this.selectProfile(chosen, false);
        else this.profile = null;
        this.renderSelect();
    },

    renderSelect() {
        const row = document.getElementById('select-profiles');
        if (!this.profiles.length) {
            row.innerHTML = this.user && this.user.role === 'therapist'
                ? UI.empty('✉️', 'Nenhuma criança compartilhada ainda. Os convites aparecem no Painel dos Adultos, em Ajustes.')
                : UI.empty('🧒', 'Cadastre a primeira criança no Painel dos Adultos.');
            document.getElementById('enter-child').disabled = true;
            return;
        }
        document.getElementById('enter-child').disabled = false;
        row.innerHTML = this.profiles.map(p => `
            <button class="profile-pick" data-profile="${p.id}" aria-pressed="${this.profile && p.id === this.profile.id}">
                <span class="avatar" aria-hidden="true">${UI.esc(p.avatar)}</span>
                ${UI.esc(p.name)}
                ${p.is_owner ? '' : `<small>de ${UI.esc(p.owner_name)}</small>`}
            </button>`).join('');
        row.querySelectorAll('[data-profile]').forEach(b => b.addEventListener('click', async () => {
            await this.selectProfile(this.profiles.find(p => p.id === Number(b.dataset.profile)));
        }));
    },

    async selectProfile(profile, rerender = true) {
        this.profile = profile;
        localStorage.setItem('tea_profile_id', profile.id);
        try {
            this.settings = await API.get(`/settings/${profile.id}`);
        } catch {
            this.settings = { sound_enabled: true, voice_enabled: false, low_stimulus: false, token_board: false, request_board: false };
        }
        this.applySettings();
        if (rerender) this.renderSelect();
    },

    applySettings() {
        const s = this.settings || {};
        SoundController.configure(s);
        document.body.classList.toggle('low-stimulus', !!s.low_stimulus);
        RequestBoard.refreshButton();
    },

    enterChild() {
        if (!this.profile) {
            UI.toast('Escolha uma criança primeiro', 'error');
            return;
        }
        Child.home();
    },

    async enterAdult() {
        if (await UI.askPassword('O Painel dos Adultos pede a senha da conta.')) Admin.open();
    },

    async leaveChild() {
        if (await UI.askPassword('Para sair da área da criança, um adulto digita a senha.')) {
            this.renderSelect();
            UI.showScreen('select-screen');
        }
    },

    openNewProfile(first = false) {
        const form = document.getElementById('new-profile-form');
        UI.renderProfileForm(form, null, first ? 'Cadastrar e começar' : 'Cadastrar criança');
        document.getElementById('new-profile-title').textContent = first ? '🧒 Vamos cadastrar a criança' : '🧒 Nova criança';
        if (!first) {
            const cancel = document.createElement('button');
            cancel.type = 'button';
            cancel.className = 'btn btn-outline';
            cancel.textContent = 'Cancelar';
            cancel.onclick = () => UI.close('new-profile-modal');
            form.querySelector('.actions').prepend(cancel);
        }
        UI.open('new-profile-modal');
    },

    async createProfile(e) {
        e.preventDefault();
        const form = e.target;
        try {
            const profile = await API.post('/profiles', UI.readProfileForm(form));
            UI.close('new-profile-modal');
            UI.toast(`${profile.name} cadastrado(a)!`, 'success');
            localStorage.setItem('tea_profile_id', profile.id);
            await this.loadProfiles();
            if (document.getElementById('panel-screen').classList.contains('active')) Admin.open('profile');
        } catch (err) {
            UI.toast(err.message, 'error');
        }
    },
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js').catch(() => {});
    }
});
