// ==========================================
// ACTIVITIES CONTROLLER - Atividades Educacionais
// ==========================================

const ActivityController = {
    currentActivity: null,
    currentLevel: 1,
    currentIndex: 0,
    correctAnswers: 0,
    incorrectAnswers: 0,
    startTime: null,
    responses: [],
    questions: [],
    isPractice: false,
    attemptsForCurrentQuestion: 1,

    async startActivity(activityType, isPractice = false) {
        this.isPractice = isPractice;
        this.currentActivity = activityType;
        this.currentIndex = 0;
        this.correctAnswers = 0;
        this.incorrectAnswers = 0;
        this.responses = [];
        this.startTime = Date.now();

        // Obter nível sugerido pela IA
        if (!isPractice && AppController.currentProfile) {
            try {
                const analysis = await API.get(
                    `/ai/analyze/${AppController.currentProfile.id}/${activityType}`
                );
                this.currentLevel = analysis.suggested_level || 1;
            } catch {
                this.currentLevel = 1;
            }
        } else {
            this.currentLevel = 1;
        }

        // Buscar questões do servidor
        try {
            const data = await API.get(
                `/activities/${activityType}/questions?level=${this.currentLevel}`
            );
            this.questions = this._shuffle([...data.questions]);
        } catch {
            AppController.showToast('Erro ao carregar questões', 'error');
            return;
        }

        AppController.showScreen('activity-screen');
        const title = isPractice ? `🎮 Treino` : (this.questions.length > 0 ? '' : '');
        document.getElementById('activity-title').textContent = title || activityType;
        document.getElementById('activity-level').textContent = `Nível ${this.currentLevel}`;
        this._renderQuestion();
    },

    _renderQuestion() {
        if (this.currentIndex >= this.questions.length) {
            this._finishActivity();
            return;
        }
        
        this.attemptsForCurrentQuestion = 1;

        const q = this.questions[this.currentIndex];
        const questionEl = document.getElementById('activity-question');
        const optionsEl = document.getElementById('activity-options');

        // Render question
        let html = `<span style="display:flex; align-items:center; gap:10px; justify-content:center;">
                        ${q.question} 
                        <button class="btn-text" onclick="ActivityController.speakQuestion('${q.question.replace(/'/g, "\\'")}')" style="font-size:2rem; cursor:pointer;" title="Ouvir instrução">🔊</button>
                    </span>`;
        if (q.visual) html += `<div class="question-visual">${q.visual}</div>`;
        if (q.sequence) html += `<div class="question-visual">${q.sequence}</div>`;
        if (q.reference && q.type === 'shape') {
            html += `<div class="question-reference">${q.reference}</div>`;
        }
        questionEl.innerHTML = html;

        // Render options
        optionsEl.innerHTML = '';
        const opts = this._shuffle([...q.options]);
        opts.forEach(opt => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            if (q.type === 'color') {
                btn.classList.add('color-option');
                btn.style.background = opt;
            } else {
                btn.textContent = opt;
            }
            btn.onclick = () => this._checkAnswer(opt, q.correct);
            optionsEl.appendChild(btn);
        });

        // Progress bar
        const pct = ((this.currentIndex + 1) / this.questions.length) * 100;
        document.getElementById('activity-progress-bar').style.width = `${pct}%`;
        document.getElementById('activity-progress-text').textContent =
            `${this.currentIndex + 1}/${this.questions.length}`;
    },

    _checkAnswer(selected, correct) {
        const isCorrect = selected === correct;
        const responseTime = Date.now() - this.startTime;

        if (isCorrect) {
            this.responses.push({
                question_index: this.currentIndex,
                is_correct: isCorrect,
                response_time: responseTime,
                attempts: this.attemptsForCurrentQuestion,
            });
            this.correctAnswers++;
            this._showFeedback(true);
            SoundController.playCorrect();
            
            // Disable all buttons to prevent double clicks
            document.querySelectorAll('.option-btn').forEach(b => (b.disabled = true));

            setTimeout(() => {
                this.currentIndex++;
                this.startTime = Date.now();
                this._renderQuestion();
            }, 1500);
        } else {
            this.incorrectAnswers++;
            this.attemptsForCurrentQuestion++;
            this._showFeedback(false);
            SoundController.playIncorrect();
        }
    },

    _showFeedback(isCorrect) {
        const modal = document.getElementById('feedback-modal');
        const content = document.getElementById('feedback-content');
        const mascot = document.getElementById('mascot-container');
        const bubble = document.getElementById('mascot-speech-bubble');

        if (isCorrect) {
            const msgs = ['Muito bem!', 'Parabéns!', 'Arrasou!', 'Incrível!', 'Perfeito!'];
            const msg = msgs[Math.floor(Math.random() * msgs.length)];
            content.textContent = '⭐ ' + msg;
            if (mascot) { mascot.textContent = '🦊✨'; mascot.style.transform = 'scale(1.2) translateY(-15px)'; }
            if (bubble) {
                bubble.textContent = msg;
                bubble.className = 'mascot-bubble show';
                bubble.style.background = '#10b981';
                bubble.style.color = 'white';
                bubble.style.borderColor = '#10b981';
            }
            this._speakFeedback(msg);
        } else {
            const msgs = ['Tente de novo!', 'Quase lá!', 'Você consegue!'];
            const msg = msgs[Math.floor(Math.random() * msgs.length)];
            content.textContent = '💪 ' + msg;
            if (mascot) { mascot.textContent = '🦊💭'; mascot.style.transform = 'scale(0.9) rotate(-5deg)'; }
            if (bubble) {
                bubble.textContent = msg;
                bubble.className = 'mascot-bubble show';
                bubble.style.background = '#f59e0b';
                bubble.style.color = 'white';
                bubble.style.borderColor = '#f59e0b';
            }
            this._speakFeedback(msg);
        }

        content.className = `feedback-bubble ${isCorrect ? 'correct' : 'incorrect'}`;
        modal.classList.add('show');

        setTimeout(() => {
            modal.classList.remove('show');
            if (mascot) { mascot.textContent = '🦊'; mascot.style.transform = 'scale(1)'; }
            if (bubble) bubble.className = 'mascot-bubble';
        }, 1800);
    },

    _speakFeedback(text) {
        if (!('speechSynthesis' in window)) return;
        window.speechSynthesis.cancel();
        const msg = new SpeechSynthesisUtterance(text);
        msg.lang = 'pt-BR';
        msg.rate = 0.95;
        msg.pitch = 1.15;
        msg.volume = 0.85;
        const voices = window.speechSynthesis.getVoices();
        const ptVoice = voices.find(v => v.lang.startsWith('pt') && v.name.toLowerCase().includes('female'))
                     || voices.find(v => v.lang.startsWith('pt') && !v.name.toLowerCase().includes('google'))
                     || voices.find(v => v.lang.startsWith('pt'));
        if (ptVoice) msg.voice = ptVoice;
        window.speechSynthesis.speak(msg);
    },

    speakQuestion(text) {
        if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
            const msg = new SpeechSynthesisUtterance(text);
            msg.lang = 'pt-BR';
            msg.rate = 0.85;
            msg.pitch = 1.1;
            msg.volume = 0.9;
            
            // Selecionar voz mais humanizada
            const voices = window.speechSynthesis.getVoices();
            const ptVoice = voices.find(v => v.lang.startsWith('pt') && v.name.toLowerCase().includes('female'))
                         || voices.find(v => v.lang.startsWith('pt') && !v.name.toLowerCase().includes('google'))
                         || voices.find(v => v.lang.startsWith('pt'));
            if (ptVoice) msg.voice = ptVoice;
            
            window.speechSynthesis.speak(msg);
            
            const bubble = document.getElementById('mascot-speech-bubble');
            if (bubble) {
                bubble.textContent = '🔊 Ouvindo...';
                bubble.className = 'mascot-bubble show';
                bubble.style.background = '#3b82f6';
                bubble.style.color = 'white';
                bubble.style.borderColor = '#3b82f6';
            }
            msg.onend = () => {
                if (bubble) bubble.className = 'mascot-bubble';
            };
        } else {
            AppController.showToast('Navegador não suporta leitura de voz.', 'error');
        }
    },

    async _finishActivity() {
        const totalTime = Date.now() - this.startTime;
        const total = this.questions.length;
        const accuracy = total > 0 ? (this.correctAnswers / total) * 100 : 0;

        let stars = 0;
        if (accuracy >= 90) stars = 3;
        else if (accuracy >= 70) stars = 2;
        else if (accuracy >= 50) stars = 1;

        // Save session to server
        if (AppController.currentProfile) {
            try {
                await API.post('/sessions', {
                    profile_id: AppController.currentProfile.id,
                    activity_type: this.currentActivity,
                    level: this.currentLevel,
                    total_questions: total,
                    correct: this.correctAnswers,
                    incorrect: this.incorrectAnswers,
                    total_time: totalTime,
                    is_practice: this.isPractice,
                    responses: this.responses,
                });

                // Check for new achievements
                await API.post(`/achievements/check/${AppController.currentProfile.id}`);
            } catch (err) {
                console.warn('[Activity] Error saving session:', err);
            }
        }

        // Show reward screen
        document.getElementById('reward-message').textContent =
            `Você acertou ${this.correctAnswers} de ${total} perguntas!`;
        document.getElementById('stars-earned').innerHTML = '⭐'.repeat(stars);
        SoundController.playReward();
        AppController.showScreen('reward-screen');
    },

    continueFromReward() {
        AppController.showScreen('child-menu-screen');
    },

    exitActivity() {
        AppController.showScreen('child-menu-screen');
    },

    _shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    },
};

