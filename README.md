# 🌟 Lumina TEA Edu

Sistema web progressivo (PWA) de apoio educacional para crianças com Transtorno do Espectro Autista (TEA), desenvolvido com FastAPI, HTML/CSS/JS puro e IA adaptativa.

---

## 🚀 Como Iniciar (Uso Local)

### Passo 1 — Instalar dependências (só na primeira vez)

```bash
pip install -r backend/requirements.txt
```

### Passo 2 — Iniciar o servidor

```bash
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

Aguarde a mensagem: `Uvicorn running on http://127.0.0.1:8000`

### Passo 3 — Acessar no navegador
- **Sistema:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/api/docs

**Contas de demonstração** (criadas na primeira execução):

| Papel | Usuário | Senha |
|---|---|---|
| Responsável (dono do perfil "Aluno Demo") | `admin` | `admin1234` |
| Profissional com acesso autorizado ao "Aluno Demo" | `terapeuta` | `terapeuta1234` |

---

## 🧠 O Que Avaliar

1. **Área da criança visual (TEACCH)** — cartões grandes com pictogramas coloridos por área de habilidade, quadro "Agora / Depois", uma instrução por tela, trilha de etapas com bandeira de chegada e tela "Terminou!".
2. **Agenda visual de rotina** — o adulto monta a rotina com pictogramas; a criança marca cada etapa como feita.
3. **Timer visual** — disco colorido que diminui com o tempo (estilo Time Timer). Aparece nas etapas da rotina que têm duração, no botão "Timer" da criança e nas atividades em que o adulto define um tempo (Painel → Atividades).
4. **Quadro de fichas** — antes da atividade, a criança escolhe o prêmio; cada etapa vale uma ⭐ e a trilha termina no prêmio. O adulto escolhe os prêmios em Painel → Ajustes.
5. **Prancha de pedidos** — botão "Pedir" sempre visível na área da criança (pausa, ajuda, água, banheiro, sim, não...). O pedido é falado em voz alta e aparece no Diário e no relatório.
6. **Como estou me sentindo?** — ao entrar na sua área, a criança toca no rosto que mostra como está (feliz, calmo, triste, bravo, com medo, cansado). O Lumina fala a frase e, nas emoções difíceis, oferece "Pedir ajuda". Os adultos veem as emoções por dia no gráfico do Progresso, no Diário e no relatório PDF. Pode ser desligado em Painel → Ajustes.
7. **Recomendação explicável** — `backend/ai_engine.py`: regras de domínio e de dificuldade (ABA) e pontuação por interesses, metas, desempenho e variedade. Cada sugestão mostra os motivos e só vale depois que um adulto aceita, ajusta ou descarta.
8. **Painel dos Adultos protegido por senha** — progresso por área e período, sessões com nível de ajuda, diário de observações, metas, plano de atividades, rotina, perfil e ajustes sensoriais.
9. **Acompanhamento compartilhado** — o responsável convida um profissional, que aceita o convite; o acesso pode ser revogado a qualquer momento.
10. **LGPD** — consentimento no cadastro, perfil sem diagnóstico, exclusão da criança ou da conta com todos os dados.
11. **Relatório em PDF** — Painel → Progresso → "Relatório PDF".
12. **API REST documentada** — http://127.0.0.1:8000/api/docs (Swagger interativo).

Testes automatizados: `pip install -r requirements-dev.txt` e `pytest` na raiz do projeto.

> Guia detalhado de avaliação acadêmica: [`docs/INSTRUÇÕES_AVALIAÇÃO.md`](docs/INSTRUÇÕES_AVALIAÇÃO.md)

---

## 📁 Estrutura do Projeto

```
PROJETO TCC/
├── INICIAR.bat              ← Inicialização rápida (duplo clique)
├── INSTRUÇÕES_AVALIAÇÃO.md  ← Guia para avaliação acadêmica
├── .env                     ← Configurações do sistema
├── Dockerfile               ← Deploy em container (produção)
├── docker-compose.yml       ← Orquestração Docker (Azure)
│
├── backend/                 ← API Python (FastAPI)
│   ├── main.py              ← Ponto de entrada
│   ├── models.py            ← Banco de dados (SQLAlchemy)
│   ├── schemas.py           ← Validações (Pydantic)
│   ├── permissions.py       ← Quem acessa cada perfil (responsável e profissionais)
│   ├── ai_engine.py         ← Recomendação por regras e pontuação
│   └── routers/             ← Endpoints da API
│
├── frontend/                ← Interface Web (PWA)
│   ├── index.html           ← Aplicação principal
│   ├── css/style.css        ← Estilos
│   ├── img/mascot/          ← Raposa Lumi (mascote)
│   ├── img/pictos/          ← Pictogramas ARASAAC (gerados pelo script abaixo)
│   └── js/                  ← Lógica do cliente (Chart.js incluído em js/vendor)
│
├── scripts/
│   └── baixar_pictogramas.py ← Baixa os pictogramas ARASAAC usados na interface
│
└── docs/                    ← Documentação técnica
    ├── schema.sql           ← Schema PostgreSQL (deploy)
    ├── azure_architecture.md ← Guia de deploy na Azure
    └── export_schema.py     ← Script para gerar schema.sql
```

---

## 🖼️ Pictogramas

As figuras da área da criança usam pictogramas do [ARASAAC](https://arasaac.org) quando eles estão em `frontend/img/pictos/`; o que ainda não foi baixado aparece como emoji. Para baixar ou atualizar:

```bash
python scripts/baixar_pictogramas.py
```

Pictogramas: Sergio Palao. Origem: ARASAAC (https://arasaac.org). Licença: CC BY-NC-SA. Propriedade: Governo de Aragão (Espanha).

---

## 🛠️ Stack Tecnológica

| Componente | Tecnologia |
|-----------|-----------|
| Backend | Python 3.9+ / FastAPI |
| Frontend | HTML5, CSS3, JavaScript (Vanilla) |
| Banco de dados (local) | SQLite (automático) |
| Banco de dados (produção) | PostgreSQL 15 |
| Recomendação | Regras e pontuação explicáveis (Python) |
| Gráficos | Chart.js (servido localmente, funciona offline) |
| Relatórios | FPDF2 (PDF de acompanhamento) |
| Deploy | Docker + Docker Compose |
| Nuvem | Microsoft Azure |

---

## ☁️ Deploy em Produção (Azure)

Consulte `docs/azure_architecture.md` para o guia completo de deploy com Docker e PostgreSQL na Azure.
