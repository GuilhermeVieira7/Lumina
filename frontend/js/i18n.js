// ==========================================
// I18N - Internacionalização
// ==========================================

const I18n = {
    current: 'pt',
    translations: {
        pt: {
            welcome: '🌟 Bem-vindo ao Aprendizado Especial',
            subtitle: 'Sistema de Apoio Educacional para Crianças com TEA',
            childArea: 'Área da Criança',
            parentArea: 'Área dos Pais/Responsáveis',
            login: 'Entrar',
            register: 'Criar Conta',
            username: 'Usuário',
            password: 'Senha',
            email: 'Email',
            confirmPassword: 'Confirmar Senha',
            back: 'Voltar',
            exit: 'Sair',
            settings: 'Configurações',
            achievements: 'Conquistas',
            myAchievements: 'Minhas Conquistas',
            starsEarned: 'estrelas conquistadas!',
            congratulations: 'Parabéns!',
            continue: 'Continuar',
            level: 'Nível',
            colors: 'Cores', shapes: 'Formas', numbers: 'Números',
            sequences: 'Sequências', matching: 'Pareamento', math: 'Matemática',
            emotions: 'Emoções', letters: 'Letras', clock: 'Relógio',
            money: 'Dinheiro', categories: 'Categorias', patterns: 'Padrões',
            practice: 'Treino Livre',
            dashboard: 'Dashboard', detailed: 'Análise Detalhada',
            recommendations: 'Recomendações', configTab: 'Configurações',
        },
        en: {
            welcome: '🌟 Welcome to Special Learning',
            subtitle: 'Educational Support System for Children with ASD',
            childArea: "Child's Area",
            parentArea: 'Parents/Guardians Area',
            login: 'Login',
            register: 'Create Account',
            username: 'Username',
            password: 'Password',
            email: 'Email',
            confirmPassword: 'Confirm Password',
            back: 'Back',
            exit: 'Exit',
            settings: 'Settings',
            achievements: 'Achievements',
            myAchievements: 'My Achievements',
            starsEarned: 'stars earned!',
            congratulations: 'Congratulations!',
            continue: 'Continue',
            level: 'Level',
            colors: 'Colors', shapes: 'Shapes', numbers: 'Numbers',
            sequences: 'Sequences', matching: 'Matching', math: 'Math',
            emotions: 'Emotions', letters: 'Letters', clock: 'Clock',
            money: 'Money', categories: 'Categories', patterns: 'Patterns',
            practice: 'Free Practice',
            dashboard: 'Dashboard', detailed: 'Detailed Analysis',
            recommendations: 'Recommendations', configTab: 'Settings',
        },
        es: {
            welcome: '🌟 Bienvenido al Aprendizaje Especial',
            subtitle: 'Sistema de Apoyo Educativo para Niños con TEA',
            childArea: 'Área del Niño',
            parentArea: 'Área de Padres/Tutores',
            login: 'Entrar',
            register: 'Crear Cuenta',
            username: 'Usuario',
            password: 'Contraseña',
            email: 'Correo electrónico',
            confirmPassword: 'Confirmar Contraseña',
            back: 'Volver',
            exit: 'Salir',
            settings: 'Configuraciones',
            achievements: 'Logros',
            myAchievements: 'Mis Logros',
            starsEarned: 'estrellas ganadas!',
            congratulations: '¡Felicidades!',
            continue: 'Continuar',
            level: 'Nivel',
            colors: 'Colores', shapes: 'Formas', numbers: 'Números',
            sequences: 'Secuencias', matching: 'Emparejamiento', math: 'Matemáticas',
            emotions: 'Emociones', letters: 'Letras', clock: 'Reloj',
            money: 'Dinero', categories: 'Categorías', patterns: 'Patrones',
            practice: 'Práctica Libre',
            dashboard: 'Panel', detailed: 'Análisis Detallado',
            recommendations: 'Recomendaciones', configTab: 'Configuraciones',
        },
    },

    init() {
        this.current = localStorage.getItem('tea_lang') || 'pt';
    },

    t(key) {
        return this.translations[this.current]?.[key] || key;
    },

    setLanguage(lang) {
        if (this.translations[lang]) {
            this.current = lang;
            localStorage.setItem('tea_lang', lang);
            this.updateUI();
            AppController.showToast(`Idioma: ${lang.toUpperCase()}`, 'success');
        }
    },

    updateUI() {
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });
    },
};