// Profile Controller (simple)
const ProfileController = {
    async loadProfiles() {
        try {
            const profiles = await API.get('/profiles');
            if (profiles.length > 0 && !AppController.currentProfile) {
                AppController.currentProfile = profiles[0];
                localStorage.setItem('tea_profile', JSON.stringify(profiles[0]));
            }
            return profiles;
        } catch { return []; }
    },

    async createProfile(name, avatar, diagnosis) {
        try {
            const profile = await API.post('/profiles', { name, avatar, diagnosis });
            AppController.currentProfile = profile;
            localStorage.setItem('tea_profile', JSON.stringify(profile));
            return profile;
        } catch { return null; }
    },

    async renderAdminProfiles() {
        const list = document.getElementById('profiles-list');
        if (!list) return;
        const profiles = await this.loadProfiles();
        list.innerHTML = '';
        if (profiles.length === 0) {
            list.innerHTML = '<p style="text-align:center;width:100%;">Nenhum perfil encontrado.</p>';
            return;
        }
        profiles.forEach(p => {
            const isActive = AppController.currentProfile && AppController.currentProfile.id === p.id;
            const btn = document.createElement('button');
            btn.className = `activity-card ${isActive ? 'color-activity' : ''}`;
            btn.innerHTML = `<span class="activity-icon">${p.avatar || '😊'}</span>
                             <span class="activity-name">${p.name}</span>
                             ${isActive ? '<small style="color:var(--success)">(Ativo)</small>' : ''}`;
            btn.onclick = () => this.selectProfile(p);
            list.appendChild(btn);
        });
    },

    async createNewProfile() {
        // Agora invoca o modal estético
        AppController.openModal('create-profile-modal');
    },
    
    async saveProfileFromModal(event) {
        event.preventDefault();
        const nome = document.getElementById('profile-name-input').value;
        const diag = document.getElementById('profile-diagnosis-input').value;
        const avatar = document.getElementById('profile-avatar-input').value || '😊';
        
        if (!nome) {
            AppController.showToast('Nome é obrigatório!', 'error');
            return;
        }
        
        const profile = await this.createProfile(nome, avatar, diag);
        if (profile) {
            AppController.showToast('Perfil criado com sucesso!', 'success');
            AppController.closeModal('create-profile-modal');
            this.renderAdminProfiles();
        }
    },

    selectProfile(profile) {
        AppController.currentProfile = profile;
        localStorage.setItem('tea_profile', JSON.stringify(profile));
        this.renderAdminProfiles();
        AppController.showToast(`Perfil alterado para ${profile.name}`, 'success');
        if(AppController._updateChildHeader) AppController._updateChildHeader();
        
        // Auto-reload na tela Admin
        if (AppController.currentScreen === 'admin-panel-screen') {
             // Atualiza os dados de onde estiver (Dashboard Principal ou Detalhado)
             const activeTab = document.querySelector('.tab-content.active');
             if (activeTab) {
                 const tId = activeTab.id;
                 if (tId === 'tab-dashboard') AdminController.loadDashboard();
                 if (tId === 'tab-detailed') AdminController.loadDetailed();
                 if (tId === 'tab-recommendations') AdminController.loadRecommendations();
             }
        }
    }
};
