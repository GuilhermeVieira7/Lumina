// ==========================================
// ADMIN - Painel dos Adultos (responsáveis e profissionais)
// ==========================================

const Admin = {
    tab: 'dashboard',
    days: 30,
    charts: {},
    routineEmoji: '⭐',
    wired: false,

    get pid() { return App.profile && App.profile.id; },
    get isOwner() { return App.profile && App.profile.is_owner; },

    open(tab) {
        if (!this.wired) this._wire();
        this._renderProfileSelect();
        UI.showScreen('panel-screen');
        this.show(tab || (App.profile ? this.tab : 'settings'));
    },

    _wire() {
        this.wired = true;
        document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => this.show(t.dataset.tab)));
        document.getElementById('panel-back').addEventListener('click', () => { App.renderSelect(); UI.showScreen('select-screen'); });
        document.getElementById('panel-child-btn').addEventListener('click', () => App.enterChild());
        document.getElementById('panel-profile').addEventListener('change', async e => {
            await App.selectProfile(App.profiles.find(p => p.id === Number(e.target.value)));
            this.open(this.tab);
        });
        document.querySelectorAll('[data-days]').forEach(b => b.addEventListener('click', () => {
            this.days = b.dataset.days ? Number(b.dataset.days) : null;
            document.querySelectorAll('[data-days]').forEach(x => x.setAttribute('aria-pressed', x === b));
            this.loadDashboard();
        }));
        document.getElementById('export-pdf').addEventListener('click', () => this.exportPdf());
        document.getElementById('share-whatsapp').addEventListener('click', () => this.shareWhatsApp());
        document.getElementById('diary-form').addEventListener('submit', e => this.addNote(e));
        document.getElementById('goal-form').addEventListener('submit', e => this.addGoal(e));
        document.getElementById('mastery-form').addEventListener('submit', e => this.saveMastery(e));
        document.getElementById('routine-form').addEventListener('submit', e => this.addRoutineItem(e));
        document.getElementById('routine-template').addEventListener('click', () => this.routineTemplate());
        document.getElementById('profile-form').addEventListener('submit', e => this.saveProfile(e));
        document.getElementById('access-form').addEventListener('submit', e => this.invite(e));
        document.getElementById('new-profile-btn').addEventListener('click', () => App.openNewProfile());
        document.getElementById('delete-profile-btn').addEventListener('click', () => this.deleteProfile());
        document.getElementById('delete-account-btn').addEventListener('click', () => this.deleteAccount());
        document.querySelectorAll('[data-theme-choice]').forEach(b => b.addEventListener('click', () => ThemeController.apply(b.dataset.themeChoice)));
        document.getElementById('set-font').addEventListener('change', e => ThemeController.setLargeFont(e.target.checked));
        [['set-sound', 'sound_enabled'], ['set-voice', 'voice_enabled'], ['set-low', 'low_stimulus']].forEach(([id, key]) =>
            document.getElementById(id).addEventListener('change', e => this.saveSetting(key, e.target.checked)));

        const grid = document.getElementById('routine-emoji');
        grid.innerHTML = UI.ROUTINE_EMOJIS.map(e => `<button type="button" data-emoji="${e}" aria-pressed="${e === this.routineEmoji}">${e}</button>`).join('');
        grid.querySelectorAll('[data-emoji]').forEach(b => b.addEventListener('click', () => {
            this.routineEmoji = b.dataset.emoji;
            grid.querySelectorAll('[data-emoji]').forEach(x => x.setAttribute('aria-pressed', x === b));
        }));
    },

    _renderProfileSelect() {
        const select = document.getElementById('panel-profile');
        select.innerHTML = App.profiles.map(p =>
            `<option value="${p.id}" ${App.profile && p.id === App.profile.id ? 'selected' : ''}>${UI.esc(p.avatar)} ${UI.esc(p.name)}</option>`).join('');
        select.classList.toggle('hidden', !App.profiles.length);
        document.getElementById('panel-shared').textContent = App.profile && !App.profile.is_owner
            ? `Compartilhado por ${App.profile.owner_name}` : '';
        document.getElementById('panel-child-btn').classList.toggle('hidden', !App.profile);

        // Sem criança: só Ajustes (convites) e, para responsáveis, o cadastro
        document.querySelectorAll('.tab').forEach(t => {
            const needsProfile = !['settings', 'profile'].includes(t.dataset.tab);
            t.classList.toggle('hidden', !App.profile && (needsProfile || (t.dataset.tab === 'profile' && App.user.role === 'therapist')));
        });
        document.querySelector('[data-tab="profile"]').innerHTML = this.isOwner || !App.profile
            ? '<span aria-hidden="true">👤</span> Perfil e acesso' : '<span aria-hidden="true">👤</span> Perfil';
    },

    show(tab) {
        this.tab = tab;
        document.querySelectorAll('.tab').forEach(t => t.setAttribute('aria-selected', t.dataset.tab === tab));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === `tab-${tab}`));
        const loaders = {
            dashboard: () => this.loadDashboard(),
            sessions: () => this.loadSessions(),
            recs: () => this.loadRecs(),
            diary: () => this.loadDiary(),
            goals: () => this.loadGoals(),
            plan: () => this.loadPlan(),
            routine: () => this.loadRoutine(),
            profile: () => this.loadProfile(),
            settings: () => this.loadSettings(),
        };
        if (this.pid || tab === 'settings' || tab === 'profile') loaders[tab]();
        if (this.pid && tab !== 'recs') this._updateRecsCount();
    },

    _fail(err) { UI.toast(err.message, 'error'); },

    // ---------- Progresso ----------
    async loadDashboard() {
        const q = this.days ? `&days=${this.days}` : '';
        try {
            const [stats, sessions] = await Promise.all([
                API.get(`/sessions/stats?profile_id=${this.pid}${q}`),
                API.get(`/sessions?profile_id=${this.pid}&limit=60&include_practice=false${q}`),
            ]);
            const stat = (pic, label, value) =>
                `<div class="stat"><span class="pic" aria-hidden="true">${pic}</span><div><div class="label">${label}</div><div class="value">${value}</div></div></div>`;
            document.getElementById('stats').innerHTML =
                stat('🧩', 'Atividades', stats.total_activities) +
                stat('🎯', 'Acerto de primeira', `${stats.accuracy}%`) +
                stat('⏱️', 'Tempo de prática', UI.formatMinutes(stats.total_time)) +
                stat('⭐', 'Estrelas', stats.total_stars) +
                stat('🔁', 'Tentativas por questão', stats.avg_attempts);
            this._charts(stats, sessions.slice().reverse());
        } catch (err) { this._fail(err); }
    },

    _charts(stats, sessions) {
        if (!window.Chart) return;
        Object.values(this.charts).forEach(c => c.destroy());
        const css = getComputedStyle(document.documentElement);
        const text = css.getPropertyValue('--text-soft').trim();
        const grid = css.getPropertyValue('--border').trim();
        Chart.defaults.color = text;
        Chart.defaults.font.family = 'Nunito, sans-serif';
        const pct = { y: { beginAtZero: true, max: 100, grid: { color: grid }, ticks: { callback: v => v + '%' } }, x: { grid: { display: false } } };
        const noAnim = document.body.classList.contains('low-stimulus') ? { animation: false } : {};

        const areas = Object.entries(stats.areas_breakdown);
        this.charts.areas = new Chart(document.getElementById('chart-areas'), {
            type: 'bar',
            data: {
                labels: areas.map(([k]) => UI.AREA_LABELS[k] || k),
                datasets: [{
                    data: areas.map(([, a]) => a.accuracy ?? 0),
                    backgroundColor: areas.map(([k]) => UI.AREA_COLORS[k]),
                    borderRadius: 8,
                }],
            },
            options: { responsive: true, maintainAspectRatio: false, scales: pct, plugins: { legend: { display: false },
                tooltip: { callbacks: { label: c => areas[c.dataIndex][1].accuracy === null ? 'Sem registros' : `${c.raw}% · ${areas[c.dataIndex][1].sessions} sessões` } } }, ...noAnim },
        });

        this.charts.timeline = new Chart(document.getElementById('chart-timeline'), {
            type: 'line',
            data: {
                labels: sessions.map(s => UI.formatDate(s.created_at)),
                datasets: [{
                    data: sessions.map(s => s.accuracy),
                    borderColor: '#4d74c9', backgroundColor: 'rgba(77,116,201,.12)',
                    fill: true, tension: .3, pointRadius: 4,
                }],
            },
            options: { responsive: true, maintainAspectRatio: false, scales: { ...pct, x: { grid: { display: false }, ticks: { maxTicksLimit: 6 } } },
                plugins: { legend: { display: false }, tooltip: { callbacks: {
                    title: c => `${App.activities[sessions[c[0].dataIndex].activity_type]?.name || ''} · ${c[0].label}`,
                    label: c => `${c.raw}% de acerto` } } }, ...noAnim },
        });

        const acts = Object.values(stats.activities_breakdown);
        this.charts.activities = new Chart(document.getElementById('chart-activities'), {
            type: 'bar',
            data: {
                labels: acts.map(a => a.name),
                datasets: [{ data: acts.map(a => a.accuracy), backgroundColor: acts.map(a => UI.AREA_COLORS[a.area]), borderRadius: 8 }],
            },
            options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                scales: { x: pct.y, y: { grid: { display: false } } }, plugins: { legend: { display: false } }, ...noAnim },
        });
    },

    async exportPdf() {
        try {
            UI.toast('Gerando relatório…');
            const q = this.days ? `&days=${this.days}` : '';
            const res = await fetch(`/api/sessions/export/pdf?profile_id=${this.pid}${q}`, {
                headers: { Authorization: `Bearer ${API.token}` },
            });
            if (!res.ok) throw new Error('Não foi possível gerar o PDF');
            const url = URL.createObjectURL(await res.blob());
            const a = document.createElement('a');
            a.href = url;
            a.download = `relatorio_lumina_${App.profile.name.replace(/\W+/g, '_')}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
            UI.toast('Relatório baixado 📄', 'success');
        } catch (err) { this._fail(err); }
    },

    async shareWhatsApp() {
        try {
            const q = this.days ? `&days=${this.days}` : '';
            const s = await API.get(`/sessions/stats?profile_id=${this.pid}${q}`);
            const period = this.days ? `últimos ${this.days} dias` : 'todo o período';
            const text = `🦊 *Lumina: ${App.profile.name}* (${period})\n\n` +
                `🧩 Atividades: ${s.total_activities}\n🎯 Acerto de primeira: ${s.accuracy}%\n` +
                `⭐ Estrelas: ${s.total_stars}\n⏱️ Tempo de prática: ${UI.formatMinutes(s.total_time)}`;
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
        } catch (err) { this._fail(err); }
    },

    // ---------- Sessões (nível de ajuda) ----------
    async loadSessions() {
        const box = document.getElementById('sessions-list');
        try {
            const sessions = await API.get(`/sessions?profile_id=${this.pid}&limit=30`);
            if (!sessions.length) { box.innerHTML = UI.empty('🕒', 'Nenhuma sessão registrada ainda.'); return; }
            box.innerHTML = sessions.map(s => {
                const a = App.activities[s.activity_type] || {};
                return `<div class="row">
                    <span class="pic" aria-hidden="true">${a.icon || '⭐'}</span>
                    <div class="grow"><b>${UI.esc(a.name || s.activity_type)}</b> ${s.is_practice ? '<span class="pill info">treino</span>' : ''}
                        <div class="meta">${UI.formatDate(s.created_at)} · nível ${s.level} · ${s.accuracy}% de acerto · ${'⭐'.repeat(s.stars) || 'sem estrelas'}</div></div>
                    <label class="sr-only" for="help-${s.id}">Ajuda dada</label>
                    <select id="help-${s.id}" data-help="${s.id}">
                        ${Object.entries(UI.HELP_LEVELS).map(([k, v]) => `<option value="${k}" ${k === (s.help_level || '') ? 'selected' : ''} ${k === '' ? 'disabled' : ''}>${v}</option>`).join('')}
                    </select>
                    <button class="btn btn-soft btn-small" data-note="${s.id}">📝 Observação</button>
                </div>`;
            }).join('');
            box.querySelectorAll('[data-help]').forEach(sel => sel.addEventListener('change', async () => {
                try {
                    await API.patch(`/sessions/${sel.dataset.help}`, { help_level: sel.value });
                    UI.toast('Nível de ajuda salvo', 'success');
                } catch (err) { this._fail(err); }
            }));
            box.querySelectorAll('[data-note]').forEach(b => b.addEventListener('click', () => {
                const row = b.closest('.row');
                if (row.querySelector('form')) return;
                const form = document.createElement('form');
                form.style.cssText = 'flex-basis:100%;display:flex;gap:10px;flex-wrap:wrap';
                form.innerHTML = `<label class="sr-only" for="sn-${b.dataset.note}">Observação</label>
                    <textarea id="sn-${b.dataset.note}" class="input" style="flex:1;min-width:220px" maxlength="2000" required placeholder="Como foi esta sessão?"></textarea>
                    <button class="btn btn-small" type="submit">Salvar no diário</button>`;
                row.appendChild(form);
                form.querySelector('textarea').focus();
                form.addEventListener('submit', async e => {
                    e.preventDefault();
                    try {
                        await API.post('/notes', { profile_id: this.pid, session_id: Number(b.dataset.note), content: form.querySelector('textarea').value.trim() });
                        form.remove();
                        UI.toast('Observação salva no diário 📓', 'success');
                    } catch (err) { this._fail(err); }
                });
            }));
        } catch (err) { this._fail(err); }
    },

    // ---------- Recomendações ----------
    async _updateRecsCount() {
        try {
            const recs = await API.get(`/ai/recommendations/${this.pid}`);
            const pill = document.getElementById('recs-count');
            pill.textContent = recs.length;
            pill.classList.toggle('hidden', !recs.length);
            return recs;
        } catch { return []; }
    },

    async loadRecs() {
        const box = document.getElementById('recs-list');
        const recs = await this._updateRecsCount();
        if (!recs.length) {
            box.innerHTML = UI.empty('✅', 'Nenhuma recomendação pendente. Novas sugestões aparecem conforme a criança pratica.');
            return;
        }
        const icons = { positive: '📈', attention: '🤝', pattern: '🔎', suggestion: '⭐', general: '💡' };
        box.innerHTML = recs.map((r, i) => {
            const act = App.activities[r.activity];
            const sameLevel = r.kind === 'level' && r.suggested_level === r.current_level;
            const levelSelect = r.kind === 'level' && act && !sameLevel
                ? `<label class="sr-only" for="rec-level-${i}">Nível</label>
                   <select id="rec-level-${i}" class="input" style="width:auto;min-height:44px">
                     ${act.levels.map(l => `<option value="${l}" ${l === (r.suggested_level || 1) ? 'selected' : ''}>Nível ${l}</option>`).join('')}
                   </select>
                   <button class="btn btn-soft btn-small" data-rec="${i}" data-action="adjust">✏️ Usar este nível</button>` : '';
            const acceptLabel = sameLevel ? '👍 Ciente, vou dar mais apoio' : r.kind === 'level' ? `✅ Aceitar nível ${r.suggested_level}` : r.kind === 'activity' ? '⭐ Destacar para a criança' : '👍 Ciente';
            return `<div class="card rec-card ${r.type}">
                <h3><span aria-hidden="true">${icons[r.type] || '💡'}</span>${act ? `<span aria-hidden="true">${act.icon}</span>` : ''} ${UI.esc(r.title)}</h3>
                <ul>${r.reasons.map(x => `<li>${UI.esc(x)}</li>`).join('')}</ul>
                ${r.kind === 'activity' ? `<p class="shared-note" style="margin-bottom:10px">${UI.esc(r.message)}</p>` : ''}
                <div class="rec-actions">
                    <button class="btn btn-small" data-rec="${i}" data-action="accept">${acceptLabel}</button>
                    ${levelSelect}
                    <button class="btn btn-outline btn-small" data-rec="${i}" data-action="dismiss">✖️ Descartar</button>
                </div></div>`;
        }).join('');
        box.querySelectorAll('[data-rec]').forEach(b => b.addEventListener('click', async () => {
            const r = recs[Number(b.dataset.rec)];
            const body = { key: r.key, activity_type: r.activity, action: b.dataset.action };
            if (b.dataset.action === 'adjust') body.level = Number(document.getElementById(`rec-level-${b.dataset.rec}`).value);
            try {
                await API.post(`/ai/recommendations/${this.pid}/decide`, body);
                UI.toast({ accept: 'Recomendação aceita', adjust: 'Nível ajustado', dismiss: 'Recomendação descartada' }[b.dataset.action], 'success');
                this.loadRecs();
            } catch (err) { this._fail(err); }
        }));
    },

    // ---------- Diário ----------
    async loadDiary() {
        const box = document.getElementById('diary-list');
        try {
            const notes = await API.get(`/notes/${this.pid}`);
            box.innerHTML = notes.length ? notes.map(n => `
                <div class="row">
                    <span class="pic" aria-hidden="true">${n.activity_type ? (App.activities[n.activity_type]?.icon || '📝') : '📝'}</span>
                    <div class="grow"><div class="meta">${UI.formatDate(n.created_at)} · ${UI.esc(n.author)}${n.activity_type ? ' · ' + UI.esc(App.activities[n.activity_type]?.name || '') : ''}</div>
                        <div style="white-space:pre-wrap">${UI.esc(n.content)}</div></div>
                    ${n.author_id === App.user.id || this.isOwner ? `<button class="btn btn-outline btn-small" data-del-note="${n.id}" aria-label="Apagar observação">🗑️</button>` : ''}
                </div>`).join('') : UI.empty('📓', 'Nenhuma observação ainda. Registre o que funcionou em casa, na escola ou na clínica.');
            box.querySelectorAll('[data-del-note]').forEach(b => b.addEventListener('click', async () => {
                if (!confirm('Apagar esta observação?')) return;
                try { await API.delete(`/notes/${b.dataset.delNote}`); this.loadDiary(); } catch (err) { this._fail(err); }
            }));
        } catch (err) { this._fail(err); }
    },

    async addNote(e) {
        e.preventDefault();
        const input = document.getElementById('diary-text');
        if (!input.value.trim()) return;
        try {
            await API.post('/notes', { profile_id: this.pid, content: input.value.trim() });
            input.value = '';
            UI.toast('Observação salva', 'success');
            this.loadDiary();
        } catch (err) { this._fail(err); }
    },

    // ---------- Metas ----------
    async loadGoals() {
        const select = document.getElementById('goal-activity');
        select.innerHTML = Object.values(App.activities).map(a => `<option value="${a.type}">${a.icon} ${UI.esc(a.name)}</option>`).join('');
        const box = document.getElementById('goals-list');
        const unit = { accuracy: '%', sessions: ' sessões', stars: ' estrelas' };
        try {
            const goals = await API.get(`/goals/${this.pid}`);
            box.innerHTML = goals.length ? goals.map(g => {
                const a = App.activities[g.activity_type] || {};
                const pct = Math.min(100, Math.round((g.current_value / g.target_value) * 100));
                return `<div class="row">
                    <span class="pic" aria-hidden="true">${g.completed ? '🏆' : a.icon || '🎯'}</span>
                    <div class="grow"><b>${UI.esc(a.name || g.activity_type)}</b>: ${UI.esc(g.description || '')}
                        ${g.completed ? '<span class="pill ok">concluída</span>' : ''}
                        <div class="meta">${g.current_value}${unit[g.target_type]} de ${g.target_value}${unit[g.target_type]}</div>
                        <div class="progress" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><i style="width:${pct}%"></i></div></div>
                    <button class="btn btn-outline btn-small" data-del-goal="${g.id}" aria-label="Apagar meta">🗑️</button>
                </div>`;
            }).join('') : UI.empty('🎯', 'Nenhuma meta ainda. Metas abertas também influenciam as recomendações.');
            box.querySelectorAll('[data-del-goal]').forEach(b => b.addEventListener('click', async () => {
                if (!confirm('Apagar esta meta?')) return;
                try { await API.delete(`/goals/${b.dataset.delGoal}`); this.loadGoals(); } catch (err) { this._fail(err); }
            }));
        } catch (err) { this._fail(err); }
    },

    async addGoal(e) {
        e.preventDefault();
        try {
            await API.post('/goals', {
                profile_id: this.pid,
                activity_type: document.getElementById('goal-activity').value,
                target_type: document.getElementById('goal-type').value,
                target_value: Number(document.getElementById('goal-target').value),
                description: document.getElementById('goal-desc').value.trim() || null,
            });
            document.getElementById('goal-desc').value = '';
            UI.toast('Meta criada', 'success');
            this.loadGoals();
        } catch (err) { this._fail(err); }
    },

    // ---------- Plano de atividades ----------
    async loadPlan() {
        const box = document.getElementById('plan-list');
        try {
            const plan = await API.get(`/plans/${this.pid}`);
            box.innerHTML = plan.map(a => `
                <div class="row">
                    <span class="pic" aria-hidden="true">${a.icon}</span>
                    <div class="grow"><b>${UI.esc(a.name)}</b><div class="meta">${UI.AREA_LABELS[a.area]}</div></div>
                    <label class="check" style="align-items:center"><input type="checkbox" data-plan="${a.activity_type}" data-field="enabled" ${a.enabled ? 'checked' : ''}> Aparece</label>
                    <label class="sr-only" for="lvl-${a.activity_type}">Nível</label>
                    <select id="lvl-${a.activity_type}" data-plan="${a.activity_type}" data-field="level">
                        ${Array.from({ length: a.max_level }, (_, i) => `<option value="${i + 1}" ${i + 1 === a.level ? 'selected' : ''}>Nível ${i + 1}</option>`).join('')}
                    </select>
                    <label class="sr-only" for="qc-${a.activity_type}">Etapas</label>
                    <select id="qc-${a.activity_type}" data-plan="${a.activity_type}" data-field="question_count">
                        ${[2, 3, 4, 5].map(n => `<option value="${n}" ${n === a.question_count ? 'selected' : ''}>${n} etapas</option>`).join('')}
                    </select>
                    <button class="btn ${a.recommended ? '' : 'btn-outline'} btn-small" data-plan="${a.activity_type}" data-field="recommended"
                        aria-pressed="${a.recommended}" aria-label="Destacar ${UI.esc(a.name)}">⭐</button>
                </div>`).join('');
            box.querySelectorAll('[data-plan]').forEach(el => {
                const evt = el.tagName === 'BUTTON' ? 'click' : 'change';
                el.addEventListener(evt, async () => {
                    let value;
                    if (el.dataset.field === 'enabled') value = el.checked;
                    else if (el.dataset.field === 'recommended') value = el.getAttribute('aria-pressed') !== 'true';
                    else value = Number(el.value);
                    try {
                        await API.put(`/plans/${this.pid}/${el.dataset.plan}`, { [el.dataset.field]: value });
                        this.loadPlan();
                    } catch (err) { this._fail(err); }
                });
            });
            const s = App.settings || {};
            document.getElementById('mastery-threshold').value = s.mastery_threshold || 85;
            document.getElementById('mastery-sessions').value = s.mastery_sessions || 3;
        } catch (err) { this._fail(err); }
    },

    async saveMastery(e) {
        e.preventDefault();
        try {
            App.settings = await API.put(`/settings/${this.pid}`, {
                mastery_threshold: Number(document.getElementById('mastery-threshold').value),
                mastery_sessions: Number(document.getElementById('mastery-sessions').value),
            });
            UI.toast('Critério salvo', 'success');
        } catch (err) { this._fail(err); }
    },

    // ---------- Rotina ----------
    async loadRoutine() {
        const box = document.getElementById('routine-list');
        try {
            const items = await API.get(`/routine/${this.pid}`);
            document.getElementById('routine-template').classList.toggle('hidden', items.length > 0);
            box.innerHTML = items.length ? items.map((i, idx) => `
                <div class="row">
                    <span class="pic" aria-hidden="true">${UI.esc(i.icon)}</span>
                    <div class="grow"><b>${UI.esc(i.label)}</b> ${i.done_today ? '<span class="pill ok">feito hoje</span>' : ''}
                        <div class="meta">${i.time ? UI.esc(i.time) : 'sem horário'}</div></div>
                    <button class="btn btn-outline btn-small" data-move="${i.id}" data-pos="${idx - 1}" ${idx === 0 ? 'disabled' : ''} aria-label="Subir">⬆️</button>
                    <button class="btn btn-outline btn-small" data-move="${i.id}" data-pos="${idx + 1}" ${idx === items.length - 1 ? 'disabled' : ''} aria-label="Descer">⬇️</button>
                    <button class="btn btn-outline btn-small" data-del-routine="${i.id}" aria-label="Remover">🗑️</button>
                </div>`).join('') : UI.empty('📅', 'A rotina está vazia. Crie etapas ou use a rotina de exemplo.');
            box.querySelectorAll('[data-move]').forEach(b => b.addEventListener('click', async () => {
                try { await API.put(`/routine/${b.dataset.move}`, { position: Number(b.dataset.pos) }); this.loadRoutine(); } catch (err) { this._fail(err); }
            }));
            box.querySelectorAll('[data-del-routine]').forEach(b => b.addEventListener('click', async () => {
                try { await API.delete(`/routine/${b.dataset.delRoutine}`); this.loadRoutine(); } catch (err) { this._fail(err); }
            }));
        } catch (err) { this._fail(err); }
    },

    async addRoutineItem(e) {
        e.preventDefault();
        const label = document.getElementById('routine-label');
        const time = document.getElementById('routine-time');
        try {
            await API.post('/routine', { profile_id: this.pid, icon: this.routineEmoji, label: label.value.trim(), time: time.value || null });
            label.value = '';
            time.value = '';
            this.loadRoutine();
        } catch (err) { this._fail(err); }
    },

    async routineTemplate() {
        try { await API.post(`/routine/${this.pid}/template`); this.loadRoutine(); } catch (err) { this._fail(err); }
    },

    // ---------- Perfil e acesso ----------
    async loadProfile() {
        const form = document.getElementById('profile-form');
        const owner = this.isOwner;
        document.getElementById('access-card').classList.toggle('hidden', !owner);
        document.getElementById('delete-profile-btn').classList.toggle('hidden', !owner);
        document.getElementById('new-profile-btn').classList.toggle('hidden', App.user.role === 'therapist');
        if (!App.profile) {
            form.innerHTML = UI.empty('🧒', 'Nenhuma criança cadastrada ainda.');
            return;
        }
        UI.renderProfileForm(form, App.profile, '💾 Salvar perfil');
        if (!owner) {
            form.querySelectorAll('input, select, textarea, button').forEach(el => { el.disabled = true; });
            form.querySelector('.actions').innerHTML = '<p class="shared-note">Só o responsável edita o perfil.</p>';
            return;
        }
        this.loadAccess();
    },

    async saveProfile(e) {
        e.preventDefault();
        try {
            const updated = await API.put(`/profiles/${this.pid}`, UI.readProfileForm(e.target));
            Object.assign(App.profile, updated);
            this._renderProfileSelect();
            UI.toast('Perfil salvo', 'success');
        } catch (err) { this._fail(err); }
    },

    async loadAccess() {
        const box = document.getElementById('access-list');
        const labels = { pending: '<span class="pill warn">aguardando aceite</span>', active: '<span class="pill ok">com acesso</span>', revoked: '<span class="pill off">revogado</span>' };
        try {
            const rows = await API.get(`/access/profile/${this.pid}`);
            box.innerHTML = rows.length ? rows.map(r => `
                <div class="row">
                    <span class="pic" aria-hidden="true">🧑‍🏫</span>
                    <div class="grow"><b>${UI.esc(r.professional_name)}</b> ${labels[r.status] || ''}</div>
                    ${r.status !== 'revoked' ? `<button class="btn btn-danger btn-small" data-revoke="${r.id}">Revogar</button>` : ''}
                </div>`).join('') : UI.empty('🔐', 'Ninguém além de você acessa os dados desta criança.');
            box.querySelectorAll('[data-revoke]').forEach(b => b.addEventListener('click', async () => {
                if (!confirm('Revogar o acesso deste profissional agora?')) return;
                try { await API.delete(`/access/${b.dataset.revoke}`); UI.toast('Acesso revogado', 'success'); this.loadAccess(); } catch (err) { this._fail(err); }
            }));
        } catch (err) { this._fail(err); }
    },

    async invite(e) {
        e.preventDefault();
        const input = document.getElementById('access-who');
        try {
            await API.post('/access', { profile_id: this.pid, professional: input.value.trim() });
            input.value = '';
            UI.toast('Convite enviado. O profissional precisa aceitar.', 'success');
            this.loadAccess();
        } catch (err) { this._fail(err); }
    },

    async deleteProfile() {
        if (!(await UI.askPassword(`Excluir ${App.profile.name} apaga todas as sessões, notas e rotina. Digite a senha para confirmar.`))) return;
        try {
            await API.delete(`/profiles/${this.pid}`);
            localStorage.removeItem('tea_profile_id');
            UI.toast('Criança e dados excluídos', 'success');
            await App.loadProfiles();
            this.open(App.profile ? 'dashboard' : 'profile');
        } catch (err) { this._fail(err); }
    },

    // ---------- Ajustes ----------
    async loadSettings() {
        const s = App.settings || {};
        document.getElementById('set-sound').checked = s.sound_enabled !== false;
        document.getElementById('set-voice').checked = !!s.voice_enabled;
        document.getElementById('set-low').checked = !!s.low_stimulus;
        document.getElementById('set-font').checked = document.documentElement.classList.contains('font-large');
        ['set-sound', 'set-voice', 'set-low'].forEach(id => { document.getElementById(id).disabled = !this.pid; });
        ThemeController.apply(ThemeController.current);
        const roles = { parent: 'Responsável', admin: 'Responsável', therapist: 'Profissional' };
        document.getElementById('account-info').textContent =
            `Conta: ${App.user.username} (${roles[App.user.role] || App.user.role}).` +
            (App.user.consent_at ? ` Consentimento registrado em ${UI.formatDate(App.user.consent_at).split(' ')[0]}.` : '');

        const invitesCard = document.getElementById('invites-card');
        invitesCard.classList.toggle('hidden', App.user.role !== 'therapist');
        if (App.user.role !== 'therapist') return;
        const box = document.getElementById('invites-list');
        try {
            const invites = await API.get('/access/invites');
            box.innerHTML = invites.length ? invites.map(i => `
                <div class="row">
                    <span class="pic" aria-hidden="true">🧒</span>
                    <div class="grow"><b>${UI.esc(i.profile_name)}</b><div class="meta">convite de ${UI.esc(i.owner_name)}</div></div>
                    ${i.status === 'pending'
                        ? `<button class="btn btn-small" data-accept="${i.id}">Aceitar</button><button class="btn btn-outline btn-small" data-decline="${i.id}">Recusar</button>`
                        : '<span class="pill ok">com acesso</span>'}
                </div>`).join('') : UI.empty('✉️', 'Nenhum convite no momento.');
            box.querySelectorAll('[data-accept]').forEach(b => b.addEventListener('click', async () => {
                try { await API.post(`/access/${b.dataset.accept}/accept`); await App.loadProfiles(); this.open('settings'); } catch (err) { this._fail(err); }
            }));
            box.querySelectorAll('[data-decline]').forEach(b => b.addEventListener('click', async () => {
                try { await API.post(`/access/${b.dataset.decline}/decline`); this.loadSettings(); } catch (err) { this._fail(err); }
            }));
        } catch (err) { this._fail(err); }
    },

    async saveSetting(key, value) {
        try {
            App.settings = await API.put(`/settings/${this.pid}`, { [key]: value });
            App.applySettings();
            UI.toast('Ajuste salvo para esta criança', 'success');
        } catch (err) { this._fail(err); }
    },

    async deleteAccount() {
        const password = await UI.askPassword('Isto exclui sua conta e todos os dados das crianças que você cadastrou. Não dá para desfazer. Digite a senha para confirmar.');
        if (!password) return;
        try {
            await API.post('/auth/delete-account', { password });
            AuthController.logout();
            UI.toast('Conta e dados excluídos', 'success');
        } catch (err) { this._fail(err); }
    },
};
