// ==========================================
// TESTE DE PONTA A PONTA (E2E) - o sistema inteiro pelo navegador, como um usuário
// ==========================================
// Cadastro -> criança -> área da criança (emoção, atividade, pedido) -> sair com senha
// -> Painel dos Adultos (todas as abas, ajuda, diário, meta, rotina, PDF, Pergunte à IA)
// -> atividade sem internet (fica guardada e é enviada quando a conexão volta)
// -> convite ao profissional -> profissional aceita e vê a criança.
//
// Falha se aparecer erro no console, resposta 5xx da API ou aviso de erro na tela.
//
// Com o Docker do Lumina rodando, na pasta do projeto (o navegador de teste entra na rede do
// container do app para abrir http://localhost, onde o service worker funciona como no uso real):
//   docker run --rm --network container:tea_application -v "%cd%/tests/e2e:/e2e" -w /e2e ^
//     mcr.microsoft.com/playwright:v1.49.0-jammy sh -c "npm i -s playwright@1.49.0 && node fluxo_completo.js"
// Outro endereço: defina BASE_URL (ex.: -e BASE_URL=https://lumina-xxxx.onrender.com, sem o --network).

const { chromium } = require('playwright');

const BASE = process.env.BASE_URL || 'http://localhost';
const SHOTS = process.env.SHOTS_DIR || '.';
const ASK_AI = process.env.ASK_AI !== '0';   // ASK_AI=0 pula a pergunta ao Gemini
const user = `e2e${Date.now().toString(36)}`;
const password = 'senha-e2e-123';
const problems = [];
let step = '';

function log(msg) { console.log(`  ✔ ${msg}`); }

async function run(page, name, fn) {
    step = name;
    await fn();
    await expectNoErrorToast(page);
    log(name);
}

async function expectNoErrorToast(page) {
    const toast = page.locator('#toast.error:not(.hidden)');
    if (await toast.count() && await toast.isVisible()) {
        problems.push(`[${step}] aviso de erro na tela: ${await toast.textContent()}`);
    }
}

function watch(page, who) {
    page.on('pageerror', e => problems.push(`[${who}/${step}] erro de JavaScript: ${e.message}`));
    page.on('console', m => {
        if (m.type() === 'error' && !/Failed to load resource|net::ERR_INTERNET_DISCONNECTED/.test(m.text())) {
            problems.push(`[${who}/${step}] console: ${m.text()}`);
        }
    });
    page.on('response', r => {
        if (r.url().includes('/api/') && r.status() >= 500) problems.push(`[${who}/${step}] ${r.status()} em ${r.url()}`);
    });
}

async function visible(page, selector, timeout = 1500) {
    try { await page.locator(selector).first().waitFor({ state: 'visible', timeout }); return true; } catch { return false; }
}

async function login(page, username, pass) {
    await page.goto(BASE);
    await page.fill('#login-username', username);
    await page.fill('#login-password', pass);
    await page.click('#login-form [type=submit]');
    await page.waitForSelector('#select-screen.active', { timeout: 15000 });
}

async function adultPassword(page) {
    await page.waitForSelector('#password-modal:not(.hidden)', { timeout: 5000 });
    await page.fill('#password-input', password);
    await page.click('#password-form [type=submit]');
}

/** Faz uma atividade inteira respondendo certo (lê a resposta do próprio estado da página). */
async function doActivity(page) {
    await page.locator('#child-tiles [data-activity]').first().click();
    await page.waitForSelector('#reward-screen.active, #activity-screen.active', { timeout: 8000 });
    if (await page.locator('#reward-screen.active').count()) await page.click('#reward-skip');
    await page.waitForSelector('#activity-screen.active', { timeout: 8000 });
    for (let i = 0; i < 40; i++) {
        if (await visible(page, '#finish-screen.active', 300)) break;
        const correct = await page.evaluate(() => {
            const q = Activity.questions && Activity.questions[Activity.index];
            return q && !Activity.locked ? q.correct : null;
        });
        if (correct !== null) {
            const btn = page.locator(`.option-btn[data-value="${correct.replace(/"/g, '\\"')}"]:not([disabled])`).first();
            if (await btn.count()) await btn.click();
        }
        await page.waitForTimeout(700);
    }
    await page.waitForSelector('#finish-screen.active', { timeout: 10000 });
    await page.waitForTimeout(800);
}

