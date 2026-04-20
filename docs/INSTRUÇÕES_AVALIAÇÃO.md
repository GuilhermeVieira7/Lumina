# 🎓 Lumina TEA Edu - Guia de Execução Local (Avaliação)

Olá! Este é o guia rápido para colocar o projeto **Lumina TEA Edu** (um sistema de software educacional, voltado ao neurodesenvolvimento de crianças autistas baseando-se em método TEACCH/ABA) para rodar localmente na sua máquina para fins de experimentação ou avaliação acadêmica.

## 📌 1. Requisitos Prévios

1. **Linguagem Python 3.9** ou superior já instalada na máquina.
2. Projeto baixado/descompactado com acesso ao terminal da pasta principal (`/PROJETO TCC`).

*Nota Arquitetural: O sistema não necessita de nenhuma interface web à parte para ligar (ex: React puro ou Node.js). O FastAPI (Python) atua nativamente servindo a Single Page Application desenvolvida em Vanilla JS de forma performática.*

---

## 🚀 2. Ligando a Aplicação (Passo a Passo Padrão)

### Passo 2.1: Instalar as Dependências

Na raiz do projeto (onde está localizado este arquivo), abra seu Terminal ou Prompt de Comando e instale o arquivo de dependências:

**Usando Windows:**
```powershell
pip install -r backend/requirements.txt
```

**Usando MacOS/Linux:**
```bash
pip3 install -r backend/requirements.txt
```

### Passo 2.2: Iniciar o Servidor (Uvicorn)

Uma vez que o FastAPI e as bibliotecas foram baixadas, basta dar boot na engine principal.

**Usando Windows:**
```powershell
cd backend
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

**Usando MacOS/Linux:**
```bash
cd backend
python3 -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

*Pronto! O console indicará que a aplicação foi iniciada ("Uvicorn running on http://127.0.0.1:8000").*

---

## 🖥 3. Acessando a Interface

Deixe o terminal rodando em segundo plano e acesse nosecteu navegador favorito (de preferência o Chrome):

👉 **URL de Acesso do Sistema:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
👉 **URL da Documentação REST API Dinâmica:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

**Credenciais de Acesso (Conta de Teste Automatizada):**
- **Usuário:** admin
- **Senha:** admin1234

---

## 🧠 O Que Avaliar? (Dicas de Arquitetura)

O sistema foi preparado sob o viés de produto real contendo as seguintes capacidades técnicas:

1. **UX em Neurociência:** Layout interativo construído sob as diretrizes TEACCH. Todas as cores, símbolos e disposições foram limitadas para prevenir sobrecargas.
2. **Motor Adaptativo Preditivo (Machine Learning):** Se acessarem o código fonte (`backend/ai_engine.py`), notarão que a dificuldade se auto-regula treinada sob um modelo `RandomForestClassifier` lendo taxa de tentativas, falhas sucessivas e tempo de reposta em milissegundos para gerar análises impulsivas ou reflexivas dos estudantes.
3. **Gerador de Laudos (FPDF2 Clínico):** Para o professor verificar na prática, abra o painel administrativo através do login e na Aba "Exportar", realize o download dinâmico em PDF compilado no Back-End.
4. **Deploy Ready:** Na raiz, já constam toda estruturação de Docker, Arquivo Docker-Compose para Deploy em Azure Cloud e conectores PostgreSQL prontos (o sistema migra automaticamente do SQLite de testes para PostgreSQL se rodado no Docker).

Qualquer dúvida ou falha ao startar na máquina, limpe o cache do pip (`pip cache purge`) ou crie um virtual env (`python -m venv venv`). Bom uso e avaliação!
