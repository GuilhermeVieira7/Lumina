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

        const fail = (message, status) => Object.assign(new Error(message), { status });

        let res;
        try {
            res = await fetch(`${this.BASE_URL}${path}`, {
                method,
                headers,
                body: body ? JSON.stringify(body) : null,
            });
        } catch (error) {
            // Chrome, Firefox e Safari dão mensagens diferentes; todos lançam TypeError sem rede
            console.warn('[API] Servidor offline ou sem conexão', error);
            throw Object.assign(fail('Sem conexão com o servidor', 0), { offline: true });
        }

        if (res.status === 401 && !path.startsWith('/auth/login')) {
            this.clearToken();
            if (window.AuthController) AuthController.expire();
            throw fail('Sessão expirada. Faça login novamente.', 401);
        }

        // Página de erro da hospedagem (ex.: 502 enquanto o servidor acorda) não é JSON
        let data = null;
        try { data = await res.json(); } catch { data = null; }

        if (!res.ok) {
            if (!data) throw fail(res.status >= 500 ? 'O servidor está iniciando ou indisponível. Tente de novo em instantes.' : 'Erro na requisição', res.status);
            const detail = Array.isArray(data.detail) ? 'Confira os campos preenchidos' : data.detail;
            throw fail(detail || 'Erro na requisição', res.status);
        }
        if (data === null) throw fail('Resposta inválida do servidor', res.status);
        return data;
    },

    // ---- Sessões feitas sem internet: guardadas no aparelho e enviadas depois ----
    PENDING_KEY: 'lumina_pending_sessions',
    _flushing: false,

    _pending() {
        try { return JSON.parse(localStorage.getItem(this.PENDING_KEY) || '[]'); } catch { return []; }
    },

    _savePending(list) {
        try { localStorage.setItem(this.PENDING_KEY, JSON.stringify(list.slice(-50))); } catch { /* armazenamento indisponível */ }
    },

    queueSession(payload) {
        const list = this._pending();
        list.push(payload);
        this._savePending(list);
    },

    pendingCount() { return this._pending().length; },

    /** Envia as sessões guardadas. Descarta só as que o servidor recusa de vez (dados inválidos, criança apagada). */
    async flushPending() {
        if (!this.token || this._flushing) return 0;
        const list = this._pending();
        if (!list.length) return 0;
        this._flushing = true;
        let sent = 0;
        const keep = [];
        try {
            for (const payload of list) {
                try {
                    await this.post('/sessions', payload);
                    sent++;
                } catch (err) {
                    if (![400, 403, 404, 422].includes(err.status)) keep.push(payload);
                }
            }
        } finally {
            // Sessões guardadas durante o envio continuam na fila
            this._savePending(keep.concat(this._pending().slice(list.length)));
            this._flushing = false;
        }
        return sent;
    },

    get(path) { return this.request('GET', path); },
    post(path, body) { return this.request('POST', path, body); },
    put(path, body) { return this.request('PUT', path, body); },
    patch(path, body) { return this.request('PATCH', path, body); },
    delete(path) { return this.request('DELETE', path); },
};
