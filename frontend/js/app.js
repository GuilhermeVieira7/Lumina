// ==========================================
// APP CONTROLLER - Controller Principal
// ==========================================

const AppController = {
    currentUser: null,
    currentProfile: null,
    currentScreen: 'login-screen',

    init() {
        this.lowStimulus = localStorage.getItem('tea_low_stimulus') === 'true';
        if (this.lowStimulus) {
            document.body.classList.add('low-stimulus');
            const checkbox = document.getElementById('low-stimulus-checkbox');
            if (checkbox) checkbox.checked = true;
        }

        SoundController.init(this.lowStimulus);
        ThemeController.init();
        I18n.init();
        I18n.updateUI();

        // Check if already logged in
        if (AuthController.checkAuth()) {
            const savedProfile = localStorage.getItem('tea_profile');
            if (savedProfile) this.currentProfile = JSON.parse(savedProfile);
            this.showScreen('select-screen');
            ProfileController.loadProfiles();
        } else {
            this.showScreen('login-screen');
        }
    },

    showScreen(screenId) {
        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const screen = document.getElementById(screenId);
        if (screen) {
            screen.classList.add('active');
            this.currentScreen = screenId;
        }
    },

    enterChildArea() {
        if (!this.currentProfile) {
            this.showToast('Selecione um perfil primeiro', 'error');
            return;
        }
        this.showScreen('child-menu-screen');
        this._updateChildHeader();
    },

    enterAdminArea() {
        this.showScreen('admin-panel-screen');
        AdminController.showTab('dashboard');
    },

    async showChildProgress() {
        if (!this.currentProfile) return;
        this.showScreen('child-progress-screen');

        try {
            const stats = await API.get(`/sessions/stats?profile_id=${this.currentProfile.id}`);
            document.getElementById('total-stars-count').textContent = stats.total_stars;

            const grid = document.getElementById('skills-progress');
            grid.innerHTML = '';

            Object.entries(stats.activities_breakdown).forEach(([type, data]) => {
                const card = document.createElement('div');
                card.className = 'skill-card';
                card.innerHTML = `
                    <div class="skill-name">${type}</div>
                    <div class="skill-stats">
                        <span>${data.stars} ⭐</span>
                        <span>${data.accuracy}%</span>
                    </div>
                    <div class="skill-progress-bar">
                        <div class="skill-progress-fill" style="width:${data.accuracy}%"></div>
                    </div>
                `;
                grid.appendChild(card);
            });

            if (Object.keys(stats.activities_breakdown).length === 0) {
                grid.innerHTML = '<p style="text-align:center;color:white;padding:20px;">Comece a praticar para ver seu progresso! 🌟</p>';
            }
        } catch {}
    },

    _updateChildHeader() {
        const avatar = document.getElementById('user-avatar');
        if (avatar && this.currentProfile) {
            avatar.textContent = this.currentProfile.avatar || '😊';
        }
    },

    showToast(message, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = `toast ${type}`;
        toast.classList.remove('hidden');
        setTimeout(() => toast.classList.add('hidden'), 3500);
    },

    // Modal helpers
    openModal(id) {
        document.getElementById(id)?.classList.remove('hidden');
    },
    closeModal(id) {
        document.getElementById(id)?.classList.add('hidden');
    },
    
    toggleLowStimulus(isActive) {
        this.lowStimulus = isActive;
        localStorage.setItem('tea_low_stimulus', isActive ? 'true' : 'false');
        if(isActive) {
            document.body.classList.add('low-stimulus');
        } else {
            document.body.classList.remove('low-stimulus');
        }
        SoundController.setLowStimulus(isActive);
        this.showToast(isActive ? 'Modo Baixo Estímulo ativado.' : 'Modo Baixo Estímulo desativado.', 'success');
    }
};

// ---- DOM Ready ----
document.addEventListener('DOMContentLoaded', () => {
    AppController.init();

    // Register service worker
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/service-worker.js')
            .then(r => console.log('[PWA] SW registered'))
            .catch(e => console.log('[PWA] SW error:', e));
    }

    console.log('🌟 Sistema TEA v2.0 — Fundamentado em ABA, TEACCH e Educação Inclusiva');
});
