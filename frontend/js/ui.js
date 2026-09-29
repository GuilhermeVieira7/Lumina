// ==========================================
// UI - Utilitários de interface compartilhados
// ==========================================

const UI = {
    AVATARS: ['😊', '🦊', '🐻', '🐼', '🐯', '🦁', '🐸', '🐙', '🦋', '🚀', '🌟', '🌈', '🎨', '⚽', '🦖', '🚂'],

    COMMUNICATION: {
        '': 'Não informado',
        verbal: '🗣️ Fala',
        gestures: '👉 Gestos e apontar',
        pictures: '🖼️ Figuras / pictogramas',
        aac: '📱 Prancha ou app de CAA',
        mixed: '🔀 Um pouco de cada',
    },

    AREA_LABELS: {
        cognicao: '🧠 Cognição',
        comunicacao: '💬 Comunicação',
        socializacao: '🤝 Socialização',
        autonomia: '🏠 Autonomia',
    },

    AREA_COLORS: {
        cognicao: '#6f9fd8',
        comunicacao: '#e8a655',
        socializacao: '#d98aa6',
        autonomia: '#6dbb8f',
    },

    COLOR_NAMES: {
        '#ef4444': 'vermelho', '#3b82f6': 'azul', '#fbbf24': 'amarelo', '#10b981': 'verde',
        '#8b5cf6': 'roxo', '#f97316': 'laranja', '#ec4899': 'rosa', '#93c5fd': 'azul claro',
        '#1e3a8a': 'azul escuro',
    },

    HELP_LEVELS: {
        '': 'Ajuda: não registrada',
        none: '🙌 Sem ajuda',
        verbal: '💬 Dica verbal',
        gesture: '👉 Gesto / apontar',
        physical: '🤝 Ajuda física',
    },

    ROUTINE_EMOJIS: ['🌅', '🪥', '🚿', '🛁', '👕', '🥣', '🍽️', '🍎', '🥤', '🏫', '🎒', '📚', '✏️', '⭐',
        '🧸', '⚽', '🎨', '🎵', '📺', '🌳', '🚗', '🛒', '👨‍👩‍👧', '🩺', '🧩', '😴', '🌙', '🚽'],

    REWARD_EMOJIS: ['🧸', '📺', '🎵', '⚽', '🍪', '🤗', '🛝', '🫧', '📱', '🎨', '🚲', '🧩',
        '🍎', '🍌', '🥤', '🌳', '🚗', '🚂', '🐶', '🐱', '📚', '⭐', '🎮', '🦖'],

    // Telas da criança: nelas aparece o botão "Pedir" e não há funções de adulto
    CHILD_SCREENS: ['child-home', 'activity-screen', 'finish-screen', 'routine-screen', 'progress-screen', 'timer-screen', 'reward-screen', 'mood-screen'],

    esc(value) {
        return String(value ?? '').replace(/[&<>"']/g, c => (
            { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
        ));
    },

    /** Pictograma ARASAAC quando baixado; senão, o próprio emoji. */
    pic(emoji, opts) { return Pictos.html(emoji, opts); },

    showScreen(id) {
        document.querySelectorAll('.screen').forEach(s => s.classList.toggle('active', s.id === id));
        document.body.classList.toggle('child-mode', this.CHILD_SCREENS.includes(id));
        document.dispatchEvent(new CustomEvent('screenchange', { detail: id }));
        window.scrollTo(0, 0);
        const heading = document.querySelector(`#${id} h1, #${id} h2`);
        if (heading) { heading.setAttribute('tabindex', '-1'); heading.focus({ preventScroll: true }); }
    },

    toast(message, type = 'info') {
        const el = document.getElementById('toast');
        el.textContent = message;
        el.className = `toast ${type}`;
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => el.classList.add('hidden'), 4000);
    },

    open(id) {
        const modal = document.getElementById(id);
        modal.classList.remove('hidden');
        const first = modal.querySelector('input, button');
        if (first) first.focus();
    },

    close(id) { document.getElementById(id).classList.add('hidden'); },

    /** Pede a senha da conta; resolve com a senha se estiver correta, ou null. */
    askPassword(reason = 'Digite a senha da conta para continuar.') {
        return new Promise(resolve => {
            const form = document.getElementById('password-form');
            const input = document.getElementById('password-input');
            document.getElementById('password-reason').textContent = reason;
            input.value = '';
            const finish = password => {
                form.onsubmit = null;
                document.getElementById('password-cancel').onclick = null;
                input.value = '';
                this.close('password-modal');
                resolve(password);
            };
            form.onsubmit = async e => {
                e.preventDefault();
                try {
                    await API.post('/auth/verify-password', { password: input.value });
                    finish(input.value);
                } catch (err) {
                    input.value = '';
                    this.toast(err.message, 'error');
                    input.focus();
                }
            };
            document.getElementById('password-cancel').onclick = () => finish(null);
            this.open('password-modal');
        });
    },

    empty(icon, text) {
        return `<div class="empty"><span class="pic" aria-hidden="true">${icon}</span>${this.esc(text)}</div>`;
    },

    formatDate(iso) {
        if (!iso) return '';
        const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
        return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' }) + ' ' +
            d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    },

    formatMinutes(ms) {
        const minutes = Math.round((ms || 0) / 60000);
        return minutes < 60 ? `${minutes} min` : `${Math.floor(minutes / 60)}h ${minutes % 60}min`;
    },

    /** Formulário de perfil da criança (cadastro e edição). */
    renderProfileForm(form, profile, submitLabel) {
        const p = profile || { avatar: '😊' };
        form.innerHTML = `
            <div class="field"><label for="${form.id}-name">Nome ou apelido</label>
                <input id="${form.id}-name" name="name" maxlength="100" required value="${this.esc(p.name)}"></div>
            <div class="field"><span class="label">Avatar</span>
                <div class="emoji-grid" role="group" aria-label="Avatar">
                    ${this.AVATARS.map(a => `<button type="button" data-avatar="${a}" aria-pressed="${a === p.avatar}">${a}</button>`).join('')}
                </div></div>
            <div class="field"><label for="${form.id}-interests">Interesses</label>
                <input id="${form.id}-interests" name="interests" maxlength="300" value="${this.esc(p.interests)}" placeholder="Ex.: dinossauros, trens, música">
                <p class="hint">Usado para sugerir atividades que a criança gosta.</p></div>
            <div class="field"><label for="${form.id}-communication">Como se comunica</label>
                <select id="${form.id}-communication" name="communication">
                    ${Object.entries(this.COMMUNICATION).map(([k, v]) => `<option value="${k}" ${k === (p.communication || '') ? 'selected' : ''}>${v}</option>`).join('')}
                </select></div>
            <div class="field"><label for="${form.id}-sensory">Preferências sensoriais</label>
                <textarea id="${form.id}-sensory" name="sensory_notes" maxlength="300" placeholder="Ex.: incomoda-se com sons altos; prefere cores calmas">${this.esc(p.sensory_notes)}</textarea>
                <p class="hint">Não registre diagnósticos ou laudos: o Lumina guarda só o que ajuda nas atividades.</p></div>
            <div class="actions"><button class="btn" type="submit">${submitLabel}</button></div>`;
        form.dataset.avatar = p.avatar || '😊';
        form.querySelectorAll('[data-avatar]').forEach(btn => btn.addEventListener('click', () => {
            form.dataset.avatar = btn.dataset.avatar;
            form.querySelectorAll('[data-avatar]').forEach(b => b.setAttribute('aria-pressed', b === btn));
        }));
    },

    readProfileForm(form) {
        const data = Object.fromEntries(new FormData(form).entries());
        data.avatar = form.dataset.avatar || '😊';
        data.communication = data.communication || null;
        return data;
    },
};
