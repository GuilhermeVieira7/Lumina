# Publicar o Lumina na internet (Render)

O Lumina fica no ar com endereço próprio e **HTTPS** (necessário para o PWA
instalar no celular), de graça, usando o [Render](https://render.com).
O arquivo `render.yaml` na raiz do projeto já descreve tudo: o app (pelo
`Dockerfile`) e um banco PostgreSQL privado.

## Passo a passo (uns 10 minutos)

1. Crie uma conta em <https://render.com> clicando em **Sign in with GitHub**
   (não pede cartão de crédito).
2. No painel do Render, clique em **New +** > **Blueprint**.
3. Autorize o Render a ver o repositório **Lumina** e selecione-o.
4. O Render lê o `render.yaml` e mostra o que vai criar: `lumina` (web) e
   `lumina-db` (banco). Clique em **Deploy Blueprint** (ou **Apply**).
5. Espere o primeiro build terminar (5 a 10 minutos). Quando aparecer
   **Live**, abra o serviço `lumina`: o endereço fica no topo, algo como
   `https://lumina-xxxx.onrender.com`.
6. Entre com a conta de demonstração e confira: `admin` / `admin1234`
   (responsável) ou `terapeuta` / `terapeuta1234` (profissional).

Depois disso, cada `git push` na branch `main` atualiza o site sozinho.

## O que já está protegido

- **HTTPS** automático, com certificado do próprio Render.
- **Banco privado**: só o app conversa com ele (`ipAllowList: []`).
  O pgAdmin **não** vai para a internet; ele continua só no Docker local.
- **SECRET_KEY** gerada pelo Render, longa e aleatória (ninguém precisa digitar).
- Senhas com **Argon2id** e bloqueio após 8 senhas erradas em 5 minutos,
  como no Docker local (ver `docs/SEGURANCA.md`).

## Limites do plano gratuito (importante para a banca)

- **O site "dorme"** depois de 15 minutos sem acesso. O primeiro acesso
  depois disso demora cerca de 1 minuto para acordar. **Abra o site uns
  2 minutos antes de apresentar.**
- **O banco gratuito do Render expira 30 dias após ser criado.** Se a banca
  for depois disso, há duas saídas:
  - mudar o banco `lumina-db` para o plano pago mais barato (cerca de US$ 6/mês)
    em *lumina-db > Settings > Instance type*; ou
  - criar um banco gratuito no [Neon](https://neon.tech), copiar a
    *connection string* dele e colar em *lumina > Environment > DATABASE_URL*.
- As contas de demonstração aparecem na tela de login, então qualquer pessoa
  com o link pode entrar nelas. **Não cadastre dados reais de crianças** no
  site público; use só dados de exemplo.

## Se algo der errado

- Em *lumina > Logs* aparece o que o servidor imprimiu. A linha
  `[*] Demo: admin / admin1234` indica que o app subiu e criou as contas.
- Build falhou: clique em **Manual Deploy > Deploy latest commit** para tentar
  de novo.
