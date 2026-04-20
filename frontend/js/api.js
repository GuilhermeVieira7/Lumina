// ==========================================
// API CLIENT - Comunicação com Backend
// ==========================================

const API = {
    BASE_URL: '/api',
    token: localStorage.getItem('tea_token'),

    setToken(token) {
        this.token = token;
        localStorage.setItem('tea_token', token);
    },

    clearToken() {
        this.token = null;
        localStorage.removeItem('tea_token');
    },

    async request(method, path, body = null) {
        const headers = { 'Content-Type': 'application/json' };
        if (this.token) {
            headers['Authorization'] = `Bearer ${this.token}`;
        }

        try {
            const res = await fetch(`${this.BASE_URL}${path}`, {
                method,
                headers,
                body: body ? JSON.stringify(body) : null,
            });

            if (res.status === 401) {
                this.clearToken();
                if (window.AuthController) {
                    AuthController.showLogin();
                }
                throw new Error('Sessão expirada. Faça login novamente.');
            }

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Erro na requisição');
            }

            return data;
        } catch (error) {
            if (error.message === 'Failed to fetch') {
                console.warn('[API] Servidor offline ou sem conexão');
                throw new Error('Sem conexão com o servidor');
            }
            throw error;
        }
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    delete(path) { return this.request('DELETE', path); },
};