async function openSub(page, group, tab) {
    await page.click(`.tab[data-group="${group}"]`);
    const sub = page.locator(`.subtabs [data-tab="${tab}"]`);
    if (await sub.isVisible()) await sub.click();
    await page.waitForSelector(`#tab-${tab}.active`);
    await page.waitForTimeout(900);
}

(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, acceptDownloads: true });
    const page = await context.newPage();
    watch(page, 'responsável');
    console.log(`Lumina E2E em ${BASE} (usuário ${user})`);

    try {
        await run(page, 'cadastro com consentimento', async () => {
            await page.goto(BASE);
            await page.click('[data-go="register-screen"]');
            await page.fill('#register-username', user);
            await page.fill('#register-password', password);
            await page.fill('#register-confirm', password);
            await page.check('#register-consent');
            await page.click('#register-form [type=submit]');
            await page.waitForSelector('#new-profile-modal:not(.hidden)', { timeout: 15000 });
        });

        await run(page, 'cadastro da criança', async () => {
            const form = page.locator('#new-profile-form');
            await form.locator('input[type=text], input:not([type])').first().fill('Teo E2E');
            const interests = form.locator('textarea, input[name*="interest" i], #pf-interests');
            if (await interests.count()) await interests.first().fill('números, animais');
            await form.locator('[type=submit]').click();
            await page.waitForSelector('#new-profile-modal.hidden, #new-profile-modal[hidden]', { state: 'attached', timeout: 10000 });
        });

        await run(page, 'área da criança e "Como estou?"', async () => {
            if (!(await visible(page, '#select-screen.active', 3000))) await page.goto(BASE);
            await page.click('#enter-child');
            if (await visible(page, '#mood-screen.active', 3000)) {
                await page.locator('#mood-grid [data-mood="feliz"]').click();
                await page.locator('#mood-go').click();
            }
            await page.waitForSelector('#child-home.active', { timeout: 8000 });
        });

        await run(page, 'atividade completa', () => doActivity(page));

        await run(page, 'prancha de pedidos', async () => {
            await page.click('#finish-continue');
            await page.waitForSelector('#child-home.active', { timeout: 8000 });
            await page.click('#ask-btn');
            await page.locator('#ask-grid button').first().click();
            if (await visible(page, '#ask-ok', 3000)) await page.click('#ask-ok');
        });

        await run(page, 'atividade sem internet fica guardada', async () => {
            if (!(await visible(page, '#child-home.active', 2000))) await page.keyboard.press('Escape');
            await context.setOffline(true);
            await doActivity(page);
            const pending = await page.evaluate(() => API.pendingCount());
            if (pending !== 1) problems.push(`[${step}] esperava 1 sessão guardada, há ${pending}`);
            await context.setOffline(false);
            await page.evaluate(() => window.dispatchEvent(new Event('online')));
            await page.waitForFunction(() => API.pendingCount() === 0, null, { timeout: 15000 });
            await page.click('#finish-continue');
        });

        await run(page, 'sair da área da criança com senha', async () => {
            await page.waitForSelector('#child-home.active', { timeout: 8000 });
            await page.click('#child-exit');
            await adultPassword(page);
            await page.waitForSelector('#select-screen.active', { timeout: 8000 });
        });

        await run(page, 'Painel dos Adultos: aba Hoje', async () => {
            await page.click('#enter-adult');
            await adultPassword(page);
            await page.waitForSelector('#panel-screen.active', { timeout: 8000 });
            await page.waitForSelector('#today-box .card', { timeout: 10000 });
        });

        await run(page, 'Resumo e gráficos', async () => {
            await openSub(page, 'progress', 'dashboard');
            await page.waitForSelector('#summary .headline');
            const sessions = await page.locator('#summary .big-num b').first().textContent();
            if (Number(sessions) < 2) problems.push(`[${step}] esperava 2 atividades no resumo, veio ${sessions}`);
        });

        await run(page, 'Sugestões', () => openSub(page, 'progress', 'recs'));

        await run(page, 'registrar ajuda numa sessão', async () => {
            await openSub(page, 'diary', 'sessions');
            await page.locator('#sessions-list details.session-item summary').first().click();
            const select = page.locator('#sessions-list select[data-help]').first();
            await select.selectOption('none');
            await page.waitForTimeout(800);
        });

        await run(page, 'diário: nova observação', async () => {
            await openSub(page, 'diary', 'diary');
            await page.fill('#diary-text', 'Observação do teste E2E: ficou calmo com música baixa.');
            await page.click('#diary-form [type=submit]');
            await page.waitForSelector('#diary-list .row', { timeout: 5000 });
        });

        await run(page, 'Plano: atividades', () => openSub(page, 'plan', 'plan'));

        await run(page, 'rotina: nova etapa', async () => {
            await openSub(page, 'plan', 'routine');
            await page.fill('#routine-label', 'Escovar os dentes');
            await page.click('#routine-form [type=submit]');
            await page.waitForSelector('#routine-list .row', { timeout: 5000 });
        });

        await run(page, 'meta com previsão', async () => {
            await openSub(page, 'plan', 'goals');
            await page.selectOption('#goal-type', 'sessions');
            await page.fill('#goal-target', '10');
            await page.click('#goal-form [type=submit]');
            await page.waitForSelector('#goals-list .row .meta', { timeout: 5000 });
        });

        await run(page, 'Ajustes e perfil', async () => {
            await openSub(page, 'config', 'profile');
            await openSub(page, 'config', 'settings');
        });

        await run(page, 'relatório PDF', async () => {
            await openSub(page, 'progress', 'dashboard');
            const [download] = await Promise.all([page.waitForEvent('download', { timeout: 20000 }), page.click('#export-pdf')]);
            const file = await download.path();
            if (!file) problems.push(`[${step}] PDF não baixou`);
        });

        if (ASK_AI) {
            await run(page, 'Pergunte à IA', async () => {
                await openSub(page, 'progress', 'today');
                await page.fill('#ai-ask-input', 'Que atividade fazer hoje e como conduzir?');
                await page.click('#ai-ask-send');
                await page.waitForSelector('.ai-msg.bot:not(.thinking)', { timeout: 90000 });
                const source = await page.locator('.ai-msg.bot .meta').last().textContent();
                log(`resposta veio de: ${source.trim()}`);
            });
        }

        await run(page, 'convidar o profissional demo', async () => {
            await openSub(page, 'config', 'profile');
            await page.fill('#access-who', 'terapeuta');
            await page.click('#access-form [type=submit]');
            await page.waitForSelector('#access-list .row', { timeout: 5000 });
        });
        await page.screenshot({ path: `${SHOTS}/e2e-responsavel.png`, fullPage: true });

        // ---- Profissional ----
        const pro = await (await browser.newContext({ viewport: { width: 390, height: 844 } })).newPage();
        watch(pro, 'profissional');
        await run(pro, 'profissional aceita o convite e vê a criança (celular)', async () => {
            await login(pro, 'terapeuta', 'terapeuta1234');
            await pro.click('#enter-adult');
            await pro.waitForSelector('#password-modal:not(.hidden)');
            await pro.fill('#password-input', 'terapeuta1234');
            await pro.click('#password-form [type=submit]');
            await pro.waitForSelector('#panel-screen.active', { timeout: 8000 });
            await openSub(pro, 'config', 'settings');
            const accept = pro.locator('#invites-list button').filter({ hasText: /aceitar/i }).last();
            await accept.waitFor({ timeout: 5000 });
            await accept.click();
            await pro.waitForTimeout(1500);
            await pro.locator('#panel-profile [data-kid]').filter({ hasText: 'Teo E2E' }).click();
            await openSub(pro, 'progress', 'today');
            await pro.waitForSelector('#today-box .card', { timeout: 10000 });
        });
        await pro.screenshot({ path: `${SHOTS}/e2e-profissional.png`, fullPage: true });

        await run(page, 'excluir a conta de teste (LGPD)', async () => {
            page.on('dialog', d => d.accept(password));
            await openSub(page, 'config', 'settings');
            await page.click('#delete-account-btn');
            if (await visible(page, '#password-modal:not(.hidden)', 2000)) await adultPassword(page);
            await page.waitForSelector('#login-screen.active', { timeout: 10000 });
        });
    } catch (err) {
        problems.push(`[${step}] parou: ${err.message.split('\n')[0]}`);
        await page.screenshot({ path: `${SHOTS}/e2e-falha.png`, fullPage: true }).catch(() => {});
    }

    await browser.close();
    if (problems.length) {
        console.log(`\n✖ ${problems.length} problema(s):`);
        problems.forEach(p => console.log('  - ' + p));
        process.exit(1);
    }
    console.log('\n✔ Fluxo completo sem erros.');
})();
