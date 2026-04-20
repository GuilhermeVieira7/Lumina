// ==========================================
// ADMIN CONTROLLER - Painel Administrativo
// ==========================================

const AdminController = {
    charts: {},

    async showTab(tabName) {
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        const tabEl = document.getElementById(`tab-${tabName}`);
        if (tabEl) tabEl.classList.add('active');
        // Highlight clicked button
        event?.target?.classList?.add('active');

        if (tabName === 'dashboard') await this.loadDashboard();
        else if (tabName === 'detailed') await this.loadDetailed();
        else if (tabName === 'recommendations') await this.loadRecommendations();
    },

    async loadDashboard() {
        if (!AppController.currentProfile) return;
        const pid = AppController.currentProfile.id;

        try {
            const stats = await API.get(`/sessions/stats?profile_id=${pid}`);
            document.getElementById('stat-total-activities').textContent = stats.total_activities;
            document.getElementById('stat-accuracy').textContent = stats.accuracy + '%';
            
            // Corrige o bug de só exibir 0.0h
            const totalMinutes = Math.floor(stats.total_time / 60000);
            if (totalMinutes < 60) {
                document.getElementById('stat-total-time').textContent = totalMinutes + ' min';
            } else {
                const hours = Math.floor(totalMinutes / 60);
                const mins = totalMinutes % 60;
                document.getElementById('stat-total-time').textContent = `${hours}h ${mins}m`;
            }
            
            document.getElementById('stat-stars').textContent = stats.total_stars;

            this._renderSkillsChart(stats.activities_breakdown);
            await this._renderTimelineChart(pid);
        } catch (err) {
            console.warn('[Admin] Dashboard error:', err);
        }
    },

    _renderSkillsChart(breakdown) {
        const ctx = document.getElementById('skills-chart');
        if (!ctx) return;

        if (this.charts.skills) this.charts.skills.destroy();

        const labels = Object.keys(breakdown);
        const accuracies = labels.map(k => breakdown[k].accuracy);

        this.charts.skills = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Taxa de Acerto (%)',
                    data: accuracies,
                    backgroundColor: 'rgba(102, 126, 234, 0.7)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    borderRadius: 8,
                }],
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                scales: { y: { beginAtZero: true, max: 100 } },
                plugins: { legend: { display: false } },
            },
        });
    },

    async _renderTimelineChart(profileId) {
        const ctx = document.getElementById('timeline-chart');
        if (!ctx) return;

        if (this.charts.timeline) this.charts.timeline.destroy();

        try {
            const sessions = await API.get(`/sessions?profile_id=${profileId}&limit=10`);
            const labels = sessions.map((_, i) => `Sessão ${i + 1}`);
            const data = sessions.map(s => s.accuracy);

            this.charts.timeline = new Chart(ctx, {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Taxa de Acerto (%)',
                        data,
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 3, fill: true, tension: 0.4,
                    }],
                },
                options: {
                    responsive: true, maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true, max: 100 } },
                    plugins: { legend: { display: false } },
                },
            });
        } catch {}
    },

    async loadDetailed() {
        if (!AppController.currentProfile) return;
        const pid = AppController.currentProfile.id;
        const container = document.getElementById('detailed-metrics');
        container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:20px;">Carregando...</p>';

        try {
            const stats = await API.get(`/sessions/stats?profile_id=${pid}`);
            
            const avgTimeSecs = (stats.avg_response_time / 1000).toFixed(1);
            const impulsivityTag = stats.avg_response_time < 3000 ? '⚡ Impulsivo (Responde Rápido)' : '🤔 Reflexivo (Pensa antes de agir)';
            
            container.innerHTML = `
                <div class="metric-item" style="border-left: 4px solid var(--accent); background: var(--bg-card); display: flex; gap: 20px; justify-content: space-around; padding: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">Tempo Típico</div>
                        <div style="font-size: 1.5rem; color: var(--text-primary); font-weight: bold;">${avgTimeSecs}s</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">Tentativas Médias</div>
                        <div style="font-size: 1.5rem; color: var(--text-primary); font-weight: bold;">${stats.avg_attempts.toFixed(1)}</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">Perfil Cognitivo</div>
                        <div style="font-size: 1.1rem; color: var(--text-primary); font-weight: bold; margin-top: 5px;">${impulsivityTag}</div>
                    </div>
                </div>
            `;

            Object.entries(stats.activities_breakdown).forEach(([type, data]) => {
                const card = document.createElement('div');
                card.className = 'metric-item';
                card.innerHTML = `
                    <div class="metric-title">${type}</div>
                    <div class="metric-details" style="display:block;">
                        <p style="margin-bottom: 8px; color: var(--text-primary); line-height: 1.6;">
                            Nesta atividade, a criança participou de <strong>${data.sessions} sessões</strong>. 
                            Ela <strong>acertou ${data.correct}</strong> questões e <strong>errou ${data.incorrect}</strong> questões, 
                            resultando em uma taxa de precisão de <strong>${data.accuracy}%</strong>.
                        </p>
                        <p style="color: var(--text-secondary); font-size: 0.95rem;">
                            Atualmente, a criança alcançou o <strong>nível ${data.current_level}</strong> e já conquistou <strong>${data.stars} estrelas</strong> ⭐ pela sua dedicação.
                        </p>
                    </div>
                `;
                container.appendChild(card);
            });

            if (Object.keys(stats.activities_breakdown).length === 0) {
                container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:40px;">Nenhuma atividade registrada ainda.</p>';
            }
        } catch {}
    },

    async loadRecommendations() {
        if (!AppController.currentProfile) return;
        const pid = AppController.currentProfile.id;
        const container = document.getElementById('recommendations-container');
        container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:20px;">Carregando...</p>';

        try {
            const recs = await API.get(`/ai/recommendations/${pid}`);
            container.innerHTML = '';

            if (recs.length === 0) {
                container.innerHTML = '<p style="text-align:center;color:var(--text-secondary);padding:40px;">Continue praticando para receber recomendações personalizadas!</p>';
                return;
            }

            recs.forEach(rec => {
                const colors = { attention: '#f59e0b', positive: '#10b981', pattern: '#3b82f6', general: '#8b5cf6' };
                const labels = { attention: 'Atenção', positive: 'Progresso', pattern: 'Padrão', general: 'Geral' };
                const color = colors[rec.type] || '#8b5cf6';

                const card = document.createElement('div');
                card.className = 'recommendation-card';
                card.style.borderLeftColor = color;
                card.innerHTML = `
                    <span class="recommendation-type" style="background:${color}">${labels[rec.type] || rec.type}</span>
                    <div class="recommendation-text">${rec.title}</div>
                    <div class="recommendation-reason">${rec.message}</div>
                `;
                container.appendChild(card);
            });
        } catch {}
    },

    async exportData() {
        if (!AppController.currentProfile) return;
        const pid = AppController.currentProfile.id;
        try {
            AppController.showToast('Gerando Relatório PDF... ⏳', 'success');
            const token = localStorage.getItem('tea_token');
            const baseUrl = window.location.protocol + '//' + window.location.host;
            const response = await fetch(`${baseUrl}/api/sessions/export/pdf?profile_id=${pid}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (!response.ok) throw new Error('Não foi possível gerar PDF');
            
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `tea_relatorio_${AppController.currentProfile.name.replace(' ','_')}.pdf`;
            a.click();
            URL.revokeObjectURL(url);
            AppController.showToast('Relatório PDF Baixado! 📥', 'success');
        } catch(err) {
            AppController.showToast('Erro ao exportar PDF', 'error');
        }
    },
    async shareWhatsApp() {
        if (!AppController.currentProfile) {
            AppController.showToast('Nenhum perfil selecionado!', 'error');
            return;
        }
        
        try {
            const pid = AppController.currentProfile.id;
            const stats = await API.get(`/sessions/stats?profile_id=${pid}`);
            
            const totalMinutes = Math.floor(stats.total_time / 60000);
            let timeStr = totalMinutes + ' minutos';
            if (totalMinutes >= 60) {
                timeStr = `${Math.floor(totalMinutes / 60)}h ${totalMinutes % 60}m`;
            }
            
            const text = `🧠 *Relatório de Prática: ${AppController.currentProfile.name}*\n\n` +
                         `✅ Acerto Geral: ${stats.accuracy}%\n` +
                         `🎯 Atividades Feitas: ${stats.total_activities}\n` +
                         `⭐ Estrelas ganhas: ${stats.total_stars}\n` +
                         `⏱️ Tempo de prática: ${timeStr}\n\n` +
                         `_Enviado através do Sistema TEA_`;
                         
            const encodedText = encodeURIComponent(text);
            const url = `https://api.whatsapp.com/send?text=${encodedText}`;
            window.open(url, '_blank');
        } catch(err) {
            AppController.showToast('Erro ao preparar mensagem de WhatsApp', 'error');
        }
    },
};
