// ==========================================
// THEME CONTROLLER - Gerenciador de Temas
// ==========================================

const ThemeController = {
    themes: {
        light:        { name: 'Claro',          start: '#667eea', end: '#764ba2', card: '#ffffff', text: '#1a202c' },
        dark:         { name: 'Escuro',         start: '#1a202c', end: '#2d3748', card: '#2d3748', text: '#f7fafc' },
        blue:         { name: 'Azul Oceano',    start: '#0ea5e9', end: '#06b6d4', card: '#f0f9ff', text: '#0c4a6e' },
        green:        { name: 'Verde Floresta', start: '#10b981', end: '#059669', card: '#f0fdf4', text: '#064e3b' },
        purple:       { name: 'Roxo Místico',   start: '#a855f7', end: '#9333ea', card: '#faf5ff', text: '#581c87' },
        highContrast: { name: 'Alto Contraste', start: '#000000', end: '#1a1a1a', card: '#ffffff', text: '#000000' },
    },

    current: 'light',

    init() {
        this.current = localStorage.getItem('tea_theme') || 'light';
        this.apply(this.current);
    },

    apply(themeName) {
        const theme = this.themes[themeName];
        if (!theme) return;

        const root = document.documentElement;
        root.style.setProperty('--bg-gradient-start', theme.start);
        root.style.setProperty('--bg-gradient-end', theme.end);
        root.style.setProperty('--bg-card', theme.card);
        root.style.setProperty('--text-primary', theme.text);

        // Update dark mode flag
        if (themeName === 'dark' || themeName === 'highContrast') {
            root.setAttribute('data-theme', 'dark');
        } else {
            root.setAttribute('data-theme', 'light');
        }

        this.current = themeName;
        localStorage.setItem('tea_theme', themeName);
    },
};
