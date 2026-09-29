// ==========================================
// CHILD - Área da criança (início, rotina, conquistas)
// ==========================================
// Uma tela por vez, pictogramas grandes e nada de funções de adulto
// (sair daqui pede a senha da conta).

const Child = {
    plan: [],
    routine: [],

    async home() {
        const p = App.profile;
        document.getElementById('child-avatar').textContent = p.avatar || '😊';
        document.getElementById('child-hello').textContent = `Olá, ${p.name}!`;
        UI.showScreen('child-home');

        const tiles = document.getElementById('child-tiles');
        tiles.innerHTML = '';
        try {
            [this.plan, this.routine] = await Promise.all([
                API.get(`/plans/${p.id}`),
                API.get(`/routine/${p.id}`),
            ]);
        } catch (err) {
            UI.toast(err.message, 'error');
            return;
        }
        this.renderNowNext();
        this.renderTiles();
    },

    /** "Agora / Depois": a próxima etapa da rotina, como no quadro visual do TEACCH. */
    renderNowNext() {
        const box = document.getElementById('now-next');
        const pending = this.routine.filter(i => !i.done_today);
        if (!pending.length) {
            box.classList.add('hidden');
            return;
        }
        const [now, next] = pending;
        const step = (item, tag, cls) => `
            <div class="step ${cls}">
                <span class="pic" aria-hidden="true">${UI.esc(item.icon)}</span>
                <span><span class="tag">${tag}</span><span class="what">${UI.esc(item.label)}</span></span>
            </div>`;
        box.innerHTML = step(now, 'Agora', 'now') +
            (next ? `<span class="arrow" aria-hidden="true">➜</span>${step(next, 'Depois', '')}` : '');
        box.classList.remove('hidden');
    },

    renderTiles() {
        const tiles = document.getElementById('child-tiles');
        const enabled = this.plan.filter(a => a.enabled)
            .sort((a, b) => Number(b.recommended) - Number(a.recommended));

        const activityTile = a => `
            <button class="tile area-${a.area} ${a.recommended ? 'recommended' : ''}" data-activity="${a.activity_type}"
                aria-label="${UI.esc(a.name)}${a.recommended ? ', recomendada' : ''}, nível ${a.level}">
                ${a.recommended ? '<span class="badge-star" aria-hidden="true">⭐ Hoje</span>' : ''}
                <span class="pic" aria-hidden="true">${a.icon}</span>
                ${UI.esc(a.name)}
                <span class="level-dots" aria-hidden="true">${Array.from({ length: a.max_level }, (_, i) => `<i class="${i < a.level ? 'on' : ''}"></i>`).join('')}</span>
            </button>`;

        let html = '';
        if (this.routine.length) {
            html += `<button class="tile special" data-open="routine"><span class="pic" aria-hidden="true">📅</span>Minha rotina</button>`;
        }
        html += enabled.map(activityTile).join('');
        if (enabled.length) {
            html += `<button class="tile special" data-free="1"><span class="pic" aria-hidden="true">🎮</span>Brincar livre</button>`;
        }
        html += `<button class="tile special" data-open="progress"><span class="pic" aria-hidden="true">🌟</span>Conquistas</button>`;
        tiles.innerHTML = html || UI.empty('🧩', 'Nenhuma atividade liberada. Peça a um adulto.');

        tiles.querySelectorAll('[data-activity]').forEach(b => b.addEventListener('click', () => {
            const plan = this.plan.find(a => a.activity_type === b.dataset.activity);
            Activity.start(plan, false);
        }));
        tiles.querySelector('[data-free]')?.addEventListener('click', () => {
            const pick = enabled[Math.floor(Math.random() * enabled.length)];
            Activity.start({ ...pick, level: 1 }, true);
        });
        tiles.querySelector('[data-open="routine"]')?.addEventListener('click', () => this.showRoutine());
        tiles.querySelector('[data-open="progress"]')?.addEventListener('click', () => this.showProgress());
    },

    async showRoutine() {
        UI.showScreen('routine-screen');
        const box = document.getElementById('routine-cards');
        try {
            this.routine = await API.get(`/routine/${App.profile.id}`);
        } catch (err) {
            UI.toast(err.message, 'error');
            return;
        }
        const firstPending = this.routine.find(i => !i.done_today);
        box.innerHTML = this.routine.map(i => `
            <button class="routine-card ${i.done_today ? 'done' : ''} ${firstPending && i.id === firstPending.id ? 'now' : ''}"
                data-item="${i.id}" aria-pressed="${i.done_today}"
                aria-label="${UI.esc(i.label)}${i.time ? ' às ' + i.time : ''}${i.done_today ? ', feito' : ''}">
                <span class="pic" aria-hidden="true">${UI.esc(i.icon)}</span>
                ${UI.esc(i.label)}
                ${i.time ? `<span class="time">${UI.esc(i.time)}</span>` : ''}
            </button>`).join('') || UI.empty('📅', 'A rotina ainda está vazia.');
        box.querySelectorAll('[data-item]').forEach(b => b.addEventListener('click', async () => {
            await API.post(`/routine/${b.dataset.item}/toggle`);
            if (b.getAttribute('aria-pressed') === 'false') SoundController.playCorrect();
            this.showRoutine();
        }));
    },

    async showProgress() {
        UI.showScreen('progress-screen');
        const pid = App.profile.id;
        try {
            const [stats, medals] = await Promise.all([
                API.get(`/sessions/stats?profile_id=${pid}`),
                API.get(`/achievements/${pid}`),
            ]);
            document.getElementById('star-total').textContent = stats.total_stars;
            document.getElementById('medals').innerHTML = medals.map(m => `
                <div class="medal ${m.unlocked ? '' : 'locked'}">
                    <div class="pic" aria-hidden="true">${m.icon}</div>
                    <b>${UI.esc(m.name)}</b>
                    <small>${m.unlocked ? 'Conquistada!' : UI.esc(m.description)}</small>
                </div>`).join('');
            const skills = Object.entries(stats.activities_breakdown);
            document.getElementById('skill-cards').innerHTML = skills.length ? skills.map(([type, d]) => `
                <div class="skill-card">
                    <span class="pic" aria-hidden="true">${App.activities[type]?.icon || '⭐'}</span>
                    <div style="flex:1">
                        <b>${UI.esc(d.name)}</b> <span aria-label="${d.stars} estrelas">· ${d.stars} ⭐</span>
                        <div class="bar" aria-hidden="true"><i style="width:${d.accuracy}%"></i></div>
                    </div>
                </div>`).join('') : UI.empty('🌱', 'Faça uma atividade para ver seu progresso aqui!');
        } catch (err) {
            UI.toast(err.message, 'error');
        }
    },
};
