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
3. **Recomendação explicável** — `backend/ai_engine.py`: regras de domínio e de dificuldade (ABA) e pontuação por interesses, metas, desempenho e variedade. Cada sugestão mostra os motivos e só vale depois que um adulto aceita, ajusta ou descarta.
4. **Painel dos Adultos protegido por senha** — progresso por área e período, sessões com nível de ajuda, diário de observações, metas, plano de atividades, rotina, perfil e ajustes sensoriais.
5. **Acompanhamento compartilhado** — o responsável convida um profissional, que aceita o convite; o acesso pode ser revogado a qualquer momento.
6. **LGPD** — consentimento no cadastro, perfil sem diagnóstico, exclusão da criança ou da conta com todos os dados.
7. **Relatório em PDF** — Painel → Progresso → "Relatório PDF".
8. **API REST documentada** — http://127.0.0.1:8000/api/docs (Swagger interativo).

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
│   └── js/                  ← Lógica do cliente (Chart.js incluído em js/vendor)
│
└── docs/                    ← Documentação técnica
    ├── schema.sql           ← Schema PostgreSQL (deploy)
    ├── azure_architecture.md ← Guia de deploy na Azure
    └── export_schema.py     ← Script para gerar schema.sql
```

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
