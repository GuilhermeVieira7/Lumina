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

**Credenciais de teste:** usuário `admin` / senha `admin1234`

---

## 🧠 O Que Avaliar

1. **Interface adaptativa** — Layout construído sob as diretrizes TEACCH/ABA para crianças com TEA
2. **IA Adaptativa** — `backend/ai_engine.py` — dificuldade auto-regulada via `RandomForestClassifier` com base em tempo de resposta, tentativas e falhas
3. **Gerador de Laudos em PDF** — Painel admin → aba "Exportar" → download de relatório clínico gerado dinamicamente
4. **API REST documentada** — http://127.0.0.1:8000/api/docs (Swagger interativo)

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
│   ├── ai_engine.py         ← IA Adaptativa (RandomForest)
│   └── routers/             ← Endpoints da API
│
├── frontend/                ← Interface Web (PWA)
│   ├── index.html           ← Aplicação principal
│   ├── css/style.css        ← Estilos
│   └── js/                  ← Lógica do cliente
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
| IA Adaptativa | scikit-learn (RandomForest) |
| Relatórios | FPDF2 (PDF clínico) |
| Deploy | Docker + Docker Compose |
| Nuvem | Microsoft Azure |

---

## ☁️ Deploy em Produção (Azure)

Consulte `docs/azure_architecture.md` para o guia completo de deploy com Docker e PostgreSQL na Azure.
