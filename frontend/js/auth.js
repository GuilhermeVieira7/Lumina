// ==========================================
// AUTH CONTROLLER - Login e Registro
// ==========================================

const AuthController = {
    showLogin() {
        AppController.showScreen('login-screen');
    },

    showRegister() {
        AppController.showScreen('register-screen');
    },

    async login(event) {
        event.preventDefault();
        const username = document.getElementById('login-username').value.trim();
        const password = document.getElementById('login-password').value;
        const btn = event.target.querySelector('button[type="submit"]');

        if (!username || !password) {
            AppController.showToast('Preencha todos os campos', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Entrando...';

        try {
            const data = await API.post('/auth/login', { username, password });
            API.setToken(data.access_token);
            AppController.currentUser = data.user;
            localStorage.setItem('tea_user', JSON.stringify(data.user));
            AppController.showToast(`Bem-vindo, ${data.user.username}! 🎉`, 'success');
            AppController.showScreen('select-screen');
            await ProfileController.loadProfiles();
        } catch (error) {
            AppController.showToast(error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Entrar';
        }
    },

    async register(event) {
        event.preventDefault();
        const username = document.getElementById('register-username').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const confirm = document.getElementById('register-confirm').value;
        const btn = event.target.querySelector('button[type="submit"]');

        if (!username || !password) {
            AppController.showToast('Preencha todos os campos obrigatórios', 'error');
            return;
        }

        if (password !== confirm) {
            AppController.showToast('As senhas não conferem', 'error');
            return;
        }

        btn.disabled = true;
        btn.textContent = 'Criando conta...';

        try {
            const data = await API.post('/auth/register', { username, email: email || null, password });
            API.setToken(data.access_token);
            AppController.currentUser = data.user;
            localStorage.setItem('tea_user', JSON.stringify(data.user));
            AppController.showToast('Conta criada com sucesso! 🎉', 'success');
            AppController.showScreen('select-screen');
            // Criar perfil inicial
            await ProfileController.createProfile('Criança 1', '😊');
            await ProfileController.loadProfiles();
        } catch (error) {
            AppController.showToast(error.message, 'error');
        } finally {
            btn.disabled = false;
            btn.textContent = 'Criar Conta';
        }
    },

    logout() {
        API.clearToken();
        AppController.currentUser = null;
        AppController.currentProfile = null;
        localStorage.removeItem('tea_user');
        localStorage.removeItem('tea_profile');
        AppController.showScreen('login-screen');
        AppController.showToast('Até logo! 👋', 'success');
    },

    checkAuth() {
        const token = localStorage.getItem('tea_token');
        const user = localStorage.getItem('tea_user');
        if (token && user) {
            API.token = token;
            AppController.currentUser = JSON.parse(user);
            return true;
        }
        return false;
    },
};
