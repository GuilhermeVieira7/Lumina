// ==========================================
// THEME CONTROLLER - Cores e tamanho do texto
// ==========================================

const ThemeController = {
    themes: ['light', 'green', 'lilac', 'dark', 'contrast'],
    current: 'light',

    init() {
        this.apply(localStorage.getItem('tea_theme') || 'light');
        this.setLargeFont(localStorage.getItem('tea_font_large') === 'true');
    },

    apply(name) {
        if (!this.themes.includes(name)) name = 'light';
        document.documentElement.setAttribute('data-theme', name);
        this.current = name;
        localStorage.setItem('tea_theme', name);
        document.querySelectorAll('[data-theme-choice]').forEach(b =>
            b.setAttribute('aria-pressed', b.dataset.themeChoice === name));
    },

    setLargeFont(on) {
        document.documentElement.classList.toggle('font-large', on);
        localStorage.setItem('tea_font_large', on);
    },
};
