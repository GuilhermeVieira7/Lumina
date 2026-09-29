// ==========================================
// AUTH CONTROLLER - Entrar, criar conta, sair
// ==========================================

const AuthController = {
    init() {
        document.getElementById('login-form').addEventListener('submit', e => this.login(e));
        document.getElementById('register-form').addEventListener('submit', e => this.register(e));
    },

    async login(event) {
        event.preventDefault();
        const btn = event.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        try {
            const data = await API.post('/auth/login', {
                username: document.getElementById('login-username').value.trim(),
                password: document.getElementById('login-password').value,
            });
            API.setToken(data.access_token);
            document.getElementById('login-password').value = '';
            await App.loadSession();
            UI.toast(`Olá, ${data.user.username}!`, 'success');
        } catch (error) {
            UI.toast(error.message, 'error');
        } finally {
            btn.disabled = false;
        }
    },

    async register(event) {
        event.preventDefault();
        const password = document.getElementById('register-password').value;
        if (password !== document.getElementById('register-confirm').value) {
            UI.toast('As senhas não são iguais', 'error');
            return;
        }
        const btn = event.target.querySelector('button[type="submit"]');
        btn.disabled = true;
        try {
            const data = await API.post('/auth/register', {
                username: document.getElementById('register-username').value.trim(),
                email: document.getElementById('register-email').value.trim() || null,
                password,
                role: event.target.querySelector('input[name="role"]:checked').value,
                consent: document.getElementById('register-consent').checked,
            });
            API.setToken(data.access_token);
            event.target.reset();
            UI.toast('Conta criada!', 'success');
            await App.loadSession();
        } catch (error) {
            UI.toast(error.message, 'error');
        } finally {
            btn.disabled = false;
        }
    },

    logout() {
        API.clearToken();
        localStorage.removeItem('tea_profile_id');
        App.user = null;
        App.profile = null;
        App.profiles = [];
        UI.showScreen('login-screen');
        UI.toast('Até logo! 👋', 'success');
    },

    expire() {
        App.user = null;
        UI.showScreen('login-screen');
    },
};

AuthController.init();
