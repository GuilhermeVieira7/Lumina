# ☁️ Sistema TEA - Hospedagem 24/7 na Microsoft Azure

Para manter o seu sistema educacional no ar ininterruptamente, suportando conexões do terapeuta, da escola e de casa paralelamente, utilizar uma **Máquina Virtual (VM) da Azure** junto com a infraestrutura em **Docker** que criamos, é sem dúvida a solução de grau de produção mais indicada e segura.

---

## 1. Topologia da Arquitetura

O sistema passará a se comportar com dois nós centrais rodando dentro da sua VM:
1. **Container App (FastAPI + PWA):** Servirá a rede externa. Responsável pelas requisições lógicas, motor IA e hospedagem estática.
2. **Container DB (PostgreSQL 15):** Totalmente isolado. Servirá apenas o Node local, protegendo os dados sensíveis dos seus pacientes atrás da firewall do Docker.

---

## 2. Passo a Passo Inicial

### A. Criação da VM na Azure
1. Acesse o portal Azure.
2. Crie uma Máquina Virtual do tipo `Standard_B1s` (Tamanho gratuito ou barato, excelente para tráfego leve) ou `Standard_B2s` (para tráfego pesado).
3. **Sistema Operacional:** Ubuntu Server 22.04 LTS (o padrão mais seguro e utilizado pela indústria).
4. **Portas de Rede (Regras de Entrada):**
   - Habilitar `SSH (22)` para você se conectar.
   - Habilitar `HTTP (80)` e `HTTPS (443)` para acesso das famílias ao sistema.

### B. Configurando o Ambiente Ubuntu
Uma vez via SSH no terminal do seu servidor Azure, você só precisa do Docker:

```bash
# Evite ferramentas complexas, vamos instalar o Docker puro:
sudo apt-get update
sudo apt-get install docker.io docker-compose -y

# Adicione seu usuario ao grupo do Docker para não precisar de 'sudo' sempre
sudo usermod -aG docker $USER
```

---

## 3. O Segredo do "Run 24/7" (Zero Downtime)

Muitas pessoas cometem o erro de rodar o Python puro usando `python main.py` na nuvem. Se ocorrer qualquer falha ou se o servidor reiniciar (atualizações do Linux), o sistema cai e não volta.

**Ao utilizar o nosso arquivo `docker-compose.yml`, solucionamos isso de duas frentes:**

1. **A flag mística `restart: always`:** 
   Ambos os servidores (Postgres e FastAPI) possuem essa tag no nosso docker-compose. Isso significa que o Docker atuará como um "Guardião 24/7". Se a aplicação der um Crash ou o servidor da Azure reiniciar no meio da madrugada, o Docker subirá sua API automaticamente em 2 milissegundos sem você fazer nada.

2. **Geração via Docker Compose:**
   Copie a pasta de seu projeto (`PROJETO TCC`) integralmente para o servidor Azure e apenas rode esse comando:
   ```bash
   # Dentro da pasta principal do projeto
   docker-compose up -d --build
   ```
   A flag `-d` (`detached`) faz a aplicação rodar eternamente no infinito do ambiente e devolve o teclado para você na hora.

---

## 4. Gerenciando em Produção como um Engenheiro Sênior de Nuvem

*   Como ver quem está online ou consultar logs?
    `docker-compose logs -f app` (Ver a tela em tempo real)

*   Se houver travamento absurdo ou vazamento de memória do SO?
    `docker-compose restart` (0% de dor de cabeça, sem mexer em código)

*   Onde meus dados estão guardados? Se eu apagar o Container, o Postgres deleta as respostas da criança?!
    *Não*. O banco de dados Postgres está salvo na cláusula `volumes: pgdata:/...` do nosso YAML. Mesmo apagando o banco via Docker, o Ubuntu reterá o HD virtual, impossibilitando perda de progresso clínico pela base do SQLite.

## Bônus: Transformar em um domínio
Hoje ele funcionará no **IP Público** (Ex: `http://170.198.89.12`).
Para mudar para algo como `app-tea.com.br` mantendo seguro, será necessário rodar um serviço extra no Docker mais para frente chamado `Caddy` ou `Nginx` (ambos grátis e configuráveis no Compose) para injetar certificados SSL/HTTPS no sistema final.
