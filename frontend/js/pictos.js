// ==========================================
// PICTOS - Pictogramas ARASAAC no lugar dos emoji
// ==========================================
// O índice (img/pictos/index.json) é gerado por scripts/baixar_pictogramas.py.
// Figura que ainda não foi baixada continua aparecendo como emoji.

const Pictos = {
    index: {},
    attribution: '',

    async load() {
        try {
            const res = await fetch('/img/pictos/index.json', { cache: 'no-cache' });
            if (!res.ok) return;
            const data = await res.json();
            this.attribution = data.attribution || '';
            this.index = Object.fromEntries(
                Object.entries(data.pictos || {}).map(([emoji, info]) => [this._key(emoji), info]));
        } catch {
            this.index = {};
        }
    },

    get count() { return Object.keys(this.index).length; },

    _key(emoji) { return String(emoji ?? '').replace(/️/g, '').trim(); },

    has(emoji) { return !!this.index[this._key(emoji)]; },

    /** Pictograma (ou o próprio emoji). alt=true descreve a figura para leitores de tela. */
    html(emoji, { alt = false, cls = '' } = {}) {
        const info = this.index[this._key(emoji)];
        if (!info) return alt
            ? `<span class="emo ${cls}" role="img" aria-label="${UI.esc(alt === true ? emoji : alt)}">${UI.esc(emoji)}</span>`
            : UI.esc(emoji);
        const text = alt === true ? info.term : alt || '';
        return `<img class="picto ${cls}" src="/img/pictos/${encodeURIComponent(info.file)}" alt="${UI.esc(text)}" draggable="false">`;
    },
};
