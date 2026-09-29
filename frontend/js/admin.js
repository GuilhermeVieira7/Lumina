// ==========================================
// ADMIN - Painel dos Adultos (responsáveis e profissionais)
// ==========================================

const Admin = {
    tab: 'dashboard',
    days: 30,
    charts: {},
    routineEmoji: '⭐',
    rewardEmoji: '🧸',
    DURATIONS: [1, 2, 3, 5, 10, 15, 20, 30, 45, 60],
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
        // Quatro seções (abas) e, dentro de cada uma, suas partes (subabas)
        document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => this.showGroup(t.dataset.group)));
        document.querySelectorAll('.tabs').forEach(list => list.addEventListener('keydown', e => {
            if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
            const tabs = [...list.querySelectorAll('.tab:not(.hidden)')];
            const i = tabs.indexOf(document.activeElement);
            if (i < 0) return;
            const next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
            next.focus();
            next.click();
        }));
        document.querySelectorAll('.subtabs [data-tab]').forEach(b => b.addEventListener('click', () => this.show(b.dataset.tab)));
        document.getElementById('panel-back').addEventListener('click', () => { App.renderSelect(); UI.showScreen('select-screen'); });
        document.getElementById('panel-child-btn').addEventListener('click', () => App.enterChild());
        document.getElementById('panel-profile').addEventListener('click', async e => {
            const btn = e.target.closest('[data-kid]');
            if (!btn || (App.profile && Number(btn.dataset.kid) === App.profile.id)) return;
            await App.selectProfile(App.profiles.find(p => p.id === Number(btn.dataset.kid)));
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
        [['set-sound', 'sound_enabled'], ['set-voice', 'voice_enabled'], ['set-low', 'low_stimulus'],
            ['set-tokens', 'token_board'], ['set-requests', 'request_board'], ['set-mood', 'mood_checkin']].forEach(([id, key]) =>
            document.getElementById(id).addEventListener('change', e => this.saveSetting(key, e.target.checked)));
        document.getElementById('reward-form').addEventListener('submit', e => this.addReward(e));

        this._emojiPicker('routine-emoji', UI.ROUTINE_EMOJIS, 'routineEmoji');
        this._emojiPicker('reward-emoji', UI.REWARD_EMOJIS, 'rewardEmoji');
        document.getElementById('routine-duration').innerHTML = this._durationOptions(null);
    },

    _emojiPicker(id, emojis, field) {
        const grid = document.getElementById(id);
        grid.innerHTML = emojis.map(e => `<button type="button" data-emoji="${e}" aria-label="${e}" aria-pressed="${e === this[field]}">${UI.pic(e)}</button>`).join('');
        grid.querySelectorAll('[data-emoji]').forEach(b => b.addEventListener('click', () => {
            this[field] = b.dataset.emoji;
            grid.querySelectorAll('[data-emoji]').forEach(x => x.setAttribute('aria-pressed', x === b));
        }));
    },

    _durationOptions(selected, noneLabel = 'Sem timer') {
        return `<option value="0" ${!selected ? 'selected' : ''}>${noneLabel}</option>` +
            this.DURATIONS.map(m => `<option value="${m}" ${m === selected ? 'selected' : ''}>⏳ ${m} min</option>`).join('');
    },

    _renderProfileSelect() {
        // Uma foto por criança: um toque troca a criança do painel
        const row = document.getElementById('panel-profile');
        row.innerHTML = App.profiles.map(p => `
            <button class="kid-chip" data-kid="${p.id}" aria-pressed="${!!(App.profile && p.id === App.profile.id)}">
                <span class="avatar" aria-hidden="true">${UI.avatar(p)}</span>${UI.esc(p.name)}
            </button>`).join('');
        row.classList.toggle('hidden', !App.profiles.length);
        document.getElementById('panel-shared').textContent = App.profile && !App.profile.is_owner
            ? `Compartilhado por ${App.profile.owner_name}` : '';
        document.getElementById('panel-child-btn').classList.toggle('hidden', !App.profile);

        // Sem criança: só Ajustes (preferências e, para responsáveis, o cadastro)
        const therapist = App.user.role === 'therapist';
        document.querySelectorAll('.subtabs [data-tab]').forEach(b => {
            const t = b.dataset.tab;
            b.dataset.off = !App.profile && (!['settings', 'profile'].includes(t) || (t === 'profile' && therapist)) ? '1' : '';
        });
        document.querySelectorAll('.tab').forEach(t => t.classList.toggle('hidden', !App.profile && t.dataset.group !== 'config'));
        document.querySelector('.subtabs [data-tab="profile"]').textContent = this.isOwner || !App.profile ? 'Criança e acesso' : 'Criança';
    },

    GROUPS: {
        dashboard: 'progress', recs: 'progress',
        sessions: 'diary', diary: 'diary',
        plan: 'plan', routine: 'plan', goals: 'plan',
        profile: 'config', settings: 'config',
    },
    lastInGroup: {},

    showGroup(group) {
        const available = [...document.querySelectorAll(`.subtabs [data-in="${group}"]`)].filter(b => !b.dataset.off).map(b => b.dataset.tab);
        const remembered = this.lastInGroup[group];
        this.show(available.includes(remembered) ? remembered : available[0]);
    },

    show(tab) {
        if (!App.profile && !['settings', 'profile'].includes(tab)) tab = 'settings';
        if (tab === 'profile' && !App.profile && App.user.role === 'therapist') tab = 'settings';
        const group = this.GROUPS[tab];
        this.tab = tab;
        this.lastInGroup[group] = tab;
        document.querySelectorAll('.tab').forEach(t => {
            const on = t.dataset.group === group;
            t.setAttribute('aria-selected', on);
            t.tabIndex = on ? 0 : -1;
        });
        const subs = [...document.querySelectorAll('.subtabs [data-tab]')];
        subs.forEach(b => {
            b.hidden = b.dataset.in !== group || !!b.dataset.off;
            b.setAttribute('aria-pressed', b.dataset.tab === tab);
        });
        // Uma parte só: não precisa mostrar a linha de subabas
        document.querySelector('.subtabs').classList.toggle('hidden', subs.filter(b => !b.hidden).length < 2);
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
        const tz = new Date().getTimezoneOffset();
        try {
            const [summary, stats, moods] = await Promise.all([
                API.get(`/summary/${this.pid}?${this.days ? `days=${this.days}` : 'all_time=true'}&tz=${tz}`),
                API.get(`/sessions/stats?profile_id=${this.pid}${q}`),
                API.get(`/moods/${this.pid}?days=${this.days || 90}&limit=1&tz=${tz}`),
            ]);
            this.summary = summary;
            this._renderSummary(summary);
            this._charts(stats, summary.daily);
            this._moodChart(moods);
        } catch (err) { this._fail(err); }
    },

    /** Topo do Progresso: uma frase em linguagem simples e os três números que importam. */
    _renderSummary(s) {
        const change = s.accuracy_change;
        const trend = change === null || s.accuracy === null ? ''
            : Math.abs(change) < 3 ? '<span class="pill info">estável</span>'
            : `<span class="pill ${change > 0 ? 'ok' : 'warn'}"><span aria-hidden="true">${change > 0 ? '▲' : '▼'}</span> ${Math.abs(Math.round(change))} pontos</span>`;
        const big = (pic, value, label, extra = '') =>
            `<div class="big-num"><span class="pic" aria-hidden="true">${pic}</span><b>${value}</b><span>${label}</span>${extra}</div>`;
        const extras = [
            ['⭐', `${s.stars} ${s.stars === 1 ? 'estrela' : 'estrelas'}`],
            ['📅', `${s.active_days} ${s.active_days === 1 ? 'dia com atividade' : 'dias com atividade'}`],
            ['💬', `${s.requests} ${s.requests === 1 ? 'pedido' : 'pedidos'} na prancha`],
            ['🙂', `${s.moods} ${s.moods === 1 ? 'emoção registrada' : 'emoções registradas'}`],
        ];
        document.getElementById('summary').innerHTML = `
            <p class="headline">${UI.esc(s.headline)}</p>
            <div class="big-nums">
                ${big('🧩', s.activities, s.activities === 1 ? 'atividade' : 'atividades')}
                ${big('🎯', s.accuracy === null ? '–' : `${Math.round(s.accuracy)}%`, 'acerto de primeira', trend)}
                ${big('⏱️', UI.formatMinutes(s.minutes * 60000), 'de prática')}
            </div>
            <ul class="summary-extra">${extras.map(([pic, text]) => `<li><span aria-hidden="true">${pic}</span> ${text}</li>`).join('')}</ul>`;
    },

    _charts(stats, daily) {
        if (!window.Chart) return;
        Object.values(this.charts).forEach(c => c.destroy());
        this.charts = {};
        const css = getComputedStyle(document.documentElement);
        const text = css.getPropertyValue('--text-soft').trim();
        const grid = css.getPropertyValue('--border').trim();
        Chart.defaults.color = text;
        Chart.defaults.font.family = 'Nunito, sans-serif';
        const pct = { y: { beginAtZero: true, max: 100, grid: { color: grid }, ticks: { callback: v => v + '%' } }, x: { grid: { display: false } } };
        const noAnim = document.body.classList.contains('low-stimulus') ? { animation: false } : {};
        const dayLabel = iso => { const [, m, d] = iso.split('-'); return `${d}/${m}`; };

        // Evolução: um ponto por dia com atividade (média do dia), não um por sessão
        const timelineEmpty = !daily.some(d => d.accuracy !== null);
        document.getElementById('chart-timeline').parentElement.classList.toggle('hidden', timelineEmpty);
        document.getElementById('timeline-empty').classList.toggle('hidden', !timelineEmpty);
        if (!timelineEmpty) {
            this.charts.timeline = new Chart(document.getElementById('chart-timeline'), {
                type: 'line',
                data: {
                    labels: daily.map(d => dayLabel(d.date)),
                    datasets: [{
                        data: daily.map(d => d.accuracy),
                        borderColor: '#4d74c9', backgroundColor: 'rgba(77,116,201,.12)',
                        fill: true, tension: .3, spanGaps: true,
                        pointRadius: daily.map(d => (d.accuracy === null ? 0 : 5)),
                        pointHoverRadius: daily.map(d => (d.accuracy === null ? 0 : 7)),
                    }],
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { ...pct, x: { grid: { display: false }, ticks: { maxTicksLimit: 8 } } },
                    plugins: { legend: { display: false }, tooltip: { filter: c => c.raw !== null, callbacks: {
                        label: c => `${Math.round(c.raw)}% de acerto · ${daily[c.dataIndex].sessions} ${daily[c.dataIndex].sessions === 1 ? 'atividade' : 'atividades'}` } } }, ...noAnim },
            });
        }

        // Áreas: só as que têm registros; as outras aparecem escritas embaixo
        const all = Object.entries(stats.areas_breakdown);
        const areas = all.filter(([, a]) => a.accuracy !== null && a.accuracy !== undefined);
        const missing = all.filter(([, a]) => a.accuracy === null || a.accuracy === undefined).map(([k]) => UI.AREA_LABELS[k] || k);
        const note = document.getElementById('areas-note');
        note.textContent = !areas.length ? 'Nenhuma atividade no período.' : missing.length ? `Sem dados no período: ${missing.join(', ')}.` : '';
        note.classList.toggle('hidden', !note.textContent);
        document.getElementById('chart-areas').parentElement.classList.toggle('hidden', !areas.length);
        if (areas.length) {
            this.charts.areas = new Chart(document.getElementById('chart-areas'), {
                type: 'bar',
                data: {
                    labels: areas.map(([k]) => UI.AREA_LABELS[k] || k),
                    datasets: [{ data: areas.map(([, a]) => a.accuracy), backgroundColor: areas.map(([k]) => UI.AREA_COLORS[k]), borderRadius: 8 }],
                },
                options: { responsive: true, maintainAspectRatio: false, scales: pct, plugins: { legend: { display: false },
                    tooltip: { callbacks: { label: c => `${c.raw}% · ${areas[c.dataIndex][1].sessions} sessões` } } }, ...noAnim },
            });
        }

        const acts = Object.values(stats.activities_breakdown);
        document.getElementById('chart-activities').closest('.card').classList.toggle('hidden', !acts.length);
        if (acts.length) {
            this.charts.activities = new Chart(document.getElementById('chart-activities'), {
                type: 'bar',
                data: {
                    labels: acts.map(a => a.name),
                    datasets: [{ data: acts.map(a => a.accuracy), backgroundColor: acts.map(a => UI.AREA_COLORS[a.area]), borderRadius: 8 }],
                },
                options: { indexAxis: 'y', responsive: true, maintainAspectRatio: false,
                    scales: { x: pct.y, y: { grid: { display: false } } }, plugins: { legend: { display: false } }, ...noAnim },
            });
        }
    },

    /** Emoções por dia: uma barra por dia, empilhando quantas vezes cada emoção foi escolhida. */
    _moodChart(moods) {
        if (!window.Chart) return;
        // _charts() acabou de destruir os gráficos anteriores, inclusive este
        const canvas = document.getElementById('chart-moods');
        const empty = !moods.total;
        canvas.parentElement.classList.toggle('hidden', empty);
        document.getElementById('moods-empty').classList.toggle('hidden', !empty);
        if (empty) return;
        // Começa no primeiro dia com registro (mantendo pelo menos uma semana visível)
        const first = moods.days.findIndex(d => Object.keys(d.counts).length);
        const days = moods.days.slice(Math.max(0, Math.min(first, moods.days.length - 7)));
        const label = iso => { const [, m, d] = iso.split('-'); return `${d}/${m}`; };
        const grid = getComputedStyle(document.documentElement).getPropertyValue('--border').trim();
        const noAnim = document.body.classList.contains('low-stimulus') ? { animation: false } : {};
        this.charts.moods = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: days.map(d => label(d.date)),
                datasets: App.moodOptions.map(m => ({
                    label: `${m.icon} ${m.label}`,
                    data: days.map(d => d.counts[m.key] || 0),
                    backgroundColor: m.color,
                    borderRadius: 4,
                })),
            },
            options: { responsive: true, maintainAspectRatio: false,
                scales: { x: { stacked: true, grid: { display: false }, ticks: { maxTicksLimit: 10 } },
                    y: { stacked: true, beginAtZero: true, grid: { color: grid }, ticks: { precision: 0 } } },
                plugins: { legend: { position: 'bottom', labels: { boxWidth: 12, filter: item =>
                    days.some(d => d.counts[App.moodOptions[item.datasetIndex].key]) } },
                    tooltip: { filter: c => c.raw > 0 } }, ...noAnim },
        });
    },

    async exportPdf() {
        try {
            UI.toast('Gerando relatório…');
            const q = this.days ? `&days=${this.days}` : '';
            const res = await fetch(`/api/sessions/export/pdf?profile_id=${this.pid}${q}&tz=${new Date().getTimezoneOffset()}`, {
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
            const s = this.summary || await API.get(`/summary/${this.pid}?${this.days ? `days=${this.days}` : 'all_time=true'}&tz=${new Date().getTimezoneOffset()}`);
            const text = `🦊 *Lumina: ${App.profile.name}*\n\n${s.headline}\n\n` +
                `🧩 Atividades: ${s.activities}\n🎯 Acerto de primeira: ${s.accuracy === null ? '–' : Math.round(s.accuracy) + '%'}\n` +
                `⏱️ Tempo de prática: ${UI.formatMinutes(s.minutes * 60000)}\n⭐ Estrelas: ${s.stars}`;
            window.open(`https://api.whatsapp.com/send?text=${encodeURIComponent(text)}`, '_blank', 'noopener');
        } catch (err) { this._fail(err); }
    },

    // ---------- Sessões (nível de ajuda) ----------
    /** Dia local de uma data ISO do servidor (UTC). */
    _day(iso) {
        const d = new Date(iso.endsWith('Z') || iso.includes('+') ? iso : iso + 'Z');
        return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    },

    _dayTitle(key) {
        const today = this._day(new Date().toISOString());
        const yesterday = this._day(new Date(Date.now() - 86400000).toISOString());
        if (key === today) return 'Hoje';
        if (key === yesterday) return 'Ontem';
        const [y, m, d] = key.split('-').map(Number);
        const date = new Date(y, m - 1, d);
        const weekday = date.toLocaleDateString('pt-BR', { weekday: 'long' });
        return `${weekday.charAt(0).toUpperCase()}${weekday.slice(1)}, ${String(d).padStart(2, '0')}/${String(m).padStart(2, '0')}`;
    },

    // ---------- Sessões (agrupadas por dia; detalhes ao tocar) ----------
    async loadSessions() {
        const box = document.getElementById('sessions-list');
        try {
            const sessions = await API.get(`/sessions?profile_id=${this.pid}&limit=60`);
            if (!sessions.length) { box.innerHTML = UI.empty('🕒', 'Nenhuma sessão registrada ainda.'); return; }
            const days = [];
            sessions.forEach(s => {
                const key = this._day(s.created_at);
                if (!days.length || days[days.length - 1].key !== key) days.push({ key, items: [] });
                days[days.length - 1].items.push(s);
            });
            const time = iso => UI.formatDate(iso).split(' ')[1];
            box.innerHTML = days.map(day => {
                const counted = day.items.filter(s => !s.is_practice);
                const avg = counted.length ? Math.round(counted.reduce((t, s) => t + s.accuracy, 0) / counted.length) : null;
                const stars = day.items.reduce((t, s) => t + (s.stars || 0), 0);
                return `<section class="day-group">
                    <h2 class="day-title">${this._dayTitle(day.key)}
                        <span class="day-meta">${day.items.length} ${day.items.length === 1 ? 'atividade' : 'atividades'}${avg === null ? '' : ` · ${avg}% de acerto`} · <span aria-hidden="true">⭐</span> ${stars}</span></h2>
                    ${day.items.map(s => {
                        const a = App.activities[s.activity_type] || {};
                        return `<details class="session-item">
                            <summary>
                                <span class="pic" aria-hidden="true">${UI.pic(a.icon || '⭐')}</span>
                                <span class="grow"><b>${UI.esc(a.name || s.activity_type)}</b>
                                    <span class="meta">${time(s.created_at)} · ${s.accuracy}% · ${s.stars ? `${s.stars} ${s.stars === 1 ? 'estrela' : 'estrelas'}` : 'sem estrelas'}</span>
                                    ${s.is_practice || !s.help_level ? `<span class="session-pills">${s.is_practice ? '<span class="pill info">treino</span>' : ''}${s.help_level ? '' : '<span class="pill warn">ajuda não registrada</span>'}</span>` : ''}</span>
                            </summary>
                            <div class="session-body">
                                <p class="meta">Nível ${s.level} · ${s.correct} de ${s.total_questions} de primeira · ${UI.formatMinutes(s.total_time)}
                                    ${s.reward ? ` · <span class="pill ok">🎁 ${UI.esc(s.reward)}</span>` : ''}
                                    ${s.timed_out ? ' · <span class="pill warn">⏳ tempo acabou</span>' : ''}</p>
                                <div class="session-actions">
                                    <label class="sr-only" for="help-${s.id}">Ajuda dada</label>
                                    <select id="help-${s.id}" data-help="${s.id}">
                                        ${Object.entries(UI.HELP_LEVELS).map(([k, v]) => `<option value="${k}" ${k === (s.help_level || '') ? 'selected' : ''} ${k === '' ? 'disabled' : ''}>${v}</option>`).join('')}
                                    </select>
                                    <button class="btn btn-soft btn-small" data-note="${s.id}"><span aria-hidden="true">📝</span> Observação</button>
                                </div>
                            </div>
                        </details>`;
                    }).join('')}
                </section>`;
            }).join('');
            box.querySelectorAll('[data-help]').forEach(sel => sel.addEventListener('change', async () => {
                try {
                    await API.patch(`/sessions/${sel.dataset.help}`, { help_level: sel.value });
                    sel.closest('details').querySelector('summary .pill.warn')?.remove();
                    UI.toast('Nível de ajuda salvo', 'success');
                } catch (err) { this._fail(err); }
            }));
            box.querySelectorAll('[data-note]').forEach(b => b.addEventListener('click', () => {
                const body = b.closest('.session-body');
                if (body.querySelector('form')) return;
                const form = document.createElement('form');
                form.className = 'session-note';
                form.innerHTML = `<label class="sr-only" for="sn-${b.dataset.note}">Observação</label>
                    <textarea id="sn-${b.dataset.note}" class="input" maxlength="2000" required placeholder="Como foi esta sessão?"></textarea>
                    <button class="btn btn-small" type="submit">Salvar no diário</button>`;
                body.appendChild(form);
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
            const count = this._groupRecs(recs).length;
            document.querySelectorAll('.recs-count').forEach(pill => {
                pill.textContent = count;
                pill.classList.toggle('hidden', !count);
            });
            return recs;
        } catch { return []; }
    },

    /** Padrões iguais em várias atividades viram um cartão só, listando as atividades. */
    _groupRecs(recs) {
        const out = [];
        const byType = {};
        recs.forEach(r => {
            const type = r.kind === 'pattern' ? r.key.split(':')[2] : null;
            if (!type) { out.push({ ...r, keys: [r.key], acts: [r.activity] }); return; }
            if (!byType[type]) {
                byType[type] = { ...r, keys: [], acts: [], reasons: [], title: r.title.split(': ').slice(1).join(': ') || r.title };
                out.push(byType[type]);
            }
            const g = byType[type];
            g.keys.push(r.key);
            g.acts.push(r.activity);
            r.reasons.forEach(x => { if (!g.reasons.includes(x)) g.reasons.push(x); });
        });
        // Um padrão numa atividade só mantém o título original ("Atividade: descrição")
        return out.map(g => (g.kind === 'pattern' && g.keys.length === 1 ? { ...recs.find(r => r.key === g.keys[0]), keys: g.keys, acts: g.acts } : g));
    },

    async loadRecs() {
        const box = document.getElementById('recs-list');
        const recs = this._groupRecs(await this._updateRecsCount());
        if (!recs.length) {
            box.innerHTML = UI.empty('✅', 'Nenhuma recomendação pendente. Novas sugestões aparecem conforme a criança pratica.');
            return;
        }
        const icons = { positive: '📈', attention: '🤝', pattern: '🔎', suggestion: '⭐', general: '💡' };
        box.innerHTML = recs.map((r, i) => {
            const act = App.activities[r.activity];
            const many = r.keys.length > 1;
            const sameLevel = r.kind === 'level' && r.suggested_level === r.current_level;
            const levelSelect = r.kind === 'level' && act && !sameLevel
                ? `<label class="sr-only" for="rec-level-${i}">Nível</label>
                   <select id="rec-level-${i}" class="input" style="width:auto;min-height:44px">
                     ${act.levels.map(l => `<option value="${l}" ${l === (r.suggested_level || 1) ? 'selected' : ''}>Nível ${l}</option>`).join('')}
                   </select>
                   <button class="btn btn-soft btn-small" data-rec="${i}" data-action="adjust">✏️ Usar este nível</button>` : '';
            const acceptLabel = sameLevel ? '👍 Ciente, vou dar mais apoio' : r.kind === 'level' ? `✅ Aceitar nível ${r.suggested_level}` : r.kind === 'activity' ? '⭐ Destacar para a criança' : '👍 Ciente';
            const actChips = many ? `<div class="chip-row" style="margin-bottom:10px">${r.acts.map(a => {
                const info = App.activities[a] || {};
                return `<span class="chip"><span class="pic" aria-hidden="true">${UI.pic(info.icon || '⭐')}</span>${UI.esc(info.name || a)}</span>`;
            }).join('')}</div>` : '';
            return `<div class="card rec-card ${r.type}">
                <h2><span aria-hidden="true">${icons[r.type] || '💡'}</span>${act && !many ? `<span aria-hidden="true">${act.icon}</span>` : ''} ${UI.esc(r.title)}${many ? ` <span class="pill info">${r.keys.length} atividades</span>` : ''}</h2>
                ${actChips}
                <ul>${r.reasons.map(x => `<li>${UI.esc(x)}</li>`).join('')}</ul>
                ${r.kind === 'activity' ? `<p class="shared-note" style="margin-bottom:10px">${UI.esc(r.message)}</p>` : ''}
                <div class="rec-actions">
                    <button class="btn btn-small" data-rec="${i}" data-action="accept">${acceptLabel}</button>
                    ${levelSelect}
                    <button class="btn btn-outline btn-small" data-rec="${i}" data-action="dismiss">✖️ Descartar${many ? ' todas' : ''}</button>
                </div></div>`;
        }).join('');
        box.querySelectorAll('[data-rec]').forEach(b => b.addEventListener('click', async () => {
            const r = recs[Number(b.dataset.rec)];
            const action = b.dataset.action;
            const level = action === 'adjust' ? Number(document.getElementById(`rec-level-${b.dataset.rec}`).value) : undefined;
            try {
                for (let k = 0; k < r.keys.length; k++) {
                    const body = { key: r.keys[k], activity_type: r.acts[k], action };
                    if (level) body.level = level;
                    await API.post(`/ai/recommendations/${this.pid}/decide`, body);
                }
                UI.toast({ accept: 'Recomendação aceita', adjust: 'Nível ajustado', dismiss: 'Recomendação descartada' }[action], 'success');
                this.loadRecs();
            } catch (err) { this._fail(err); }
        }));
    },

    // ---------- Diário ----------
    async loadDiary() {
        const box = document.getElementById('diary-list');
        this.loadRequests();
        this.loadMoods();
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

    async loadRequests() {
        try {
            const data = await API.get(`/requests/${this.pid}?days=7&limit=10`);
            document.getElementById('requests-summary').innerHTML = data.summary.map(r =>
                `<span class="chip"><span class="pic" aria-hidden="true">${UI.pic(r.icon)}</span>${UI.esc(r.label)} <b>× ${r.count}</b></span>`).join('');
            document.getElementById('requests-list').innerHTML = data.items.length ? data.items.map(r => `
                <div class="row">
                    <span class="pic" aria-hidden="true">${UI.pic(r.icon)}</span>
                    <div class="grow"><b>${UI.esc(r.label)}</b>
                        <div class="meta">${UI.formatDate(r.created_at)}${r.context ? ' · durante ' + UI.esc(r.context) : ''}</div></div>
                </div>`).join('') : UI.empty('💬', 'Nenhum pedido nos últimos 7 dias. Os pedidos feitos no botão "Pedir" aparecem aqui.');
        } catch (err) { this._fail(err); }
    },

    async loadMoods() {
        try {
            const data = await API.get(`/moods/${this.pid}?days=7&limit=10&tz=${new Date().getTimezoneOffset()}`);
            document.getElementById('moods-summary').innerHTML = data.summary.map(m =>
                `<span class="chip"><span class="pic" aria-hidden="true">${UI.pic(m.icon)}</span>${UI.esc(m.label)} <b>× ${m.count}</b></span>`).join('');
            document.getElementById('moods-list').innerHTML = data.items.length ? data.items.map(m => `
                <div class="row">
                    <span class="pic" aria-hidden="true">${UI.pic(m.icon)}</span>
                    <div class="grow"><b>${UI.esc(m.label)}</b>
                        <div class="meta">${UI.formatDate(m.created_at)} · ${m.moment === 'livre' ? 'contou pelo botão "Como estou?"' : 'ao entrar na área da criança'}</div></div>
                </div>`).join('') : UI.empty('🙂', 'Nenhuma emoção registrada nos últimos 7 dias. Ela aparece quando a criança responde "Como você está se sentindo?".');
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
                        <div class="progress" role="progressbar" aria-label="Progresso da meta" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><i style="width:${pct}%"></i></div></div>
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
                    <span class="pic" aria-hidden="true">${UI.pic(a.icon)}</span>
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
                    <label class="sr-only" for="tl-${a.activity_type}">Timer visual</label>
                    <select id="tl-${a.activity_type}" data-plan="${a.activity_type}" data-field="time_limit">
                        ${[0, 1, 2, 3, 5, 10, 15].map(n => `<option value="${n}" ${n === (a.time_limit || 0) ? 'selected' : ''}>${n ? `⏳ ${n} min` : 'Sem timer'}</option>`).join('')}
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
                    <span class="pic" aria-hidden="true">${UI.pic(i.icon)}</span>
                    <div class="grow"><b>${UI.esc(i.label)}</b> ${i.done_today ? '<span class="pill ok">feito hoje</span>' : ''}
                        <div class="meta">${i.time ? UI.esc(i.time) : 'sem horário'}</div></div>
                    <label class="sr-only" for="dur-${i.id}">Timer visual de ${UI.esc(i.label)}</label>
                    <select id="dur-${i.id}" data-duration="${i.id}">${this._durationOptions(i.duration)}</select>
                    <button class="btn btn-outline btn-small" data-move="${i.id}" data-pos="${idx - 1}" ${idx === 0 ? 'disabled' : ''} aria-label="Subir">⬆️</button>
                    <button class="btn btn-outline btn-small" data-move="${i.id}" data-pos="${idx + 1}" ${idx === items.length - 1 ? 'disabled' : ''} aria-label="Descer">⬇️</button>
                    <button class="btn btn-outline btn-small" data-del-routine="${i.id}" aria-label="Remover">🗑️</button>
                </div>`).join('') : UI.empty('📅', 'A rotina está vazia. Crie etapas ou use a rotina de exemplo.');
            box.querySelectorAll('[data-move]').forEach(b => b.addEventListener('click', async () => {
                try { await API.put(`/routine/${b.dataset.move}`, { position: Number(b.dataset.pos) }); this.loadRoutine(); } catch (err) { this._fail(err); }
            }));
            box.querySelectorAll('[data-duration]').forEach(sel => sel.addEventListener('change', async () => {
                try {
                    await API.put(`/routine/${sel.dataset.duration}`, { duration: Number(sel.value) });
                    UI.toast('Timer da etapa salvo', 'success');
                } catch (err) { this._fail(err); }
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
        const duration = document.getElementById('routine-duration');
        try {
            await API.post('/routine', {
                profile_id: this.pid, icon: this.routineEmoji, label: label.value.trim(),
                time: time.value || null, duration: Number(duration.value) || null,
            });
            label.value = '';
            time.value = '';
            duration.value = '0';
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
            let updated = await API.put(`/profiles/${this.pid}`, UI.readProfileForm(e.target));
            updated = await UI.saveProfilePhoto(e.target, updated);
            Object.assign(App.profile, updated);
            this.loadProfile();
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
        document.getElementById('set-tokens').checked = s.token_board !== false;
        document.getElementById('set-requests').checked = s.request_board !== false;
        document.getElementById('set-mood').checked = s.mood_checkin !== false;
        ['set-sound', 'set-voice', 'set-low', 'set-tokens', 'set-requests', 'set-mood'].forEach(id => { document.getElementById(id).disabled = !this.pid; });
        document.getElementById('reward-form').classList.toggle('hidden', !this.pid);
        if (this.pid) {
            this._renderRewardOptions();
            this._renderRequestOptions();
        }
        document.getElementById('picto-credit').textContent = Pictos.count ? Pictos.attribution : '';
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

    // ---------- Quadro de fichas ----------
    _renderRewardOptions() {
        const current = App.settings.rewards || [];
        const isOn = r => current.some(c => c.icon === r.icon && c.label === r.label);
        const custom = current.filter(c => !App.rewardOptions.some(o => o.icon === c.icon && o.label === c.label));
        const all = [...App.rewardOptions, ...custom];
        const box = document.getElementById('reward-options');
        box.innerHTML = all.map((r, i) => `
            <button type="button" class="chip toggle" data-reward-opt="${i}" aria-pressed="${isOn(r)}">
                <span class="pic" aria-hidden="true">${UI.pic(r.icon)}</span>${UI.esc(r.label)}
            </button>`).join('');
        box.querySelectorAll('[data-reward-opt]').forEach(b => b.addEventListener('click', () => {
            const r = all[Number(b.dataset.rewardOpt)];
            const next = isOn(r)
                ? current.filter(c => !(c.icon === r.icon && c.label === r.label))
                : [...current, r];
            if (!next.length) { UI.toast('Deixe pelo menos um prêmio ligado', 'error'); return; }
            this._saveRewards(next);
        }));
    },

    async _saveRewards(rewards) {
        try {
            App.settings = await API.put(`/settings/${this.pid}`, { rewards });
            this._renderRewardOptions();
        } catch (err) { this._fail(err); }
    },

    async addReward(e) {
        e.preventDefault();
        const input = document.getElementById('reward-label');
        const label = input.value.trim();
        if (!label) return;
        const current = App.settings.rewards || [];
        if (current.length >= 12) { UI.toast('Use no máximo 12 prêmios; desligue algum antes.', 'error'); return; }
        if (current.some(r => r.icon === this.rewardEmoji && r.label.toLowerCase() === label.toLowerCase())) {
            UI.toast('Esse prêmio já existe', 'error');
            return;
        }
        await this._saveRewards([...current, { icon: this.rewardEmoji, label }]);
        input.value = '';
        UI.toast('Prêmio adicionado', 'success');
    },

    // ---------- Prancha de pedidos ----------
    _renderRequestOptions() {
        const current = App.settings.requests || [];
        const box = document.getElementById('request-options');
        box.innerHTML = App.requestOptions.map(o => `
            <button type="button" class="chip toggle" data-request-opt="${o.key}" aria-pressed="${current.includes(o.key)}">
                <span class="pic" aria-hidden="true">${UI.pic(o.icon)}</span>${UI.esc(o.label)}
            </button>`).join('');
        box.querySelectorAll('[data-request-opt]').forEach(b => b.addEventListener('click', async () => {
            const key = b.dataset.requestOpt;
            const next = current.includes(key) ? current.filter(k => k !== key) : [...current, key];
            if (!next.length) { UI.toast('Deixe pelo menos um pedido ligado', 'error'); return; }
            try {
                App.settings = await API.put(`/settings/${this.pid}`, { requests: next });
                this._renderRequestOptions();
            } catch (err) { this._fail(err); }
        }));
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
