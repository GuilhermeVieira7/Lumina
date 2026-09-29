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

Deixe o terminal rodando em segundo plano e acesse seu navegador favorito (de preferência o Chrome):

👉 **URL de Acesso do Sistema:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
👉 **URL da Documentação REST API Dinâmica:** [http://127.0.0.1:8000/api/docs](http://127.0.0.1:8000/api/docs)

**Contas de demonstração (criadas automaticamente):**
- **Responsável:** `admin` / `admin1234` (dono do perfil "Aluno Demo")
- **Profissional:** `terapeuta` / `terapeuta1234` (já autorizado a acompanhar o "Aluno Demo")

---

## 🧠 O Que Avaliar? (roteiro sugerido)

1. **Entrar como responsável** (`admin`), escolher o "Aluno Demo" e abrir o **Painel dos Adultos** (pede a senha da conta).
2. Em **Rotina**, clicar em "Usar rotina de exemplo" (algumas etapas já vêm com timer visual). Em **Atividades**, escolher o que aparece para a criança, o nível, o número de etapas e, se quiser, um timer; destacar uma atividade com ⭐. Em **Ajustes**, ver o quadro de fichas (prêmios) e a prancha de pedidos.
3. Clicar em **Área da Criança**: primeiro a pergunta "Como você está se sentindo?" (a criança toca num rosto; nas emoções difíceis aparece "Pedir ajuda"), depois cartões grandes com pictogramas, quadro "Agora / Depois" da rotina com botão do timer, escolha do prêmio antes da atividade (quadro de fichas: cada etapa vale uma ⭐), atividade em modo de foco com trilha de etapas (TEACCH), dica visual depois de dois erros (ensino sem erro, ABA) e tela "Terminou!" com o prêmio. O botão **Pedir** abre a prancha de pedidos (pausa, ajuda, água, sim, não...), que fala o pedido em voz alta. Para sair da área da criança é preciso a senha de um adulto.
4. Voltar ao painel: **Progresso** (por área de habilidade e período), **Sessões** (registrar o nível de ajuda; ver o prêmio escolhido e se o tempo acabou), **Recomendações** (aceitar, ajustar ou descartar, cada uma com os motivos), **Diário** (com as emoções e os pedidos da criança), o gráfico "Como a criança se sentiu" no Progresso, **Metas** e **Relatório PDF**.
5. **Entrar como profissional** (`terapeuta`): ele vê o "Aluno Demo" compartilhado, pode registrar observações e metas, mas não edita o perfil. Como responsável, em **Perfil e acesso**, revogar o acesso e confirmar que o profissional deixa de ver a criança.
6. **Recomendação explicável:** `backend/ai_engine.py` usa regras explícitas (critério de domínio configurável e dificuldade recorrente) e uma pontuação por interesses, metas, desempenho e variedade. Nada muda para a criança sem a decisão de um adulto.
7. **Testes automatizados:** `pip install -r requirements-dev.txt` e depois `pytest` na raiz do projeto.
8. **Deploy:** Dockerfile e docker-compose para PostgreSQL. Bancos SQLite criados por versões anteriores recebem as colunas novas automaticamente ao iniciar.

Qualquer dúvida ou falha ao iniciar, crie um ambiente virtual (`python -m venv venv`) e reinstale as dependências. Bom uso e avaliação!
